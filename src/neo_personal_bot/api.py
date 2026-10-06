"""Small exhibit server. The default adapter never calls a real cloud."""

import os
from collections.abc import Mapping
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from neo_personal_bot.adapters.cursor import CursorCloudAdapter
from neo_personal_bot.adapters.fixture import FixtureNeoAdapter
from neo_personal_bot.adapters.neo import NeoCloudAdapter
from neo_personal_bot.card import status_label
from neo_personal_bot.jobs import Store
from neo_personal_bot.roles import exhibit_team
from neo_personal_bot.service import handle_message
from neo_personal_bot.tickets import Card, Team

_PAGE = Path(__file__).with_name("exhibit.html").read_text(encoding="utf-8")


class MessageIn(BaseModel):
    text: str


def adapters_from_env() -> dict[str, object]:
    backend = os.environ.get("NEO_PERSONAL_BOT_BACKEND", "fixture")
    adapters: dict[str, object] = {}
    if backend == "neo":
        adapters["neo"] = NeoCloudAdapter(
            os.environ["NEO_CLOUD_BASE_URL"],
            os.environ["NEO_CLOUD_TOKEN"],
        )
    else:
        adapters["neo"] = FixtureNeoAdapter()
    cursor_key = os.environ.get("CURSOR_API_KEY")
    if cursor_key:
        adapters["cursor"] = CursorCloudAdapter(
            cursor_key,
            base_url=os.environ.get("CURSOR_API_BASE", "https://api.cursor.com"),
        )
    return adapters


def create_app(
    store: Store | None = None,
    adapters: Mapping[str, object] | None = None,
    team: Team | None = None,
) -> FastAPI:
    app = FastAPI(title="neo-personal-bot", version="0.1.0")
    app.state.store = store or Store(os.environ.get("NEO_PERSONAL_BOT_DB", "data/exhibit.db"))
    app.state.adapters = dict(adapters) if adapters is not None else adapters_from_env()
    app.state.team = team or exhibit_team()

    @app.get("/", response_class=HTMLResponse)
    def exhibit() -> str:
        return _PAGE

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/team")
    def team_view() -> dict[str, object]:
        current: Team = app.state.team
        return {
            "id": current.id,
            "name": current.name,
            "roles": [
                {
                    "mention": role.mention,
                    "duty": role.duty,
                    "repo_urls": role.repo_urls,
                    "backend": role.backend,
                }
                for role in current.roles
            ],
        }

    @app.post("/messages")
    def messages(body: MessageIn) -> dict[str, object]:
        card = handle_message(
            body.text,
            team=app.state.team,
            adapters=app.state.adapters,
            store=app.state.store,
        )
        return card_payload(card)

    @app.get("/jobs")
    def jobs() -> dict[str, object]:
        return {"jobs": app.state.store.list_jobs()}

    return app


def card_payload(card: Card) -> dict[str, object]:
    payload = card.model_dump()
    payload["status_label"] = status_label(card.status)
    return payload


app = create_app()
