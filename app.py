from pathlib import Path
import sqlite3
import csv
import io
import os
from datetime import date, timedelta

from flask import Flask, jsonify, render_template, request, send_file


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("CASEFLOW_DATA_DIR", str(BASE_DIR / "data")))
DB_PATH = DATA_DIR / "caseflow.db"

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

CASE_STATUSES = [
    "一审进行中", "一审已结案", "二审进行中", "二审已结案",
    "执行进行中", "执行已终本", "执行完毕", "已结案",
]


def get_db():
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                client_type TEXT NOT NULL DEFAULT '个人',
                phone TEXT,
                email TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_number TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                case_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '一审进行中',
                client_id INTEGER,
                deadline TEXT,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                deadline TEXT,
                priority TEXT NOT NULL DEFAULT '普通',
                status TEXT NOT NULL DEFAULT '待办',
                case_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                event_date TEXT NOT NULL,
                title TEXT NOT NULL,
                event_type TEXT NOT NULL DEFAULT '其他',
                description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS client_followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                case_id INTEGER,
                followup_date TEXT NOT NULL,
                channel TEXT NOT NULL DEFAULT '电话',
                content TEXT NOT NULL,
                next_action TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                action TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # 兼容早期 MVP 数据：将简化版状态迁移到完整状态体系。
        db.execute("UPDATE cases SET status = '一审进行中' WHERE status = '进行中'")
        db.execute("UPDATE cases SET status = '已结案' WHERE status = '已完成'")
        existing_columns = {row[1] for row in db.execute("PRAGMA table_info(cases)").fetchall()}
        for column, definition in {
            "fee_status": "TEXT DEFAULT '未收费'",
            "invoice_status": "TEXT DEFAULT '未开票'",
            "claim_amount": "REAL",
            "fee_amount": "REAL",
            "risk_level": "TEXT NOT NULL DEFAULT '中'",
            "owner_name": "TEXT DEFAULT ''",
            "tags": "TEXT DEFAULT ''",
            "deadline_kind": "TEXT DEFAULT '关键节点'",
        }.items():
            if column not in existing_columns:
                db.execute(f"ALTER TABLE cases ADD COLUMN {column} {definition}")


def log_activity(entity_type, entity_id, action, detail):
    with get_db() as db:
        db.execute(
            "INSERT INTO activity_logs (entity_type, entity_id, action, detail) VALUES (?, ?, ?, ?)",
            (entity_type, entity_id, action, detail),
        )


def health_score(case):
    """基于风险、关键日期和未完成待办计算 0-100 的案件健康度。"""
    score = 100
    score -= {"低": 5, "中": 15, "高": 30}.get(case["risk_level"] or "中", 15)
    deadline = case["deadline"]
    if deadline:
        days = (date.fromisoformat(deadline) - date.today()).days
        if days < 0:
            score -= 35
        elif days <= 3:
            score -= 20
        elif days <= 7:
            score -= 10
    with get_db() as db:
        open_todos = db.execute(
            "SELECT COUNT(*) FROM todos WHERE case_id = ? AND status != '已完成'", (case["id"],)
        ).fetchone()[0]
    return max(0, min(100, score - min(open_todos * 5, 20)))


def health_label(score):
    return "健康" if score >= 80 else "需关注" if score >= 60 else "高风险"


@app.get("/")
def index():
    with get_db() as db:
        counts = {
            "cases": db.execute("SELECT COUNT(*) FROM cases").fetchone()[0],
            "clients": db.execute("SELECT COUNT(*) FROM clients").fetchone()[0],
            "todos": db.execute("SELECT COUNT(*) FROM todos WHERE status != '已完成'").fetchone()[0],
        }
    return render_template("index.html", counts=counts)


@app.get("/cases")
def cases_page():
    return render_template("cases.html")


@app.get("/cases/<int:case_id>")
def case_detail_page(case_id):
    return render_template("case_detail.html", case_id=case_id)


@app.get("/api/cases/<int:case_id>")
def get_case(case_id):
    with get_db() as db:
        row = db.execute(
            """
            SELECT cases.*, clients.name AS client_name, clients.phone AS client_phone
            FROM cases LEFT JOIN clients ON clients.id = cases.client_id
            WHERE cases.id = ?
            """,
            (case_id,),
        ).fetchone()
    if not row:
        return jsonify({"error": "案件不存在"}), 404
    item = dict(row)
    item["health_score"] = health_score(row)
    item["health_label"] = health_label(item["health_score"])
    return jsonify(item)


