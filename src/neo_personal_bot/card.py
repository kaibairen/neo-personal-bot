"""Status card shown to the user. Cloud JSON stays behind this."""

from neo_personal_bot.tickets import NEO_WORKING, Card

_LABELS = {
    "answered": "已回复",
    "needs_approval": "待审批",
    "no_repo": "未派发",
    "rejected": "未派发",
    "missing_adapter": "未派发",
    "NOT_YET_STARTED": "排队",
    "PROVISIONING": "执行中",
    "INSTALLING": "执行中",
    "RUNNING": "执行中",
    "WAITING_FOR_BACKGROUND_WORK": "执行中",
    "CREATING": "执行中",
    "IDLE": "本轮结束",
    "FINISHED": "已完成",
    "ERROR": "失败",
    "ARCHIVED": "已归档",
    "EXPIRED": "已过期",
    "CANCELLED": "已取消",
}


def status_label(status: str) -> str:
    label = _LABELS.get(status, status)
    if status in _LABELS and status not in {"answered", "needs_approval", "no_repo", "rejected", "missing_adapter"}:
        return f"{label}（{status}）"
    return label


def still_working(status: str) -> bool:
    return status in NEO_WORKING or status in {"CREATING", "RUNNING"}


def format_card(card: Card) -> str:
    lines = [
        f"角色：{card.role_name or '—'}",
        f"状态：{status_label(card.status)}",
        f"分支：{card.branch or '—'}",
        f"PR：{card.pr_url or '—'}",
        f"错误：{card.error or '—'}",
        card.summary,
    ]
    return "\n".join(lines)
