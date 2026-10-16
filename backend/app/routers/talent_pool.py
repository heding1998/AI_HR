from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import TalentPool, User
from ..schemas import TalentPoolOut

router = APIRouter(prefix="/api/talent-pool", tags=["talent-pool"])


@router.get("", response_model=list[TalentPoolOut])
def list_talent_pool(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    tier: str | None = None,
):
    query = select(TalentPool)
    if tier is not None:
        query = query.where(TalentPool.tier == tier)
    query = query.order_by(TalentPool.score.desc(), TalentPool.id)
    return db.execute(query).scalars().all()
