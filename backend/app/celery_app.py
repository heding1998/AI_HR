"""Celery 应用与异步任务。"""

from celery import Celery

from .config import settings

celery_app = Celery(
    "aihr",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
)


@celery_app.task(name="process_batch")
def process_batch_task(batch_id: int) -> None:
    from .batch_service import process_batch
    from .db import SessionLocal
    from .deps import get_storage

    session = SessionLocal()
    try:
        process_batch(session, get_storage(), batch_id)
    finally:
        session.close()
