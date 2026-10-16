from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..batch_service import load_scoring_standard, score_resume_record
from ..deps import get_current_user, get_db, get_llm
from ..llm import LLMClient
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


@router.post("/{resume_id}/rescore", response_model=ResumeDetailOut)
def rescore_resume(
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    llm: Annotated[LLMClient, Depends(get_llm)],
    _: Annotated[User, Depends(get_current_user)],
):
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在",
        )
    if not resume.extracted_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="简历内容尚未提取，无法评分",
        )
    a_rows, b_rows = load_scoring_standard(db, resume.job_id)
    score_resume_record(llm, resume, a_rows, b_rows)
    db.commit()
    return resume
