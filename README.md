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
- 工作记录：记录工作类别、内容和工时，自动汇总案件总工时
- 文书模板：管理文本模板及小体积 PDF/DOCX 附件，支持筛选、下载和批量删除
- 本地 SQLite 数据存储

## 本地安装

从 [CaseFlow v1.2.0 Release](https://github.com/kiliwei12/caseflow-manager/releases/tag/v1.2.0) 下载免 Python 的独立安装包：

- **macOS Apple Silicon（M 系列芯片）**：[下载 DMG 安装包](https://github.com/kiliwei12/caseflow-manager/releases/download/v1.2.0/CaseFlow-macOS-Apple-Silicon-v1.2.0.dmg)，打开后拖入“应用程序”。
- **Windows 10/11 x64**：[下载 Setup.exe 安装程序](https://github.com/kiliwei12/caseflow-manager/releases/download/v1.2.0/CaseFlow-Windows-Setup-v1.2.0.exe)，双击后按向导安装。

独立安装包无需预装 Python。本地数据分别保存在 macOS 的 `~/Library/Application Support/CaseFlow/` 和 Windows 的 `%APPDATA%\CaseFlow\`。

### 从源码运行（需要 Python）

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

源码运行的数据位于项目内的 `data/caseflow.db`；独立安装版的数据位于上文所述系统用户数据目录。数据库不会提交到 Git，更新演示数据前请先备份。

线上 Demo 使用匿名 Cookie 为每位访客创建独立临时数据库。不同浏览器和不同设备之间不会共享修改，临时数据可能在 24 小时后或服务重启时清理。

## 项目定位

CaseFlow 重点解决案件信息分散、关键日期易遗漏和进展不可追踪的问题，提供案件风险、健康度、客户跟进和操作审计能力。

## 产品差异化

- 案件风险等级与 0–100 健康度评分
- 未来 14 天关键日期预警
- 负责人、标签和高级筛选
- 客户跟进记录与下一步行动
- CSV 数据导出和操作日志

## 测试

```bash
python -m unittest discover -s tests
```
