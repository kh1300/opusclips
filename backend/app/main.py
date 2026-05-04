from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import clips, health, jobs, videos
from app.core.config import settings
from app.db.session import Base, engine
from app import models  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)

    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(videos.router, prefix=settings.api_v1_prefix)
    app.include_router(jobs.router, prefix=settings.api_v1_prefix)
    app.include_router(clips.router, prefix=settings.api_v1_prefix)
    return app


app = create_app()

