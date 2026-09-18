"""为面试演示准备一组脱敏示例数据。"""
from app import get_db, init_db


def seed():
    init_db()
    with get_db() as db:
        if db.execute("SELECT COUNT(*) FROM cases").fetchone()[0] > 0:
            print("数据库已有案件，跳过演示数据写入")
            return

        client_id = db.execute(
            "INSERT INTO clients (name, client_type, phone, email) VALUES (?, ?, ?, ?)",
            ("星河科技有限公司", "企业", "13800000001", "legal@xinghe.example"),
        ).lastrowid
        case_id = db.execute(
            """
            INSERT INTO cases (case_number, name, case_type, status, client_id, deadline, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("(2026)沪0101民初001号", "星河科技诉远航供应链合同纠纷", "合同纠纷", "进行中", client_id, "2026-10-15", "围绕设备采购合同履约和逾期付款的争议。"),
        ).lastrowid
        db.execute(
            "INSERT INTO cases (case_number, name, case_type, status, client_id, deadline, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("(2025)沪0101知初008号", "星河科技商标侵权纠纷", "知识产权", "已结案", client_id, None, "已完成调解并结案。"),
        )
        db.executemany(
            "INSERT INTO todos (title, deadline, priority, status, case_id) VALUES (?, ?, ?, ?, ?)",
            [
                ("补充提交付款凭证", "2026-10-08", "紧急", "待办", case_id),
                ("与客户确认庭审提纲", "2026-10-10", "重要", "进行中", case_id),
                ("归档已结案件材料", "2026-09-30", "普通", "已完成", None),
            ],
        )
        db.executemany(
            "INSERT INTO timeline_events (case_id, event_date, title, event_type, description) VALUES (?, ?, ?, ?, ?)",
            [
                (case_id, "2026-09-18", "完成首次客户访谈", "沟通", "确认争议焦点、证据范围和客户预期。"),
                (case_id, "2026-09-20", "提交立案材料", "立案", "完成起诉材料和证据目录整理。"),
            ],
        )
    print("演示数据写入完成")


if __name__ == "__main__":
    seed()

