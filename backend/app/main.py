from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, build_adapters
from app.routers import certificates, grade, health, ingest, station, transactions


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    adapters = build_adapters(settings)

    app = FastAPI(title="Panen Pay API")
    app.state.settings = settings
    app.state.store = adapters.store
    app.state.grader = adapters.grader
    app.state.brief_writer = adapters.brief_writer

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for module in (ingest, grade, transactions, certificates, station):
        app.include_router(module.router, prefix="/api/v1")
    # health is reachable both bare and under the API prefix
    app.include_router(health.router)
    app.include_router(health.router, prefix="/api/v1")
    # QR scans land on the backend origin; bounce them to the frontend page
    app.include_router(certificates.redirect_router)
    return app


app = create_app()
