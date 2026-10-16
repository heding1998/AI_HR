from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Job, ScoringStandardA, ScoringStandardB, User
from ..schemas import (
    ScoringStandardAIn,
    ScoringStandardAOut,
    ScoringStandardBIn,
    ScoringStandardBOut,
    ScoringStandardOut,
)
from ..scoring import validate_a_table, validate_b_table

router = APIRouter(prefix="/api/jobs/{job_id}/scoring-standard", tags=["scoring-standard"])


def _get_job_or_404(db: Session, job_id: int) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="岗位不存在",
        )
    return job


@router.get("", response_model=ScoringStandardOut)
def get_standard(
    job_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    _get_job_or_404(db, job_id)
    a = db.execute(
        select(ScoringStandardA)
        .where(ScoringStandardA.job_id == job_id)
        .order_by(ScoringStandardA.id)
    ).scalars().all()
    b = db.execute(
        select(ScoringStandardB)
        .where(ScoringStandardB.job_id == job_id)
        .order_by(ScoringStandardB.id)
    ).scalars().all()
    return {"a": a, "b": b}


@router.put("/a", response_model=list[ScoringStandardAOut])
def put_a_table(
    job_id: int,
    body: list[ScoringStandardAIn],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    _get_job_or_404(db, job_id)
    error = validate_a_table(body)
    if error is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    db.execute(delete(ScoringStandardA).where(ScoringStandardA.job_id == job_id))
    db.add_all([ScoringStandardA(job_id=job_id, **row.model_dump()) for row in body])
    db.commit()
    return db.execute(
        select(ScoringStandardA)
        .where(ScoringStandardA.job_id == job_id)
        .order_by(ScoringStandardA.id)
    ).scalars().all()


@router.put("/b", response_model=list[ScoringStandardBOut])
def put_b_table(
    job_id: int,
    body: list[ScoringStandardBIn],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    _get_job_or_404(db, job_id)
    error = validate_b_table(body)
    if error is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    db.execute(delete(ScoringStandardB).where(ScoringStandardB.job_id == job_id))
    db.add_all([ScoringStandardB(job_id=job_id, **row.model_dump()) for row in body])
    db.commit()
    return db.execute(
        select(ScoringStandardB)
        .where(ScoringStandardB.job_id == job_id)
        .order_by(ScoringStandardB.id)
    ).scalars().all()
