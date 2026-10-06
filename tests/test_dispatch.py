from neo_personal_bot.adapters.fixture import FixtureNeoAdapter
from neo_personal_bot.jobs import Store
from neo_personal_bot.roles import exhibit_team
from neo_personal_bot.service import handle_message
from neo_personal_bot.tickets import Role, Team


def _handle(text: str, adapter: FixtureNeoAdapter | None = None, team: Team | None = None):
    adapter = adapter or FixtureNeoAdapter()
    store = Store(":memory:")
    card = handle_message(
        text,
        team=team or exhibit_team(),
        adapters={"neo": adapter},
        store=store,
    )
    return card, adapter, store


def test_engineer_dispatch_polls_until_idle():
    adapter = FixtureNeoAdapter(statuses=["NOT_YET_STARTED", "PROVISIONING", "IDLE"])
    card, adapter, _store = _handle(
        "@工程师 在 neo-personal-bot 里给 README 加上一行产品一句话，并开 PR",
        adapter,
    )
    assert card.kind == "dispatch"
    assert card.status == "IDLE"
    assert card.branch == "neo/readme-line"
    assert card.pr_url.endswith("/pull/1")
    assert len(adapter.created) == 1
    ticket = adapter.created[0]
    assert ticket.backend == "neo"
    assert ticket.want_pr is True
    assert ticket.repo_urls == ["https://github.com/kaibairen/neo-personal-bot"]
    assert "repoUrls" not in ticket.instruction
    assert "长期职责" in ticket.instruction


def test_send_stops_for_approval_and_does_not_dispatch():
    card, adapter, store = _handle("@工程师 给客户发送这封邮件")
    assert card.kind == "approval"
    assert card.status == "needs_approval"
    assert adapter.created == []
    assert store.list_jobs()[0]["kind"] == "approval"


def test_delete_production_stops_for_approval():
    card, adapter, _store = _handle("@工程师 删除生产数据库")
    assert card.status == "needs_approval"
    assert adapter.created == []


def test_researcher_reply_does_not_dispatch():
    card, adapter, _store = _handle("@研究员 我们团队有哪些人")
    assert card.kind == "reply"
    assert card.role_name == "研究员"
    assert adapter.created == []


def test_researcher_cannot_dispatch_without_a_repo():
    card, adapter, _store = _handle("@研究员 给 README 加上一行并开 PR")
    assert card.status == "no_repo"
    assert adapter.created == []


def test_unknown_role_and_missing_mention():
    unknown, adapter, _store = _handle("@财务 报销")
    assert unknown.kind == "reply"
    assert "没有 @财务" in unknown.summary
    assert adapter.created == []
    help_card, adapter, _store = _handle("今天做什么")
    assert "用 @角色 点名" in help_card.summary
    assert adapter.created == []


def test_cursor_backend_is_a_different_adapter():
    team = Team(
        id="studio",
        name="studio",
        roles=[
            Role(
                id="engineer",
                mention="工程师",
                duty="改仓库",
                repo_urls=["https://github.com/kaibairen/neo-personal-bot"],
                ref="main",
                backend="cursor",
            )
        ],
    )

    class CursorSpy:
        def __init__(self) -> None:
            self.created = []

        def create(self, ticket):
            self.created.append(ticket)
            from neo_personal_bot.tickets import ExternalRef

            return ExternalRef(
                backend="cursor",
                agent_id="bc-1",
                run_id="run-1",
                status="CREATING",
            )

        def refresh(self, ref):
            return ref.model_copy(
                update={
                    "status": "FINISHED",
                    "branch": "cursor/add-readme",
                    "pr_url": "https://github.com/kaibairen/neo-personal-bot/pull/9",
                    "summary": "done",
                }
            )

    neo = FixtureNeoAdapter()
    cursor = CursorSpy()
    store = Store(":memory:")
    card = handle_message(
        "@工程师 给 README 加上一行并开 PR",
        team=team,
        adapters={"neo": neo, "cursor": cursor},
        store=store,
    )
    assert neo.created == []
    assert len(cursor.created) == 1
    assert card.status == "FINISHED"
    assert card.pr_url.endswith("/pull/9")


def test_cloud_rejection_does_not_refresh():
    from neo_personal_bot.adapters.base import CloudRequestError

    class Rejecting:
        def __init__(self) -> None:
            self.refreshed = False

        def create(self, ticket):
            raise CloudRequestError(400, "prompt and repoUrls are required")

        def refresh(self, ref):
            self.refreshed = True
            return ref

    adapter = Rejecting()
    store = Store(":memory:")
    card = handle_message(
        "@工程师 给 README 加上一行并开 PR",
        team=exhibit_team(),
        adapters={"neo": adapter},
        store=store,
    )
    assert card.kind == "failed"
    assert card.status == "rejected"
    assert card.error == "prompt and repoUrls are required"
    assert adapter.refreshed is False


def test_waiting_for_background_work_is_not_success():
    adapter = FixtureNeoAdapter(statuses=["WAITING_FOR_BACKGROUND_WORK"])
    card, _adapter, _store = _handle("@工程师 给 README 加上一行", adapter)
    assert card.kind == "dispatch"
    assert card.status == "WAITING_FOR_BACKGROUND_WORK"
    assert card.pr_url is None
