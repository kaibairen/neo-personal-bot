import json

import httpx

from neo_personal_bot.adapters.cursor import (
    CursorCloudAdapter,
    cursor_create_body,
    ref_from_cursor_run,
)
from neo_personal_bot.adapters.neo import NeoCloudAdapter, neo_create_body
from neo_personal_bot.router import route_message
from neo_personal_bot.roles import exhibit_team
from neo_personal_bot.tickets import ExternalRef


def _ticket():
    route = route_message(
        "@工程师 在 neo-personal-bot 里给 README 加上一行产品一句话，并开 PR",
        exhibit_team(),
    )
    assert route.ticket is not None
    return route.ticket


def test_neo_body_is_not_a_cursor_request():
    body = neo_create_body(_ticket())
    assert set(body) == {"prompt", "repoUrls", "source", "mode", "ref"}
    assert body["source"] == "api"
    assert body["mode"] == "agent"
    assert isinstance(body["prompt"], str)
    assert "text" not in body["prompt"]


def test_cursor_body_is_not_a_neo_request():
    body = cursor_create_body(_ticket())
    assert set(body) == {"prompt", "repos", "autoCreatePR"}
    assert body["prompt"] == {"text": _ticket().instruction}
    assert body["repos"][0]["startingRef"] == "main"
    assert "repoUrls" not in body
    assert "expertId" not in body


def test_neo_create_and_refresh_use_run_routes():
    seen: list[tuple[str, str, dict | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer token"
        payload = json.loads(request.content) if request.content else None
        seen.append((request.method, request.url.path, payload))
        if request.method == "POST":
            return httpx.Response(
                201,
                json={
                    "id": "run-1",
                    "status": "RUNNING",
                    "branchName": None,
                    "pullRequests": [],
                    "errorMessage": None,
                },
            )
        return httpx.Response(
            200,
            json={
                "id": "run-1",
                "status": "IDLE",
                "branchName": "neo/readme-line",
                "pullRequests": [
                    {
                        "repoUrl": "https://github.com/kaibairen/neo-personal-bot",
                        "branch": "neo/readme-line",
                        "url": "https://github.com/kaibairen/neo-personal-bot/pull/1",
                        "draft": False,
                        "number": 1,
                        "title": "readme",
                    }
                ],
                "errorMessage": None,
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = NeoCloudAdapter("https://cloud.example", "token", client=client)
    ref = adapter.create(_ticket())
    assert ref.status == "RUNNING"
    finished = adapter.refresh(ref)
    assert finished.status == "IDLE"
    assert finished.pr_url.endswith("/pull/1")
    assert seen[0][0] == "POST"
    assert seen[0][1] == "/v1/runs"
    assert seen[0][2]["repoUrls"]
    assert seen[1] == ("GET", "/v1/runs/run-1", None)


def test_neo_rejects_missing_prompt_without_refresh():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "prompt is required"})

    adapter = NeoCloudAdapter(
        "https://cloud.example",
        "token",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    from neo_personal_bot.adapters.base import CloudRequestError

    try:
        adapter.create(_ticket())
    except CloudRequestError as error:
        assert error.status_code == 400
        assert error.message == "prompt is required"
    else:
        raise AssertionError("expected CloudRequestError")


def test_cursor_error_run_is_not_hidden_by_idle_agent():
    ref = ref_from_cursor_run(
        "bc-1",
        {
            "id": "run-1",
            "status": "ERROR",
            "result": "tests failed",
            "git": {"branches": []},
        },
    )
    assert ref.status == "ERROR"
    assert ref.error == "tests failed"
    assert ref.summary is None


def test_cursor_create_reads_run_status_not_agent_status():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/agents"
        assert request.headers["authorization"].startswith("Basic ")
        return httpx.Response(
            200,
            json={
                "agent": {"id": "bc-1", "status": "IDLE"},
                "run": {"id": "run-1", "status": "CREATING"},
            },
        )

    adapter = CursorCloudAdapter(
        "key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    ref = adapter.create(_ticket())
    assert ref.agent_id == "bc-1"
    assert ref.status == "CREATING"


def test_external_ref_roundtrip_keeps_backends_apart():
    neo = ExternalRef(backend="neo", run_id="run-1", status="IDLE")
    cursor = ExternalRef(backend="cursor", run_id="run-1", agent_id="bc-1", status="FINISHED")
    assert neo.model_dump().keys() != {"prompt", "repoUrls"}
    assert "agent_id" in cursor.model_dump()
    assert neo.backend != cursor.backend
