"""Route a message, and only then call the selected cloud adapter."""

from collections.abc import Mapping

from neo_personal_bot.adapters.base import CloudRequestError
from neo_personal_bot.card import still_working
from neo_personal_bot.jobs import Store
from neo_personal_bot.router import route_message
from neo_personal_bot.tickets import Card, ExternalRef, TaskTicket, Team, is_terminal


def handle_message(
    text: str,
    *,
    team: Team,
    adapters: Mapping[str, object],
    store: Store,
    max_polls: int = 8,
) -> Card:
    decision = route_message(text, team)
    if decision.kind == "dispatch" and decision.ticket is not None:
        card = _dispatch(decision.ticket, adapters, max_polls)
    elif decision.kind == "approval":
        card = Card(
            kind="approval",
            role_name=decision.role.mention if decision.role else None,
            status="needs_approval",
            summary=decision.summary,
        )
    elif decision.kind == "no_repo":
        card = Card(
            kind="failed",
            role_name=decision.role.mention if decision.role else None,
            status="no_repo",
            summary=decision.summary,
        )
    else:
        card = Card(
            kind="reply",
            role_name=decision.role.mention if decision.role else None,
            status="answered",
            summary=decision.summary,
        )
    store.add(text, card)
    return card


def _dispatch(ticket: TaskTicket, adapters: Mapping[str, object], max_polls: int) -> Card:
    adapter = adapters.get(ticket.backend)
    if adapter is None or not hasattr(adapter, "create") or not hasattr(adapter, "refresh"):
        return Card(
            kind="failed",
            role_name=ticket.role_name,
            status="missing_adapter",
            summary=f"没有名为 {ticket.backend} 的执行适配器，没有派发。",
        )
    try:
        ref = adapter.create(ticket)
        polls = 0
        while not is_terminal(ref) and polls < max_polls:
            ref = adapter.refresh(ref)
            polls += 1
    except CloudRequestError as error:
        return Card(
            kind="failed",
            role_name=ticket.role_name,
            status="rejected",
            error=error.message,
            summary="cloud agent 没有接受这张任务票。",
        )
    return card_from_ref(ticket.role_name, ref)


def card_from_ref(role_name: str, ref: ExternalRef) -> Card:
    if ref.status == "ERROR" or ref.error:
        return Card(
            kind="failed",
            role_name=role_name,
            status=ref.status,
            branch=ref.branch,
            pr_url=ref.pr_url,
            error=ref.error or ref.status,
            summary=ref.summary or "cloud agent 这一轮失败了。",
        )
    if still_working(ref.status) or not is_terminal(ref):
        return Card(
            kind="dispatch",
            role_name=role_name,
            status=ref.status,
            branch=ref.branch,
            pr_url=ref.pr_url,
            summary="任务已派发，这一轮还没结束。",
        )
    summary = ref.summary or "cloud agent 这一轮结束了。"
    return Card(
        kind="dispatch",
        role_name=role_name,
        status=ref.status,
        branch=ref.branch,
        pr_url=ref.pr_url,
        summary=summary,
    )
