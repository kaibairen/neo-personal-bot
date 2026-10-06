# neo-personal-bot

个人化的可自定义工作团队。

人用一句话点名角色。控制面只做角色、意图和审批。需要改仓库时，把一张内部任务票派给 [neo cloud agent](https://github.com/Neo2Agent/neo-cloud-agent)。Cursor Cloud Agents 是另一套适配器，不和 neo 共用请求字段。

## 展出

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/neo-personal-bot
.venv/bin/uvicorn neo_personal_bot.api:app --host 127.0.0.1 --port 8765
```

浏览器打开 `http://127.0.0.1:8765`。默认后端是本地录像，不需要云账号。三条样例：

- `@工程师 在 neo-personal-bot 里给 README 加上一行产品一句话，并开 PR` → 状态、分支、PR
- `@工程师 给客户发送这封邮件` → 待审批，不派发
- `@研究员 我们团队有哪些人` → 只回复，不派发

接到真的 neo cloud agent 时：

```bash
NEO_PERSONAL_BOT_BACKEND=neo \
NEO_CLOUD_BASE_URL=https://你的控制面 \
NEO_CLOUD_TOKEN=你的令牌 \
.venv/bin/uvicorn neo_personal_bot.api:app --host 127.0.0.1 --port 8765
```

`CURSOR_API_KEY` 只在角色的 `backend` 设为 `cursor` 时使用，请求打到 `POST /v1/agents`。

## 文档

- [产品 PRD](docs/prd.md)
- [架构说明](docs/architecture.md)
- [Grok Bot、技术栈与开源方案](docs/research.md)
