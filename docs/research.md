# 技术调研

核对日期：2026-10-06。价格、星标和限额会变，以页面当天的文字为准。找不到的接口写成缺口，不补。

## Grok 不是一个 Bot

公开文档把产品拆开。和「个人化可自定义工作团队」最接近的是 **Grok Bot**，不是 grok.com 里的通用助手，也不是 X 上的 @grok。

| 产品 | 交互单位 | 和团队的关系 |
| --- | --- | --- |
| grok.com / iOS / Android | 一条多轮对话 | 一个助手。多 agent 是并行查完再合成一条带引用的回答 |
| Grok on X | 社交产品里的 Grok | 2026-10-06 没有打开 X 帮助中心。不把它当成工作单位 |
| API `https://api.x.ai/v1` | 一次 Responses 请求 | 模型与工具，不是持久电脑 |
| Voice / Voice Agent Builder | 一段语音或一通电话 | 渠道，不是队友花名册 |
| Grok Build | 终端会话，或一份 workflow 报告 | 成百上千个一次性工人，跑完就散 |
| Grok Bot | 给一个命名 Bot 发消息 | 少数有职责的队友，共用该用户的一台云电脑 |

来源：<https://docs.x.ai/grok/overview>、<https://docs.x.ai/grok-bot/overview>、<https://docs.x.ai/llms.txt>、<https://docs.x.ai/developers/model-capabilities/text/multi-agent>、<https://x.ai/news/workflows>。

### Grok Bot 怎么设计

