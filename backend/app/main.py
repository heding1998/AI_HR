from fastapi import FastAPI

from .config import settings
from .routers import auth, jobs

app = FastAPI(title=settings.app_name)

app.include_router(auth.router)
app.include_router(jobs.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
