# CaseFlow v1.1.1

修正独立桌面版“本地安装”页面：现在准确显示 macOS 与 Windows 各自的数据库位置和新版下载地址。安装 v1.1.1 会替换旧版应用，但不会清除原有本地数据库。

## 下载

- **macOS Apple Silicon**：`CaseFlow-macOS-Apple-Silicon-v1.1.1.dmg`
- **Windows 10/11 x64**：`CaseFlow-Windows-Setup-v1.1.1.exe`

## 安装

### macOS

1. 打开 DMG。
2. 将 `CaseFlow.app` 拖入 Applications。
3. 首次启动如果出现开发者验证提示，请右键应用并选择“打开”，或在“系统设置 → 隐私与安全性”中允许打开。

### Windows

1. 双击 Setup EXE。
2. 按安装向导完成安装。
3. 从开始菜单或桌面快捷方式启动 CaseFlow。

## 数据与隐私

- macOS 数据：`~/Library/Application Support/CaseFlow/caseflow.db`
- Windows 数据：`%APPDATA%\CaseFlow\caseflow.db`
- 数据仅保存在当前电脑中，不发送到 CaseFlow 云端。
- 升级或重新安装应用不会覆盖数据库，仍建议定期备份。

## 说明

macOS DMG 使用临时本地签名，尚未进行 Apple Developer ID 公证。Windows 安装包尚未购买代码签名证书，因此系统可能显示未知发布者提示。
