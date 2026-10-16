from fastapi import FastAPI

from .config import settings
from .routers import auth

app = FastAPI(title=settings.app_name)

app.include_router(auth.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
