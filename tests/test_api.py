from fastapi.testclient import TestClient

from neo_personal_bot.adapters.fixture import FixtureNeoAdapter
from neo_personal_bot.api import create_app
from neo_personal_bot.jobs import Store


def _client() -> tuple[TestClient, FixtureNeoAdapter]:
    adapter = FixtureNeoAdapter()
    app = create_app(store=Store(":memory:"), adapters={"neo": adapter})
    return TestClient(app), adapter


def test_exhibit_page_and_engineer_story():
    client, adapter = _client()
    page = client.get("/")
    assert page.status_code == 200
    assert "neo-personal-bot" in page.text
    assert "给团队的一句话" in page.text

    response = client.post(
        "/messages",
        json={"text": "@工程师 在 neo-personal-bot 里给 README 加上一行产品一句话，并开 PR"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "IDLE"
    assert body["branch"] == "neo/readme-line"
    assert body["pr_url"].endswith("/pull/1")
    assert body["error"] is None
    assert len(adapter.created) == 1

    approval = client.post("/messages", json={"text": "@工程师 给客户发送这封邮件"})
    assert approval.json()["status"] == "needs_approval"
    assert len(adapter.created) == 1

    jobs = client.get("/jobs")
    assert jobs.status_code == 200
    assert len(jobs.json()["jobs"]) == 2


def test_team_lists_both_roles():
    client, _adapter = _client()
    payload = client.get("/team").json()
    mentions = [role["mention"] for role in payload["roles"]]
    assert mentions == ["研究员", "工程师"]
