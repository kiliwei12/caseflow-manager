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

## 上线注意事项

- 生产环境应使用持久化磁盘保存 `data/caseflow.db`。
- 不要把包含真实客户信息的数据库提交到 GitHub。
- 后续加入登录和权限控制后，再开放给真实团队使用。
- 部署平台的启动命令使用 Dockerfile 默认命令，端口读取 `PORT` 环境变量。

