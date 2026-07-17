"""Adapter selection happens once, here (§E). Routers only ever see the
interfaces exposed on app.state — never which implementation is behind them.
"""

from dataclasses import dataclass

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.services.brief_writer import make_brief_writer
from app.services.vision_grader import make_grader
from app.store import InMemoryStore, Store

class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    FIREBASE_SERVICE_ACCOUNT_JSON: str | None = None
    PANEN_BASE_URL: str = "http://localhost:8000"
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

@dataclass
class Adapters:
    store: Store
    grader: object
    brief_writer: object

def build_adapters(settings: Settings) -> Adapters:
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        from app.store import FirestoreStore

        store: Store = FirestoreStore(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
    else:
        store = InMemoryStore()
    return Adapters(
        store=store,
        grader=make_grader(settings.OPENAI_API_KEY),
        brief_writer=make_brief_writer(settings.OPENAI_API_KEY),
    )
