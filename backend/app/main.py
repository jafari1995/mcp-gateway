from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, mcp
from app.config import get_settings
from app.db import SessionLocal, init_db
from app.seed import ensure_admin_user


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    configured = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    allow_origins = configured + [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    seen: set[str] = set()
    origins = [o for o in allow_origins if not (o in seen or seen.add(o))]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(mcp.router)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()
        db = SessionLocal()
        try:
            ensure_admin_user(db)
        finally:
            db.close()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
