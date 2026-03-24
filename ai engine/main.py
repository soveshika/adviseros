from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import assets, clients, investments, recommendations, reports, analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (use Alembic in production instead)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Financial advisory AI platform — REST API",
    lifespan=lifespan,
)

# Register routers
app.include_router(clients.router,         prefix="/api/v1")
app.include_router(assets.router,          prefix="/api/v1")
app.include_router(investments.router,     prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(reports.router,         prefix="/api/v1")
app.include_router(analysis.router,        prefix="/api/v1")   # ← AI engine


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