2026-10-06 的 [overview](https://docs.x.ai/grok-bot/overview) 写明：

- 每个 Bot 有名字、职责，消息就是界面。可以打字、听写或语音。
- Bot 跑在一台持久云电脑上，有浏览器、文件系统和终端。电脑在 **Cursor 的云**里。笔记本合上，工作继续。
- 套餐：付费个人 Cursor 计划、Cursor Teams，或绑定的个人 SuperGrok / Plus / Heavy。用量按周重置。
- 该用户的所有 Bot **共用**这台电脑的文件、浏览器会话和应用登录。隔离在用户与用户之间。文档要求把放上电脑的东西视为每个 Bot 都能碰到。
- 多个 Bot 可以并行。每个 Bot 一块屏幕，同一块屏幕上同时只有一个 computer-use 任务。
- Bot 会互相发消息、在群里交接，用户不必当路由器。
- 走一遍操作可以存成 skill，再按日程重跑。
- 记忆是稳定偏好、角色上下文和先前工作的摘要。会影响结论的决定要回源核对，不靠记忆。
- 站点挡住自动化、会话过期或需要人的步骤时，Bot 把步骤交回给人，而不是绕过去。

这是值得借的工作方式：一个角色一件可重复的结果；长期规则放在职责里，这一次的任务放在消息里；对外动作先停下来给人看；设备只负责对话和批准。

不照搬的部分：全角色共用登录态（Grok 自己说明这不是安全边界）；用「多 agent 合成一条答案」冒充团队；用 Build 那种匿名工人当日常编制；做一个什么都记得的通用助手。

Grok Bot 没有公开的 Bot CRUD REST。`llms.txt` 里这组页面是客户端说明。删 Bot 之后的保留，overview 指向 Cursor 的条款和计费页，而不是 `api.x.ai` 上的一个资源。

编码可以再委派给另一台 Cursor Cloud Agent，做完把文件抄回对话。控制面是队友对话，执行面是另一台电脑。neo-personal-bot 采用同一刀切法，只是控制面由我们自己写。

### Grok / xAI 公开技术栈

文档站自称为 SpaceXAI（xAI），仍在 `https://docs.x.ai/`。

| 层 | 公开方案 |
| --- | --- |
| 推理 | `https://api.x.ai/v1`，`Authorization: Bearer` |
| 推荐 API | Responses API。OpenAI SDK 把 `base_url` 指到这里。Chat Completions 被标为 Deprecated |
| 其它客户端 | `xai-sdk`、Vercel AI SDK `@ai-sdk/xai`、LiteLLM `xai/grok-4.7` |
| 旗舰文本 | `grok-4.7`。定价页在 200k prompt 以下约为输入 $2、缓存 $0.50、输出 $6 / 1M tokens；达到阈值后整次请求按高价。以 <https://docs.x.ai/developers/pricing> 为准 |
| 工具 | 网页搜索、X 搜索、代码执行、Collections、出图、远程 MCP 在服务端闭环。自定义函数把 `function_call` 交回调用方执行 |
| 语音 | `wss://api.x.ai/v1/realtime`，模型别名 `grok-voice-latest` |
| 多 agent API | `grok-4.20-multi-agent`（beta）。一次请求里的内部研究 agent，不能挂客户端函数，不能当团队编排器 |
| 数据 | 默认不用用户内容训练；非 ZDR 有约 30 天的审计保留。细节以安全 FAQ 和企业条款为准 |

个人工作团队如果只用 Grok API，能得到模型、搜索、沙箱代码、RAG 和函数协议。会话身份、渠道、审批、任务队列、命名角色、云电脑都要自己做。Grok 4.7 Fast 不在公开 API 上，只在 Cursor 和 Grok Build 里。

代码执行沙箱没有外网，也没有跨请求的磁盘。超时和内存的具体数字在文档里没有给出。

## neo cloud agent 是哪一个

公开名字正好是 neo-cloud-agent 的，是 <https://github.com/Neo2Agent/neo-cloud-agent>。README 写明对标 Cursor Cloud Agent。默认内核是 pi-agent，也可以选另一套 loop。它和 kaibairen 没有公开的 fork 关系。

已核对的创建契约（`packages/contracts/src/run.ts`，控制面 `POST /v1/runs`）：

- 必填 `prompt`。`repoUrls` 要是数组，除非同时给了 `envId`。
- 可选 `ref`、`expertId`、`expertTeamId`、`source`、`model`、`mode`（`agent` 或 `ask`）。
- 成功 `201`，body 是 `Run`。缺 prompt 为 `400`，`error` 为 `prompt is required`。
- 状态：`NOT_YET_STARTED` → `PROVISIONING` → `INSTALLING` → `RUNNING` → `IDLE`，另有 `WAITING_FOR_BACKGROUND_WORK`、`ERROR`、`ARCHIVED`、`EXPIRED`。
- 分支在 `branchName`。PR 在 `pullRequests[]`，其中有 `url`。
- 追问是 `POST /v1/runs/{id}/follow-ups`，同一个 run id。
- 鉴权是控制面的 Bearer 令牌或登录会话，不是 Cursor key。

同一组织的 `Neo2Agent/neo-bot` 是更早的 Web 控制面，不是个人团队产品。Telegram 入口会把用户原文直接开成 Run，仓库来自通知设置里的默认仓库，不选专家。neo-personal-bot 补上的就是这一层：先选角色，再决定派不派。

Cursor Cloud Agents 是第二条执行面，不是同一个接口：

- `POST https://api.cursor.com/v1/agents`
- `prompt.text` 必填，`repos[].url` 与 `startingRef` 可选，`autoCreatePR` 可选
- 响应里 agent id 是 `bc-...`，run 是另一个对象，初始状态常见 `CREATING`
- 完成后看 `GET /v1/agents/{id}/runs/{runId}` 的 `status`、`result`、`git.branches[].prUrl`
- v1 webhook 文档写明 coming soon
- 这个 GitHub 账号的 `cursor_browser_apk` 已经打过这组 API

两套字段在代码里分成 `neo_create_body` 和 `cursor_create_body`。内部只有 `TaskTicket`。

## 开源方案：拿来做什么

观察日 2026-10-06。不把星标当选型理由。

**借鉴形态，不整仓 fork**

| 项目 | 拿来做什么 | 不拿来做什么 |
| --- | --- | --- |
| [openclaw/openclaw](https://github.com/openclaw/openclaw) | 一个入口把渠道消息归一，角色写成工作区文件 | 当骨架。一个 Gateway 是一个信任边界，沙箱默认关，渠道和技能市场都在产品里 |
| [HKUDS/nanobot](https://github.com/HKUDS/nanobot) | 看一个小的 agent loop 怎么把工具留在循环里 | 当团队产品和隔离执行器。它是单人助手 |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | 看「聊天入口 + 远端终端」怎样拆 | 当控制面。它的产品是一个会成长的 agent |
| [paperclipai/paperclip](https://github.com/paperclipai/paperclip) | 抄「角色、任务、一次隔离运行」和数据库队列。它把 Cursor Cloud 列成可雇佣的执行器 | 整仓搬进来。它是公司操作系统，聊天是实验功能 |

**可以嵌进控制面的库**

- [pydantic-ai](https://github.com/pydantic/pydantic-ai)：以后让路由模型只决定「回复还是派发」。展出为了没有密钥也能跑，用的是确定性规则，不假装已经接了模型。
- [openai-agents-python](https://github.com/openai/openai-agents-python)：角色移交可以以后再加。它不提供隔离机器。
- CrewAI、LangGraph：名词和状态图可以参考。第一版一张任务票就够，不先引入。

**不要当底座**

- Dify、FastGPT：可视化 RAG 平台，许可证还对多租户 SaaS 和品牌有附加限制。
- Coze Studio、Agno、微软 Agent Framework：又一套平台，和薄控制面冲突。
- AutoGen：上游要求新项目改用 Agent Framework。
- [daytonaio/daytona](https://github.com/daytonaio/daytona)：开源仓已归档，核心开发转到私有库。
- `python-telegram-bot`：GPL-3.0。若要 Telegram，用 MIT 的 aiogram。
- Mem0、Letta、Graphiti：第一周用角色职责和消息记录就够。

**隔离执行，和聊天编排分开**

- 主路径：neo-cloud-agent 已经是这台云电脑。
- 第二路径：Cursor Cloud Agents API。
- 若以后要开源的命令执行器，再看 [OpenHands software-agent-sdk](https://github.com/OpenHands/software-agent-sdk) 的 `DockerWorkspace`。不要把 OpenHands 的整套 GUI 搬进来。
- E2B 的 microVM 是更硬的隔离，演示阶段不作为第一依赖。

## 我们选的栈

| 层 | 选择 | 原因 |
| --- | --- | --- |
| 控制面 | Python 3.12、FastAPI、Pydantic | 和飞书官方 SDK、以后的 Pydantic AI 同语言。网页和 CLI 共用一个函数 |
| 规则路由 | 确定性规则 | 展出不依赖模型密钥。审批必须在模型之前也能挡住 |
| 模型 | 暂不调用。以后用 OpenAI 兼容 HTTP，可指向 `https://api.x.ai/v1` 的 `grok-4.7` | Grok API 是推理，不是团队运行时 |
| 存储 | 展出 SQLite。生产 Postgres 16，`jobs` + `SKIP LOCKED` | 演示不为一张表加 Redis |
| 渠道 | 现在 CLI 和本机网页。下一渠道飞书或 aiogram | 没有一个小库同时覆盖飞书、企微、Slack |
| 执行 | `adapters/neo.py` 为主，`adapters/cursor.py` 为辅 | 用户要求的是 neo cloud agent。这个账号已经有 Cursor 客户端，所以第二套适配器保持独立 |
| 无凭证展出 | `adapters/fixture.py` | 状态序列与 Neo 的枚举一致，测试可以断网跑完 |

不选的理由同样具体：不在控制面里跑 shell，是因为 Grok Bot 把电脑放在云上，路由进程不该变成第二台没有审批的电脑。不 fork 大平台，是因为那些仓库的发布节奏、信任模型和 UI 会变成产品本身，而这里要的只有任务票和一张卡片。
