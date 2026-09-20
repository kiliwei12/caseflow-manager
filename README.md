# CaseFlow 案件管理平台

这是一个面向个人律师、法务和小型法律团队的案件全生命周期管理平台，提供两种明确分离的运行方式：

- **线上 Demo**：每个浏览器获得独立的匿名临时数据，仅用于体验。
- **本地私有版**：数据库保存在用户电脑中，用于管理真实业务数据。

线上 Demo：[caseflow-manager.onrender.com](https://caseflow-manager.onrender.com)

本项目以独立的产品设计、数据模型、界面和功能迭代为目标，用于展示 Flask 全栈开发与产品经理项目实践。

## 第一阶段 MVP

- 案件管理：创建、查看、编辑、删除和状态筛选
- 客户管理：维护客户基本信息
- 待办事项：关联案件、设置优先级和截止日期
- 案件详情：查看案件基础信息及关联待办
- 本地 SQLite 数据存储

## 本地安装

下载项目后运行：

- macOS：双击 `CaseFlow.command`
- Windows：双击 `CaseFlow.bat`

也可以通过终端运行：

```bash
# macOS / Linux
bash install_local.sh
bash start_local.sh
```

Windows 用户运行：

```powershell
powershell -ExecutionPolicy Bypass -File install_local.ps1
powershell -ExecutionPolicy Bypass -File start_local.ps1
```

也可以访问线上 Demo 中的“本地安装”页面查看说明。

## 演示数据

首次启动后，可写入脱敏的演示客户、案件、待办、时间线、客户跟进和操作日志：

```bash
python seed_demo.py
```

本地版业务数据位于 `data/caseflow.db`，不会提交到 Git。更新演示数据前请先备份该文件。

线上 Demo 使用匿名 Cookie 为每位访客创建独立临时数据库。不同浏览器和不同设备之间不会共享修改，临时数据可能在 24 小时后或服务重启时清理。

## 项目定位

CaseFlow 重点解决案件信息分散、关键日期易遗漏和进展不可追踪的问题，提供案件风险、健康度、客户跟进和操作审计能力。

## 产品差异化

- 案件风险等级与 0–100 健康度评分
- 未来 14 天关键日期预警
- 负责人、标签和高级筛选
- 客户跟进记录与下一步行动
- CSV 数据导出和操作日志