@app.get("/api/cases/<int:case_id>/timeline")
def list_timeline(case_id):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM timeline_events WHERE case_id = ? ORDER BY event_date DESC, id DESC",
            (case_id,),
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/cases/<int:case_id>/timeline")
def create_timeline(case_id):
    payload = request.get_json(silent=True) or {}
    event_date = str(payload.get("event_date", "")).strip()
    title = str(payload.get("title", "")).strip()
    if not event_date or not title:
        return jsonify({"error": "请填写事件日期和事件标题"}), 400
    with get_db() as db:
        exists = db.execute("SELECT id FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not exists:
            return jsonify({"error": "案件不存在"}), 404
        cursor = db.execute(
            "INSERT INTO timeline_events (case_id, event_date, title, event_type, description) VALUES (?, ?, ?, ?, ?)",
            (case_id, event_date, title, payload.get("event_type", "其他"), payload.get("description", "").strip()),
        )
    log_activity("时间线", cursor.lastrowid, "添加事件", title)
    return jsonify({"id": cursor.lastrowid}), 201


@app.delete("/api/timeline/<int:event_id>")
def delete_timeline(event_id):
    with get_db() as db:
        cursor = db.execute("DELETE FROM timeline_events WHERE id = ?", (event_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "时间线事件不存在"}), 404
    return jsonify({"success": True})


@app.get("/clients")
def clients_page():
    return render_template("clients.html")


@app.get("/todos")
def todos_page():
    return render_template("todos.html")


@app.get("/statistics")
def statistics_page():
    return render_template("statistics.html")


@app.get("/activity-log")
def activity_log_page():
    return render_template("activity_log.html")


@app.get("/templates")
def templates_page():
    return render_template("templates.html")


@app.get("/api/statistics")
def statistics():
    with get_db() as db:
        total_cases = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        total_clients = db.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        open_todos = db.execute("SELECT COUNT(*) FROM todos WHERE status != '已完成'").fetchone()[0]
        completed_todos = db.execute("SELECT COUNT(*) FROM todos WHERE status = '已完成'").fetchone()[0]
        overdue_todos = db.execute(
            "SELECT COUNT(*) FROM todos WHERE status != '已完成' AND deadline IS NOT NULL AND deadline < ?",
            (date.today().isoformat(),),
        ).fetchone()[0]
        cases_by_status = [dict(row) for row in db.execute("SELECT status AS label, COUNT(*) AS value FROM cases GROUP BY status ORDER BY value DESC").fetchall()]
        cases_by_type = [dict(row) for row in db.execute("SELECT case_type AS label, COUNT(*) AS value FROM cases GROUP BY case_type ORDER BY value DESC").fetchall()]
        todos_by_priority = [dict(row) for row in db.execute("SELECT priority AS label, COUNT(*) AS value FROM todos WHERE status != '已完成' GROUP BY priority ORDER BY value DESC").fetchall()]
        risk_distribution = [dict(row) for row in db.execute("SELECT risk_level AS label, COUNT(*) AS value FROM cases GROUP BY risk_level ORDER BY value DESC").fetchall()]
        deadlines = [dict(row) for row in db.execute(
            "SELECT id, case_number, name, deadline, deadline_kind, risk_level FROM cases WHERE deadline IS NOT NULL AND deadline <= ? ORDER BY deadline",
            ((date.today() + timedelta(days=14)).isoformat(),),
        ).fetchall()]
        recent_logs = [dict(row) for row in db.execute("SELECT * FROM activity_logs ORDER BY created_at DESC, id DESC LIMIT 8").fetchall()]
    return jsonify({
        "total_cases": total_cases,
        "total_clients": total_clients,
        "open_todos": open_todos,
        "completed_todos": completed_todos,
        "overdue_todos": overdue_todos,
        "cases_by_status": cases_by_status,
        "cases_by_type": cases_by_type,
        "todos_by_priority": todos_by_priority,
        "risk_distribution": risk_distribution,
        "upcoming_deadlines": deadlines,
        "recent_logs": recent_logs,
    })


@app.get("/api/activity-logs")
def list_activity_logs():
    with get_db() as db:
        rows = db.execute("SELECT * FROM activity_logs ORDER BY created_at DESC, id DESC LIMIT 100").fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/api/todos")
def list_todos():
    status = request.args.get("status", "").strip()
    query = """
        SELECT todos.*, cases.name AS case_name
        FROM todos LEFT JOIN cases ON cases.id = todos.case_id
        WHERE 1 = 1
    """
    params = []
    if status:
        query += " AND todos.status = ?"
        params.append(status)
    query += " ORDER BY CASE todos.status WHEN '待办' THEN 0 WHEN '进行中' THEN 1 ELSE 2 END, todos.deadline IS NULL, todos.deadline"
    with get_db() as db:
        rows = db.execute(query, params).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/todos")
def create_todo():
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return jsonify({"error": "请填写待办标题"}), 400
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO todos (title, deadline, priority, status, case_id) VALUES (?, ?, ?, ?, ?)",
            (title, payload.get("deadline") or None, payload.get("priority", "普通"), payload.get("status", "待办"), payload.get("case_id") or None),
        )
    log_activity("待办", cursor.lastrowid, "创建待办", title)
    return jsonify({"id": cursor.lastrowid}), 201


