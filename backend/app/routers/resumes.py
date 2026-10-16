from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Resume, User
from ..schemas import ResumeDetailOut

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.get("/{resume_id}", response_model=ResumeDetailOut)
def get_resume(
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在",
        )
    return resume
