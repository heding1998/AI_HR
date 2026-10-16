from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Application, User
from ..schemas import ApplicationOut

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    job_id: int | None = None,
):
    query = select(Application)
    if job_id is not None:
        query = query.where(Application.job_id == job_id)
    query = query.order_by(Application.score.desc(), Application.id)
    return db.execute(query).scalars().all()
