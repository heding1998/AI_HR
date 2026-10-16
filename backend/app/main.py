from fastapi import FastAPI

from .config import settings
from .routers import auth, batches, jobs, scoring_standard

app = FastAPI(title=settings.app_name)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(scoring_standard.router)
app.include_router(batches.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
