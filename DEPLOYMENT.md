# CaseFlow 部署说明

## Docker 验证

```bash
docker build -t caseflow-manager .
docker run --rm -p 8080:8080 caseflow-manager
```

## Render Demo 部署

项目根目录已经包含 `render.yaml` 和 `Dockerfile`。在 Render 中选择 **New → Blueprint**，连接 GitHub 仓库 `kiliwei12/caseflow-manager`，Render 会读取该配置创建 Web Service。

部署完成后，访问 Render 分配的 `onrender.com` 地址，并先打开 `/health` 确认服务状态为 `ok`。

Render Demo 会为每个浏览器创建独立的匿名临时 SQLite 数据库，并自动写入脱敏演示数据。访客之间不会共享修改，临时数据会在 24 小时后或服务重启时清理；不要在 Demo 中保存真实客户信息。

若现有 Render 服务不是通过 Blueprint 创建，请在服务的 Environment 中添加：

```text
CASEFLOW_DEMO_MODE=1
CASEFLOW_DATA_DIR=/tmp/caseflow-demo
CASEFLOW_DEMO_TTL_HOURS=24
SECRET_KEY=<随机长字符串>
```

## Vercel Demo 部署

项目也包含 `vercel.json`，可以直接导入 GitHub 仓库 `kiliwei12/caseflow-manager`。Vercel 会识别根目录的 `app.py` Flask 实例，并将其部署为一个 Python Function。

在 Vercel 中选择 **Add New → Project → Import Git Repository**，选择该仓库后直接点击 Deploy。部署完成后访问 `/health` 检查服务状态。

Vercel Demo 同样按匿名访客隔离临时数据；函数重启后数据可能恢复为初始演示数据。若需要持久化，应将 SQLite 替换为托管 PostgreSQL 或其他外部数据库。

## 上线注意事项

- 真实业务优先使用本地私有安装版，数据保存在 `data/caseflow.db`。
- 不要把包含真实客户信息的数据库提交到 GitHub。
- 后续加入登录和权限控制后，再开放给真实团队使用。
- 部署平台的启动命令使用 Dockerfile 默认命令，端口读取 `PORT` 环境变量。
