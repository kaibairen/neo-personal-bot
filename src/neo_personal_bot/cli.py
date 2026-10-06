"""Exhibit the two stories on stdout. Uses the fixture cloud agent."""

from neo_personal_bot.adapters.fixture import FixtureNeoAdapter
from neo_personal_bot.card import format_card
from neo_personal_bot.jobs import Store
from neo_personal_bot.roles import exhibit_team
from neo_personal_bot.service import handle_message

STORIES = (
    "@工程师 在 neo-personal-bot 里给 README 加上一行产品一句话，并开 PR",
    "@工程师 给客户发送这封邮件",
    "@研究员 我们团队有哪些人",
)


def main() -> int:
    team = exhibit_team()
    adapter = FixtureNeoAdapter()
    store = Store(":memory:")
    adapters = {"neo": adapter}
    for text in STORIES:
        card = handle_message(text, team=team, adapters=adapters, store=store)
        print(f"用户：{text}")
        print(format_card(card))
        print()
    print(f"派发次数：{len(adapter.created)}")
    return 0
