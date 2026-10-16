from fastapi import FastAPI

from .config import settings
from .routers import (
    applications,
    auth,
    batches,
    jobs,
    resumes,
    scoring_standard,
    talent_pool,
)

app = FastAPI(title=settings.app_name)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(scoring_standard.router)
app.include_router(batches.router)
app.include_router(resumes.router)
app.include_router(applications.router)
app.include_router(talent_pool.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
