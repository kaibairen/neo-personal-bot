"""Internal task ticket. Neo and Cursor request bodies stay in their adapters."""

from typing import Literal

from pydantic import BaseModel, Field

BackendName = Literal["neo", "cursor"]

NEO_TERMINAL = frozenset({"IDLE", "ERROR", "ARCHIVED", "EXPIRED"})
CURSOR_TERMINAL = frozenset({"FINISHED", "ERROR", "CANCELLED", "EXPIRED"})
NEO_WORKING = frozenset(
    {
        "NOT_YET_STARTED",
        "PROVISIONING",
        "INSTALLING",
        "RUNNING",
        "WAITING_FOR_BACKGROUND_WORK",
    }
)


class Role(BaseModel):
    id: str
    mention: str
    duty: str
    repo_urls: list[str] = Field(default_factory=list)
    ref: str | None = None
    backend: BackendName = "neo"
    expert_id: str | None = None


class Team(BaseModel):
    id: str
    name: str
    roles: list[Role]


class TaskTicket(BaseModel):
    id: str
    role_id: str
    role_name: str
    user_text: str
    instruction: str
    repo_urls: list[str]
    ref: str | None = None
    want_pr: bool = False
    backend: BackendName = "neo"
    expert_id: str | None = None


class ExternalRef(BaseModel):
    backend: BackendName
    run_id: str
    status: str
    agent_id: str | None = None
    branch: str | None = None
    pr_url: str | None = None
    summary: str | None = None
    error: str | None = None


class Card(BaseModel):
    kind: Literal["reply", "approval", "dispatch", "failed"]
    role_name: str | None = None
    status: str
    branch: str | None = None
    pr_url: str | None = None
    error: str | None = None
    summary: str


def is_terminal(ref: ExternalRef) -> bool:
    if ref.backend == "neo":
        return ref.status in NEO_TERMINAL
    return ref.status in CURSOR_TERMINAL
