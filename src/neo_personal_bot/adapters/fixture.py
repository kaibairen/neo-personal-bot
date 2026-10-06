"""Scripted neo-cloud-agent stand-in so the exhibit runs without credentials."""

from neo_personal_bot.tickets import ExternalRef, TaskTicket


class FixtureNeoAdapter:
    """create() returns the first status. Each refresh() advances one step."""

    name = "neo"

    def __init__(
        self,
        statuses: list[str] | None = None,
        branch: str = "neo/readme-line",
        pr_url: str = "https://github.com/kaibairen/neo-personal-bot/pull/1",
        summary: str = "已在 README 加上产品一句话，并打开 PR。",
    ) -> None:
        self.statuses = list(statuses or ["RUNNING", "IDLE"])
        self.branch = branch
        self.pr_url = pr_url
        self.summary = summary
        self.created: list[TaskTicket] = []
        self._step: dict[str, int] = {}

    def create(self, ticket: TaskTicket) -> ExternalRef:
        self.created.append(ticket)
        run_id = f"run-{ticket.id[:8]}"
        self._step[run_id] = 0
        return self._at(run_id, 0)

    def refresh(self, ref: ExternalRef) -> ExternalRef:
        step = self._step.get(ref.run_id, 0) + 1
        self._step[ref.run_id] = step
        return self._at(ref.run_id, step)

    def _at(self, run_id: str, step: int) -> ExternalRef:
        index = min(step, len(self.statuses) - 1)
        status = self.statuses[index]
        done = status in {"IDLE", "ERROR", "ARCHIVED", "EXPIRED"}
        failed = status == "ERROR"
        return ExternalRef(
            backend="neo",
            run_id=run_id,
            status=status,
            branch=self.branch if done and not failed else None,
            pr_url=self.pr_url if done and not failed else None,
            summary=self.summary if done and not failed else None,
            error="fixture run failed" if failed else None,
        )
