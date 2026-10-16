from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..batch_service import STATUS_FAILED
from ..celery_app import process_batch_task
from ..deps import get_current_user, get_db, get_storage
from ..models import Job, Resume, UploadBatch, User
from ..schemas import BatchDetailOut, BatchOut, ResumeOut
from ..storage import ObjectStorage

router = APIRouter(prefix="/api/batches", tags=["batches"])

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 上传 ZIP 最大 100MB


@router.post("", response_model=BatchOut, status_code=status.HTTP_201_CREATED)
def upload_batch(
    job_id: Annotated[int, Form()],
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[ObjectStorage, Depends(get_storage)],
    _: Annotated[User, Depends(get_current_user)],
):
    if db.get(Job, job_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="岗位不存在",
        )

    data = file.file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="上传文件过大",
        )
    if not data.startswith(b"PK"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不是有效的 ZIP 文件",
        )

    batch = UploadBatch(job_id=job_id, status="pending")
    db.add(batch)
    db.commit()
    db.refresh(batch)

    try:
        storage.put(f"uploads/{batch.id}.zip", data)
        process_batch_task.delay(batch.id)
    except Exception as exc:
        batch.status = STATUS_FAILED
        batch.error = f"上传处理失败：{str(exc)[:200]}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="上传处理失败，请稍后重试",
        )

    return batch


@router.get("", response_model=list[BatchOut])
def list_batches(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    return db.execute(select(UploadBatch).order_by(UploadBatch.id.desc())).scalars().all()


@router.get("/{batch_id}", response_model=BatchDetailOut)
def get_batch(
    batch_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    batch = db.get(UploadBatch, batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批次不存在",
        )
    resumes = db.execute(
        select(Resume).where(Resume.batch_id == batch_id).order_by(Resume.id)
    ).scalars().all()
    return {
        "id": batch.id,
        "job_id": batch.job_id,
        "status": batch.status,
        "total_count": batch.total_count,
        "processed_count": batch.processed_count,
        "error": batch.error,
        "created_at": batch.created_at,
        "resumes": resumes,
    }


@router.get("/{batch_id}/resumes", response_model=list[ResumeOut])
def list_batch_resumes(
    batch_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    if db.get(UploadBatch, batch_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批次不存在",
        )
    return db.execute(
        select(Resume).where(Resume.batch_id == batch_id).order_by(Resume.id)
    ).scalars().all()
