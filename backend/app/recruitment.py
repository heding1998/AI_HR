"""评分结果落地：生成应聘记录，并把达标候选人写入高分人才库（按人去重、保留最高分）。"""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .models import Application, Resume, TalentPool
from .scoring import is_pass, tier_for_score

APPLICATION_PASSED = "passed"
APPLICATION_FAILED = "failed"


def _upsert_talent_pool(
    session: Session, name: str, contact: str, score: float, resume_id: int
) -> None:
    """按姓名 + 联系方式原子去重，仅在分数更高时更新（保留最高分）。"""
    stmt = pg_insert(TalentPool).values(
        name=name,
        contact=contact,
        score=score,
        tier=tier_for_score(score),
        resume_id=resume_id,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[TalentPool.name, TalentPool.contact],
        set_={
            "score": stmt.excluded.score,
            "tier": stmt.excluded.tier,
            "resume_id": stmt.excluded.resume_id,
        },
        where=stmt.excluded.score > TalentPool.score,
    )
    session.execute(stmt)


def record_application_and_pool(session: Session, resume: Resume) -> None:
    """为一份已评分的简历生成应聘记录；达标且可识别身份时同步写入人才库。"""
    score = resume.score
    if score is None:
        return

    content = resume.extracted_content or {}
    name = str(content.get("name") or "").strip()
    contact = str(content.get("contact") or "").strip()

    # 幂等：同一份简历只生成一条应聘记录。
    already = session.execute(
        select(Application.id).where(Application.resume_id == resume.id)
    ).scalar_one_or_none()
    if already is None:
        session.add(
            Application(
                job_id=resume.job_id,
                resume_id=resume.id,
                candidate_name=name,
                candidate_contact=contact,
                score=score,
                status=APPLICATION_PASSED if is_pass(score) else APPLICATION_FAILED,
            )
        )

    # 姓名与联系方式齐全才去重入库，避免缺失联系方式的不同人被误合并。
    if is_pass(score) and name and contact:
        _upsert_talent_pool(session, name, contact, score, resume.id)
