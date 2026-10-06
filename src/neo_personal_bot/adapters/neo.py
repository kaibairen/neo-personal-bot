"""Client for Neo2Agent neo-cloud-agent: POST /v1/runs, GET /v1/runs/{id}.

Request fields match CreateRunRequest. Cursor fields are not sent.
"""

import httpx

from neo_personal_bot.adapters.base import CloudRequestError
from neo_personal_bot.tickets import ExternalRef, TaskTicket


class NeoCloudAdapter:
    name = "neo"

    def __init__(
        self,
        base_url: str,
        token: str,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._client = client or httpx.Client(timeout=30.0)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def create(self, ticket: TaskTicket) -> ExternalRef:
        payload = neo_create_body(ticket)
        response = self._client.post(
            f"{self.base_url}/v1/runs",
            headers=self._headers(),
            json=payload,
        )
        body = _json_or_empty(response)
        if response.status_code != 201:
            raise CloudRequestError(response.status_code, _error_message(body, response.status_code))
        return ref_from_neo_run(body)

    def refresh(self, ref: ExternalRef) -> ExternalRef:
        response = self._client.get(
            f"{self.base_url}/v1/runs/{ref.run_id}",
            headers=self._headers(),
        )
        body = _json_or_empty(response)
        if response.status_code != 200:
            raise CloudRequestError(response.status_code, _error_message(body, response.status_code))
        return ref_from_neo_run(body)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }


def neo_create_body(ticket: TaskTicket) -> dict[str, object]:
    body: dict[str, object] = {
        "prompt": ticket.instruction,
        "repoUrls": list(ticket.repo_urls),
        "source": "api",
        "mode": "agent",
    }
    if ticket.ref:
        body["ref"] = ticket.ref
    if ticket.expert_id:
        body["expertId"] = ticket.expert_id
    return body


def ref_from_neo_run(run: dict[str, object]) -> ExternalRef:
    pull_requests = run.get("pullRequests")
    pr_url = None
    if isinstance(pull_requests, list) and pull_requests:
        first = pull_requests[0]
        if isinstance(first, dict) and isinstance(first.get("url"), str):
            pr_url = first["url"]
    run_id = run.get("id")
    status = run.get("status")
    if not isinstance(run_id, str) or not isinstance(status, str):
        raise CloudRequestError(502, "neo cloud agent 的响应缺少 id 或 status")
    branch = run.get("branchName")
    error = run.get("errorMessage")
    return ExternalRef(
        backend="neo",
        run_id=run_id,
        status=status,
        branch=branch if isinstance(branch, str) else None,
        pr_url=pr_url,
        error=error if isinstance(error, str) else None,
    )


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
    return f"neo cloud agent 返回 HTTP {status_code}"
