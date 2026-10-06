"""The exhibit team: two named roles, not a general helper."""

from neo_personal_bot.tickets import Role, Team

EXHIBIT_REPO = "https://github.com/kaibairen/neo-personal-bot"


def exhibit_team() -> Team:
    return Team(
        id="studio",
        name="我的工作室",
        roles=[
            Role(
                id="researcher",
                mention="研究员",
                duty=(
                    "把问题查清。回答分成事实、推断和未核实。"
                    "不改仓库，不对外发送。需要改代码时交给工程师。"
                ),
                repo_urls=[],
            ),
            Role(
                id="engineer",
                mention="工程师",
                duty=(
                    "只负责绑定仓库里的改动和 PR。"
                    "不对外发送，不付款，不删除生产数据。"
                    "做完要留下可复查的分支和 PR。"
                ),
                repo_urls=[EXHIBIT_REPO],
                ref="main",
                backend="neo",
            ),
        ],
    )
