"""写入脱敏、可重复使用的 CaseFlow 演示数据。"""


def seed_connection(db):
    """向一个已初始化的 SQLite 连接写入演示数据。"""
    if db.execute("SELECT COUNT(*) FROM cases").fetchone()[0] > 0:
        return False

    clients = {}
    for name, client_type, phone, email in [
        ("澄明智造科技有限公司", "企业", "13800001001", "legal@chengming.example"),
        ("云岚新能源有限公司", "企业", "13800001002", "legal@yunlan.example"),
        ("林先生", "个人", "13800001003", "lin.example@caseflow.local"),
    ]:
        clients[name] = db.execute(
            "INSERT INTO clients (name, client_type, phone, email) VALUES (?, ?, ?, ?)",
            (name, client_type, phone, email),
        ).lastrowid

    cases = {}
    case_rows = [
        (
            "(2026)沪0101民初1288号", "澄明智造诉远界供应链买卖合同纠纷", "合同纠纷", "一审进行中",
            "澄明智造科技有限公司", "2026-09-23", "开庭日期", "高", "李晓", "紧急,大额,开庭",
            3200000, 180000, "部分收费", "未开票", "围绕设备采购合同的履行、验收及逾期付款展开争议。",
        ),
        (
            "(2026)沪01知民终326号", "云岚新能源商标侵权纠纷二审", "知识产权", "二审进行中",
            "云岚新能源有限公司", "2026-09-27", "举证期限", "中", "王晨", "二审,证据补强",
            860000, 95000, "已收费", "已开票", "一审判决后对方提起上诉，当前重点为补充混淆可能性证据。",
        ),
        (
            "(2025)沪0101民初0812号", "林先生劳动争议纠纷", "劳动争议", "已结案",
            "林先生", None, "关键节点", "低", "陈悦", "已结案,调解",
            180000, 28000, "已收费", "已开票", "经庭前调解达成和解，已完成款项支付与材料归档。",
        ),
    ]
    for row in case_rows:
        (
            number, name, case_type, status, client_name, deadline, deadline_kind, risk_level,
            owner, tags, claim, fee, fee_status, invoice_status, description,
        ) = row
        cases[name] = db.execute(
            """
            INSERT INTO cases
            (case_number, name, case_type, status, client_id, deadline, deadline_kind,
             risk_level, owner_name, tags, claim_amount, fee_amount, fee_status, invoice_status, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (number, name, case_type, status, clients[client_name], deadline, deadline_kind,
             risk_level, owner, tags, claim, fee, fee_status, invoice_status, description),
        ).lastrowid

    case_a = cases["澄明智造诉远界供应链买卖合同纠纷"]
    case_b = cases["云岚新能源商标侵权纠纷二审"]
    case_c = cases["林先生劳动争议纠纷"]

    db.executemany(
        "INSERT INTO todos (title, deadline, priority, status, case_id) VALUES (?, ?, ?, ?, ?)",
        [
            ("整理开庭举证材料", "2026-09-21", "紧急", "进行中", case_a),
            ("与客户确认庭审陈述重点", "2026-09-22", "重要", "待办", case_a),
            ("补充提交商标使用证据", "2026-09-26", "重要", "待办", case_b),
            ("归档调解协议及结案材料", "2026-09-18", "普通", "已完成", case_c),
        ],
    )
    db.executemany(
        "INSERT INTO timeline_events (case_id, event_date, title, event_type, description) VALUES (?, ?, ?, ?, ?)",
        [
            (case_a, "2026-08-28", "接受委托", "沟通", "完成案件初步评估并明确证据缺口。"),
            (case_a, "2026-09-05", "完成立案", "立案", "法院受理案件并确定首次开庭日期。"),
            (case_a, "2026-09-23", "首次开庭", "开庭", "围绕合同履行、验收和付款节点进行举证质证。"),
            (case_b, "2026-09-02", "收到上诉材料", "其他", "完成一审材料复盘，制定二审证据补强清单。"),
            (case_b, "2026-09-27", "提交补充证据", "其他", "提交商标使用、市场影响和混淆可能性相关材料。"),
            (case_c, "2025-12-16", "达成调解", "调解", "双方达成调解并完成款项支付。"),
        ],
    )
    db.executemany(
        """
        INSERT INTO client_followups (client_id, case_id, followup_date, channel, content, next_action)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (clients["澄明智造科技有限公司"], case_a, "2026-09-18", "会议", "与法务负责人确认开庭材料分工及到庭安排。", "9 月 21 日前确认全部证据原件。"),
            (clients["澄明智造科技有限公司"], case_a, "2026-09-16", "电话", "同步对方最新和解意向，客户决定继续推进开庭。", "准备庭审陈述与和解底线方案。"),
            (clients["云岚新能源有限公司"], case_b, "2026-09-17", "邮件", "发送二审补充证据目录并确认盖章文件。", "9 月 24 日回收盖章材料。"),
        ],
    )
    db.executemany(
        "INSERT INTO activity_logs (entity_type, entity_id, action, detail) VALUES (?, ?, ?, ?)",
        [
            ("案件", case_a, "创建案件", "澄明智造诉远界供应链买卖合同纠纷"),
            ("案件", case_a, "更新风险等级", "调整为高风险：开庭日期临近且待补充证据"),
            ("客户跟进", clients["澄明智造科技有限公司"], "新增跟进", "确认开庭材料分工及到庭安排"),
            ("待办", case_a, "创建待办", "整理开庭举证材料"),
            ("案件", case_b, "推进状态", "一审已结案 → 二审进行中"),
            ("案件", case_c, "标记结案", "调解完成并归档"),
        ],
    )
    db.executemany(
        "INSERT INTO work_records (case_id, work_date, category, content, hours) VALUES (?, ?, ?, ?, ?)",
        [
            (case_a, "2026-09-18", "起草", "整理庭审提纲与争议焦点", 2.5),
            (case_a, "2026-09-19", "沟通", "与客户确认证据原件及出庭安排", 1.0),
            (case_b, "2026-09-17", "调研", "检索商标混淆可能性相关裁判规则", 3.0),
        ],
    )
    db.executemany(
        """INSERT INTO document_templates
           (name, category, description, content) VALUES (?, ?, ?, ?)""",
        [
            ("民事起诉状基础模板", "起诉状", "适用于一般合同及侵权纠纷，可替换花括号中的字段。", "原告：{原告名称}\n被告：{被告名称}\n\n诉讼请求：\n{诉讼请求}\n\n事实与理由：\n{事实与理由}\n\n此致\n{受理法院}"),
            ("客户沟通纪要", "备忘录", "用于会谈后快速沉淀事实、结论和下一步行动。", "会议日期：{日期}\n参与人员：{参与人员}\n\n核心事实：\n{核心事实}\n\n达成结论：\n{结论}\n\n下一步行动：\n{下一步行动}"),
        ],
    )
    return True


def seed():
    """为当前运行模式的数据库写入演示数据。"""
    from app import get_db, init_db

    init_db()
    with get_db() as db:
        inserted = seed_connection(db)
    print("CaseFlow 作品集演示数据写入完成" if inserted else "数据库已有案件，跳过演示数据写入")


if __name__ == "__main__":
    seed()
