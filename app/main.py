from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import Base, engine
from app.routers import applications, auth


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables on startup. A bigger project would use Alembic migrations.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=get_settings().app_name,
    version="1.0.0",
    description=(
        "Track the jobs you apply for: save applications, move them through "
        "statuses (applied → interviewing → offer), search and filter them, "
        "and see your response rate.\n\n"
        "**Try it:** register at `POST /auth/register`, then click **Authorize** "
        "and log in with your email and password."
    ),
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(applications.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
