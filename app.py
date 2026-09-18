from pathlib import Path
import sqlite3

from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "caseflow.db"

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


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
                status TEXT NOT NULL DEFAULT '进行中',
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
            """
        )


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
    return jsonify(dict(row))


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


@app.get("/api/statistics")
def statistics():
    with get_db() as db:
        total_cases = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        total_clients = db.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        open_todos = db.execute("SELECT COUNT(*) FROM todos WHERE status != '已完成'").fetchone()[0]
        completed_todos = db.execute("SELECT COUNT(*) FROM todos WHERE status = '已完成'").fetchone()[0]
        cases_by_status = [dict(row) for row in db.execute("SELECT status AS label, COUNT(*) AS value FROM cases GROUP BY status ORDER BY value DESC").fetchall()]
        cases_by_type = [dict(row) for row in db.execute("SELECT case_type AS label, COUNT(*) AS value FROM cases GROUP BY case_type ORDER BY value DESC").fetchall()]
        todos_by_priority = [dict(row) for row in db.execute("SELECT priority AS label, COUNT(*) AS value FROM todos WHERE status != '已完成' GROUP BY priority ORDER BY value DESC").fetchall()]
    return jsonify({
        "total_cases": total_cases,
        "total_clients": total_clients,
        "open_todos": open_todos,
        "completed_todos": completed_todos,
        "cases_by_status": cases_by_status,
        "cases_by_type": cases_by_type,
        "todos_by_priority": todos_by_priority,
    })


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
    return jsonify({"success": True})


@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    with get_db() as db:
        cursor = db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "待办不存在"}), 404
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
    return jsonify({"success": True})


@app.delete("/api/clients/<int:client_id>")
def delete_client(client_id):
    with get_db() as db:
        cursor = db.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "客户不存在"}), 404
    return jsonify({"success": True})


@app.get("/api/cases")
def list_cases():
    keyword = request.args.get("keyword", "").strip()
    status = request.args.get("status", "").strip()
    query = """
        SELECT cases.*, clients.name AS client_name
        FROM cases LEFT JOIN clients ON clients.id = cases.client_id
        WHERE 1 = 1
    """
    params = []
    if keyword:
        query += " AND (cases.case_number LIKE ? OR cases.name LIKE ? OR COALESCE(clients.name, '') LIKE ?)"
        params.extend([f"%{keyword}%"] * 3)
    if status:
        query += " AND cases.status = ?"
        params.append(status)
    query += " ORDER BY cases.created_at DESC, cases.id DESC"
    with get_db() as db:
        rows = db.execute(query, params).fetchall()
    return jsonify([dict(row) for row in rows])


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
                INSERT INTO cases (case_number, name, case_type, status, client_id, deadline, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["case_number"].strip(),
                    payload["name"].strip(),
                    payload["case_type"].strip(),
                    payload.get("status", "进行中"),
                    payload.get("client_id") or None,
                    payload.get("deadline") or None,
                    payload.get("description", "").strip(),
                ),
            )
            case_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"error": "案号已存在，请使用唯一案号"}), 409
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
                SET case_number = ?, name = ?, case_type = ?, status = ?, client_id = ?, deadline = ?, description = ?
                WHERE id = ?
                """,
                (
                    payload["case_number"].strip(),
                    payload["name"].strip(),
                    payload["case_type"].strip(),
                    payload.get("status", "进行中"),
                    payload.get("client_id") or None,
                    payload.get("deadline") or None,
                    payload.get("description", "").strip(),
                    case_id,
                ),
            )
            if cursor.rowcount == 0:
                return jsonify({"error": "案件不存在"}), 404
    except sqlite3.IntegrityError:
        return jsonify({"error": "案号已存在，请使用唯一案号"}), 409
    return jsonify({"success": True})


@app.delete("/api/cases/<int:case_id>")
def delete_case(case_id):
    with get_db() as db:
        cursor = db.execute("DELETE FROM cases WHERE id = ?", (case_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "案件不存在"}), 404
    return jsonify({"success": True})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "caseflow-manager"})


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5066, debug=True)
