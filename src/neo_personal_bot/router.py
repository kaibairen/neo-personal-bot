"""Turn one message into a reply, an approval stop, or an internal task ticket.

This module does not open a shell, clone a repo, or call a cloud API.
"""

import re
import uuid
from dataclasses import dataclass
from typing import Literal

from neo_personal_bot.tickets import Role, TaskTicket, Team

# Phrases that leave the machine: send, pay, or destroy production state.
# A git edit that happens to contain "删除" is not in this list on purpose.
APPROVAL_MARKERS = (
    "发出去",
    "发送",
    "付款",
    "支付",
    "购买",
    "删库",
    "删除生产",
    "删除账号",
    "删除仓库",
)

_PR_PATTERN = re.compile(r"(?<![A-Za-z])PR(?![A-Za-z])|pull request|开PR", re.IGNORECASE)
_DISPATCH_PATTERN = re.compile(
    r"加上|修改|改仓库|提交改动|(?<![A-Za-z])PR(?![A-Za-z])|pull request|开PR",
    re.IGNORECASE,
)
_MENTION_PATTERN = re.compile(r"@(\S+)")


@dataclass(frozen=True)
class Route:
    kind: Literal["reply", "approval", "dispatch", "no_repo", "unknown", "help"]
    summary: str
    role: Role | None = None
    ticket: TaskTicket | None = None


def route_message(text: str, team: Team) -> Route:
    mention = _first_mention(text)
    if mention is None:
        return Route("help", _roster(team, "用 @角色 点名。"))

    role = _role_for_mention(team, mention)
    if role is None:
        return Route("unknown", _roster(team, f"没有 @{mention} 这个角色。"))

    marker = _approval_marker(text)
    if marker is not None:
        return Route(
            "approval",
            f"这条消息要{marker}，已停在审批，没有派给 cloud agent。",
            role=role,
        )

    if _DISPATCH_PATTERN.search(text):
        if not role.repo_urls:
            return Route(
                "no_repo",
                f"{role.mention}没有绑定仓库，所以没有派发。需要改代码时 @工程师。",
                role=role,
            )
        want_pr = _PR_PATTERN.search(text) is not None
        ticket = TaskTicket(
            id=uuid.uuid4().hex,
            role_id=role.id,
            role_name=role.mention,
            user_text=text.strip(),
            instruction=build_instruction(role, text, want_pr),
            repo_urls=list(role.repo_urls),
            ref=role.ref,
            want_pr=want_pr,
            backend=role.backend,
            expert_id=role.expert_id,
        )
        return Route("dispatch", "已写成任务票，准备派给 cloud agent。", role=role, ticket=ticket)

    return Route(
        "reply",
        f"{role.mention}：{role.duty} 这条消息没有要派到云端的仓库改动。",
        role=role,
    )


def build_instruction(role: Role, user_text: str, want_pr: bool) -> str:
    finish = "改完打开 PR，并在结果里给出分支和 PR 链接。" if want_pr else "给出可复查的结果。不要打开 PR。"
    repos = "、".join(role.repo_urls) if role.repo_urls else "（无）"
    return (
        f"你是{role.mention}。长期职责：{role.duty}\n"
        f"仓库：{repos}\n"
        f"这一次只做用户这句话里的任务：{user_text.strip()}\n"
        f"完成标准：{finish}\n"
        "不要对外发送、付款、购买或删除生产数据。做不到就停下来说明原因。"
    )


def _first_mention(text: str) -> str | None:
    match = _MENTION_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1)


def _role_for_mention(team: Team, mention: str) -> Role | None:
    ordered = sorted(team.roles, key=lambda role: len(role.mention), reverse=True)
    for role in ordered:
        if mention == role.mention or mention.startswith(role.mention):
            return role
    return None


def _approval_marker(text: str) -> str | None:
    for marker in APPROVAL_MARKERS:
        if marker in text:
            return marker
    return None


def _roster(team: Team, lead: str) -> str:
    names = "、".join(f"@{role.mention}" for role in team.roles)
    return f"{lead}当前团队「{team.name}」：{names}。"