@app.put("/api/todos/<int:todo_id>")
def update_todo(todo_id):
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return jsonify({"error": "请填写待办标题"}), 400
    with get_db() as db:
        cursor = db.execute(
            "UPDATE todos SET title = ?, deadline = ?, priority = ?, status = ?, case_id = ? WHERE id = ?",
            (title, payload.get("deadline") or None, payload.get("priority", "普通"), payload.get("status", "待办"), payload.get("case_id") or None, todo_id),
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "待办不存在"}), 404
    log_activity("待办", todo_id, "编辑待办", title)
    return jsonify({"success": True})


@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    with get_db() as db:
        row = db.execute("SELECT title FROM todos WHERE id = ?", (todo_id,)).fetchone()
        cursor = db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "待办不存在"}), 404
    log_activity("待办", todo_id, "删除待办", row["title"])
    return jsonify({"success": True})


@app.get("/api/cases/options")
def case_options():
    with get_db() as db:
        rows = db.execute("SELECT id, case_number, name FROM cases ORDER BY id DESC").fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/api/clients/options")
def client_options():
    with get_db() as db:
        rows = db.execute("SELECT id, name, client_type FROM clients ORDER BY name").fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/api/clients/<int:client_id>/followups")
def list_client_followups(client_id):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT client_followups.*, cases.name AS case_name
            FROM client_followups LEFT JOIN cases ON cases.id = client_followups.case_id
            WHERE client_followups.client_id = ?
            ORDER BY followup_date DESC, id DESC
            """,
            (client_id,),
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/clients/<int:client_id>/followups")
def create_client_followup(client_id):
    payload = request.get_json(silent=True) or {}
    followup_date = str(payload.get("followup_date", "")).strip()
    content = str(payload.get("content", "")).strip()
    if not followup_date or not content:
        return jsonify({"error": "请填写跟进日期和跟进内容"}), 400
    with get_db() as db:
        client = db.execute("SELECT name FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not client:
            return jsonify({"error": "客户不存在"}), 404
        cursor = db.execute(
            "INSERT INTO client_followups (client_id, case_id, followup_date, channel, content, next_action) VALUES (?, ?, ?, ?, ?, ?)",
            (client_id, payload.get("case_id") or None, followup_date, payload.get("channel", "电话"), content, payload.get("next_action", "").strip()),
        )
    log_activity("客户跟进", cursor.lastrowid, "新增跟进", f"{client['name']}：{content}")
    return jsonify({"id": cursor.lastrowid}), 201


@app.delete("/api/client-followups/<int:followup_id>")
def delete_client_followup(followup_id):
    with get_db() as db:
        row = db.execute("SELECT content FROM client_followups WHERE id = ?", (followup_id,)).fetchone()
        cursor = db.execute("DELETE FROM client_followups WHERE id = ?", (followup_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "跟进记录不存在"}), 404
    log_activity("客户跟进", followup_id, "删除跟进", row["content"])
    return jsonify({"success": True})


@app.get("/api/clients")
def list_clients():
    keyword = request.args.get("keyword", "").strip()
    query = "SELECT * FROM clients WHERE 1 = 1"
    params = []
    if keyword:
        query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)"
        params.extend([f"%{keyword}%"] * 3)
    query += " ORDER BY created_at DESC, id DESC"
    with get_db() as db:
        rows = db.execute(query, params).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/clients")
def create_client():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    if not name:
        return jsonify({"error": "请填写客户名称"}), 400
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO clients (name, client_type, phone, email) VALUES (?, ?, ?, ?)",
            (name, payload.get("client_type", "个人"), payload.get("phone", "").strip(), payload.get("email", "").strip()),
        )
    log_activity("客户", cursor.lastrowid, "创建客户", name)
    return jsonify({"id": cursor.lastrowid}), 201


@app.put("/api/clients/<int:client_id>")
def update_client(client_id):
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    if not name:
        return jsonify({"error": "请填写客户名称"}), 400
    with get_db() as db:
        cursor = db.execute(
            "UPDATE clients SET name = ?, client_type = ?, phone = ?, email = ? WHERE id = ?",
            (name, payload.get("client_type", "个人"), payload.get("phone", "").strip(), payload.get("email", "").strip(), client_id),
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "客户不存在"}), 404
    log_activity("客户", client_id, "编辑客户", name)
    return jsonify({"success": True})


@app.delete("/api/clients/<int:client_id>")
def delete_client(client_id):
    with get_db() as db:
        row = db.execute("SELECT name FROM clients WHERE id = ?", (client_id,)).fetchone()
        cursor = db.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "客户不存在"}), 404
    log_activity("客户", client_id, "删除客户", row["name"])
    return jsonify({"success": True})


@app.get("/api/cases")
def list_cases():
    keyword = request.args.get("keyword", "").strip()
    status = request.args.get("status", "").strip()
    case_type = request.args.get("type", "").strip()
    risk_level = request.args.get("risk_level", "").strip()
    owner = request.args.get("owner", "").strip()
    tag = request.args.get("tag", "").strip()
    client_id = request.args.get("client_id", "").strip()
    query = """
        SELECT cases.*, clients.name AS client_name
        FROM cases LEFT JOIN clients ON clients.id = cases.client_id
        WHERE 1 = 1
    """
    params = []
    if keyword:
        query += " AND (cases.case_number LIKE ? OR cases.name LIKE ? OR COALESCE(clients.name, '') LIKE ? OR COALESCE(cases.tags, '') LIKE ? OR COALESCE(cases.owner_name, '') LIKE ?)"
        params.extend([f"%{keyword}%"] * 5)
    if status:
        query += " AND cases.status = ?"
        params.append(status)
    if case_type:
        query += " AND cases.case_type = ?"
        params.append(case_type)
    if risk_level:
        query += " AND cases.risk_level = ?"
        params.append(risk_level)
    if owner:
        query += " AND cases.owner_name = ?"
        params.append(owner)
    if tag:
        query += " AND cases.tags LIKE ?"
        params.append(f"%{tag}%")
    if client_id:
        query += " AND cases.client_id = ?"
        params.append(client_id)
    query += " ORDER BY cases.created_at DESC, cases.id DESC"
    with get_db() as db:
        rows = db.execute(query, params).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["health_score"] = health_score(row)
        item["health_label"] = health_label(item["health_score"])
        items.append(item)
    return jsonify(items)


@app.get("/api/cases/export")
def export_cases():
    with get_db() as db:
        rows = db.execute(
            """
            SELECT cases.case_number, cases.name, cases.case_type, clients.name AS client_name,
                   cases.status, cases.risk_level, cases.owner_name, cases.tags,
                   cases.deadline_kind, cases.deadline, cases.fee_status, cases.invoice_status
            FROM cases LEFT JOIN clients ON clients.id = cases.client_id
            ORDER BY cases.created_at DESC, cases.id DESC
            """
        ).fetchall()
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["案号", "案件名称", "案由", "客户", "状态", "风险等级", "负责人", "标签", "关键日期类型", "关键日期", "收费状态", "开票状态"])
    writer.writerows([list(row) for row in rows])
    payload = io.BytesIO(("\ufeff" + stream.getvalue()).encode("utf-8"))
    return send_file(payload, mimetype="text/csv", as_attachment=True, download_name="caseflow-cases.csv")


@app.post("/api/cases")
def create_case():
    payload = request.get_json(silent=True) or {}
    required = ["case_number", "name", "case_type"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        return jsonify({"error": "请填写案号、案件名称和案件类型"}), 400
    try:
        with get_db() as db:
            cursor = db.execute(
                """
                INSERT INTO cases (case_number, name, case_type, status, client_id, deadline, description, claim_amount, fee_amount, fee_status, invoice_status, risk_level, owner_name, tags, deadline_kind)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["case_number"].strip(),
                    payload["name"].strip(),
                    payload["case_type"].strip(),
                    payload.get("status", "一审进行中"),
                    payload.get("client_id") or None,
                    payload.get("deadline") or None,
                    payload.get("description", "").strip(),
                    payload.get("claim_amount") or None,
                    payload.get("fee_amount") or None,
                    payload.get("fee_status", "未收费"),
                    payload.get("invoice_status", "未开票"),
                    payload.get("risk_level", "中"),
                    payload.get("owner_name", "").strip(),
                    payload.get("tags", "").strip(),
                    payload.get("deadline_kind", "关键节点"),
                ),
            )
            case_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"error": "案号已存在，请使用唯一案号"}), 409
    log_activity("案件", case_id, "创建案件", payload["name"].strip())
    return jsonify({"id": case_id}), 201


