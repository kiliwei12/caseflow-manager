# CaseFlow 部署说明

## 本地生产模式验证

```bash
cd /Users/wei/Documents/Codex/2026-09-18/vibecoding/caseflow-manager
source .venv/bin/activate
pip install -r requirements.txt
python -c "from app import init_db; init_db()"
gunicorn --bind 127.0.0.1:5066 --workers 2 app:app
```

浏览器访问 `http://127.0.0.1:5066`。

## Docker 验证

```bash
docker build -t caseflow-manager .
docker run --rm -p 5066:5066 caseflow-manager
```

## Render Demo 部署

项目根目录已经包含 `render.yaml` 和 `Dockerfile`。在 Render 中选择 **New → Blueprint**，连接 GitHub 仓库 `kiliwei12/caseflow-manager`，Render 会读取该配置创建 Web Service。

部署完成后，访问 Render 分配的 `onrender.com` 地址，并先打开 `/health` 确认服务状态为 `ok`。

当前 Demo 启动时会自动写入脱敏演示数据，适合作品集展示。免费实例重启或重新部署后，SQLite 数据可能被重置；不要在这个 Demo 中保存真实客户信息。

## 上线注意事项

- 生产环境应使用持久化磁盘保存 `data/caseflow.db`。
- 不要把包含真实客户信息的数据库提交到 GitHub。
- 后续加入登录和权限控制后，再开放给真实团队使用。
- 部署平台的启动命令使用 Dockerfile 默认命令，端口读取 `PORT` 环境变量。
