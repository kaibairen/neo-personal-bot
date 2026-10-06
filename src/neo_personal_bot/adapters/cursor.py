"""Client for Cursor Cloud Agents API v1.

The run status is the source of truth. An IDLE agent can still have an ERROR run.
Follow-up would be a new run; this client only creates and reads the first run.
"""

import httpx

from neo_personal_bot.adapters.base import CloudRequestError
from neo_personal_bot.tickets import ExternalRef, TaskTicket


class CursorCloudAdapter:
    name = "cursor"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.cursor.com",
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = client or httpx.Client(timeout=30.0)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def create(self, ticket: TaskTicket) -> ExternalRef:
        response = self._client.post(
            f"{self.base_url}/v1/agents",
            auth=(self.api_key, ""),
            json=cursor_create_body(ticket),
        )
        body = _json_or_empty(response)
        if response.status_code not in {200, 201}:
            raise CloudRequestError(response.status_code, _error_message(body, response.status_code))
        return ref_from_cursor_create(body)

    def refresh(self, ref: ExternalRef) -> ExternalRef:
        if not ref.agent_id:
            raise CloudRequestError(400, "Cursor 任务缺少 agent id")
        response = self._client.get(
            f"{self.base_url}/v1/agents/{ref.agent_id}/runs/{ref.run_id}",
            auth=(self.api_key, ""),
        )
        body = _json_or_empty(response)
        if response.status_code != 200:
            raise CloudRequestError(response.status_code, _error_message(body, response.status_code))
        return ref_from_cursor_run(ref.agent_id, body)

    def close_quietly(self) -> None:
        self.close()


def cursor_create_body(ticket: TaskTicket) -> dict[str, object]:
    repos: list[dict[str, str]] = []
    for url in ticket.repo_urls:
        entry = {"url": url}
        if ticket.ref:
            entry["startingRef"] = ticket.ref
        repos.append(entry)
    return {
        "prompt": {"text": ticket.instruction},
        "repos": repos,
        "autoCreatePR": ticket.want_pr,
    }


def ref_from_cursor_create(payload: dict[str, object]) -> ExternalRef:
    agent = payload.get("agent")
    run = payload.get("run")
    if not isinstance(agent, dict) or not isinstance(run, dict):
        raise CloudRequestError(502, "Cursor 的响应缺少 agent 或 run")
    agent_id = agent.get("id")
    run_id = run.get("id")
    status = run.get("status")
    if not isinstance(agent_id, str) or not isinstance(run_id, str) or not isinstance(status, str):
        raise CloudRequestError(502, "Cursor 的响应缺少 agent.id、run.id 或 run.status")
    return ExternalRef(backend="cursor", agent_id=agent_id, run_id=run_id, status=status)


def ref_from_cursor_run(agent_id: str, run: dict[str, object]) -> ExternalRef:
    run_id = run.get("id")
    status = run.get("status")
    if not isinstance(run_id, str) or not isinstance(status, str):
        raise CloudRequestError(502, "Cursor run 缺少 id 或 status")
    branch, pr_url = _first_branch(run.get("git"))
    result = run.get("result") if isinstance(run.get("result"), str) else None
    summary = result
    error = None
    if status in {"ERROR", "CANCELLED", "EXPIRED"}:
        error = result or status
        summary = None
    return ExternalRef(
        backend="cursor",
        agent_id=agent_id,
        run_id=run_id,
        status=status,
        branch=branch,
        pr_url=pr_url,
        summary=summary,
        error=error,
    )


def _first_branch(git: object) -> tuple[str | None, str | None]:
    if not isinstance(git, dict):
        return None, None
    branches = git.get("branches")
    if not isinstance(branches, list) or not branches or not isinstance(branches[0], dict):
        return None, None
    first = branches[0]
    branch = first.get("branch") if isinstance(first.get("branch"), str) else None
    pr_url = first.get("prUrl") if isinstance(first.get("prUrl"), str) else None
    return branch, pr_url


def _json_or_empty(response: httpx.Response) -> dict[str, object]:
    try:
        body = response.json()
    except ValueError:
        return {}
    if isinstance(body, dict):
        return body
    return {}


def _error_message(body: dict[str, object], status_code: int) -> str:
    error = body.get("error")
    if isinstance(error, str) and error:
        return error
    message = body.get("message")
    if isinstance(message, str) and message:
        return message
    return f"Cursor Cloud Agent 返回 HTTP {status_code}"