@app.put("/api/cases/<int:case_id>")
def update_case(case_id):
    payload = request.get_json(silent=True) or {}
    required = ["case_number", "name", "case_type"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        return jsonify({"error": "请填写案号、案件名称和案件类型"}), 400
    try:
        with get_db() as db:
            cursor = db.execute(
                """
                UPDATE cases
                SET case_number = ?, name = ?, case_type = ?, status = ?, client_id = ?, deadline = ?, description = ?, claim_amount = ?, fee_amount = ?, fee_status = ?, invoice_status = ?, risk_level = ?, owner_name = ?, tags = ?, deadline_kind = ?
                WHERE id = ?
                """,
                (
                    payload["case_number"].strip(),
                    payload["name"].strip(),
                    payload["case_type"].strip(),
                    payload.get("status", "一审进行中"),
                    payload.get("client_id") or None,
                    payload.get("deadline") or None,
                    payload.get("description", "").strip(),
                    payload.get("claim_amount") or None,
                    payload.get("fee_amount") or None,
                    payload.get("fee_status", "未收费"),
                    payload.get("invoice_status", "未开票"),
                    payload.get("risk_level", "中"),
                    payload.get("owner_name", "").strip(),
                    payload.get("tags", "").strip(),
                    payload.get("deadline_kind", "关键节点"),
                    case_id,
                ),
            )
            if cursor.rowcount == 0:
                return jsonify({"error": "案件不存在"}), 404
    except sqlite3.IntegrityError:
        return jsonify({"error": "案号已存在，请使用唯一案号"}), 409
    log_activity("案件", case_id, "编辑案件", payload["name"].strip())
    return jsonify({"success": True})


@app.post("/api/cases/<int:case_id>/advance-status")
def advance_case_status(case_id):
    with get_db() as db:
        row = db.execute("SELECT status FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not row:
            return jsonify({"error": "案件不存在"}), 404
        current = row["status"]
        try:
            next_status = CASE_STATUSES[CASE_STATUSES.index(current) + 1]
        except (ValueError, IndexError):
            return jsonify({"error": "当前案件已处于最终状态，无法继续推进"}), 400
        db.execute("UPDATE cases SET status = ? WHERE id = ?", (next_status, case_id))
    log_activity("案件", case_id, "推进状态", f"{current} → {next_status}")
    return jsonify({"success": True, "status": next_status})


@app.post("/api/cases/<int:case_id>/close")
def close_case(case_id):
    with get_db() as db:
        cursor = db.execute("UPDATE cases SET status = '已结案' WHERE id = ?", (case_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "案件不存在"}), 404
    log_activity("案件", case_id, "标记结案", "状态更新为已结案")
    return jsonify({"success": True, "status": "已结案"})


@app.post("/api/cases/<int:case_id>/toggle-fee")
def toggle_fee_status(case_id):
    values = ["未收费", "部分收费", "已收费"]
    with get_db() as db:
        row = db.execute("SELECT fee_status FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not row:
            return jsonify({"error": "案件不存在"}), 404
        next_value = values[(values.index(row["fee_status"] or values[0]) + 1) % len(values)]
        db.execute("UPDATE cases SET fee_status = ? WHERE id = ?", (next_value, case_id))
    log_activity("案件", case_id, "切换收费状态", next_value)
    return jsonify({"success": True, "value": next_value})


@app.post("/api/cases/<int:case_id>/toggle-invoice")
def toggle_invoice_status(case_id):
    values = ["未开票", "部分开票", "已开票"]
    with get_db() as db:
        row = db.execute("SELECT invoice_status FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not row:
            return jsonify({"error": "案件不存在"}), 404
        next_value = values[(values.index(row["invoice_status"] or values[0]) + 1) % len(values)]
        db.execute("UPDATE cases SET invoice_status = ? WHERE id = ?", (next_value, case_id))
    log_activity("案件", case_id, "切换开票状态", next_value)
    return jsonify({"success": True, "value": next_value})


@app.delete("/api/cases/<int:case_id>")
def delete_case(case_id):
    with get_db() as db:
        row = db.execute("SELECT name FROM cases WHERE id = ?", (case_id,)).fetchone()
        cursor = db.execute("DELETE FROM cases WHERE id = ?", (case_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "案件不存在"}), 404
    log_activity("案件", case_id, "删除案件", row["name"])
    return jsonify({"success": True})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "caseflow-manager"})


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5066, debug=True)
elif os.environ.get("VERCEL"):
    # Vercel Demo 模式：使用临时目录并自动准备脱敏演示数据。
    init_db()
    with get_db() as db:
        has_cases = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0] > 0
    if not has_cases:
        from seed_demo import seed
        seed()
