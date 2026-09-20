# CaseFlow v1.2.0

本版本将原有占位入口升级为可实际操作的业务功能。

## 新增功能

- 案件工作记录：支持新增、编辑、删除工作内容和工时。
- 工时汇总：案件详情自动统计累计工时和记录数量。
- 文书模板管理：支持新增、查看、编辑、删除、分类筛选和批量删除。
- 模板附件：支持保存和下载最大 2MB 的 PDF / DOCX 文件。
- 示例数据：新增工作记录与文本模板，方便直接体验。
- 自动化测试：覆盖工作记录和文书模板主要操作闭环。

## 下载

- **macOS Apple Silicon**：`CaseFlow-macOS-Apple-Silicon-v1.2.0.dmg`
- **Windows 10/11 x64**：`CaseFlow-Windows-Setup-v1.2.0.exe`

## 数据与升级

- macOS 数据：`~/Library/Application Support/CaseFlow/caseflow.db`
- Windows 数据：`%APPDATA%\CaseFlow\caseflow.db`
- 安装新版不会删除现有本地数据库。

## 安全提示

macOS DMG 尚未进行 Apple Developer ID 公证，Windows 安装程序也未使用商业代码签名证书；首次打开可能出现系统安全提示。
