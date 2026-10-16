from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import Job, ScoringStandardA, ScoringStandardB, User
from .security import hash_password

EXAMPLE_JOB_CODE = "DEMO-JOB-001"

EXAMPLE_A_TABLE = [
    {"category": "学历", "subcategory": "学历", "category_score": 2, "subcategory_score": 2},
    {
        "category": "工作经验",
        "subcategory": "工作经验",
        "category_score": 3,
        "subcategory_score": 3,
    },
    {
        "category": "项目经验",
        "subcategory": "项目经验",
        "category_score": 3,
        "subcategory_score": 3,
    },
    {
        "category": "个人技能",
        "subcategory": "个人技能",
        "category_score": 2,
        "subcategory_score": 2,
    },
]

EXAMPLE_B_TABLE = [
    {
        "category": "学历",
        "subcategory": "学历",
        "level1_indicator": "最高学历",
        "level2_indicator": "硕士及以上",
        "weight": 10,
    },
    {
        "category": "学历",
        "subcategory": "学历",
        "level1_indicator": "最高学历",
        "level2_indicator": "本科",
        "weight": 8,
    },
    {
        "category": "学历",
        "subcategory": "学历",
        "level1_indicator": "最高学历",
        "level2_indicator": "大专及以下",
        "weight": 4,
    },
    {
        "category": "工作经验",
        "subcategory": "工作经验",
        "level1_indicator": "工作年限",
        "level2_indicator": "8 年以上",
        "weight": 10,
    },
    {
        "category": "工作经验",
        "subcategory": "工作经验",
        "level1_indicator": "工作年限",
        "level2_indicator": "5~8 年",
        "weight": 8,
    },
    {
        "category": "工作经验",
        "subcategory": "工作经验",
        "level1_indicator": "工作年限",
        "level2_indicator": "3~5 年",
        "weight": 6,
    },
    {
        "category": "工作经验",
        "subcategory": "工作经验",
        "level1_indicator": "工作年限",
        "level2_indicator": "3 年以下",
        "weight": 3,
    },
    {
        "category": "项目经验",
        "subcategory": "项目经验",
        "level1_indicator": "项目经验",
        "level2_indicator": "有大型项目经验",
        "weight": 10,
    },
    {
        "category": "项目经验",
        "subcategory": "项目经验",
        "level1_indicator": "项目经验",
        "level2_indicator": "有一般项目经验",
        "weight": 7,
    },
    {
        "category": "个人技能",
        "subcategory": "个人技能",
        "level1_indicator": "技能",
        "level2_indicator": "精通 Java 技术栈",
        "weight": 10,
    },
    {
        "category": "个人技能",
        "subcategory": "个人技能",
        "level1_indicator": "技能",
        "level2_indicator": "熟悉 Java 技术栈",
        "weight": 8,
    },
]


def ensure_default_admin(db: Session) -> User:
    user = db.execute(
        select(User).where(User.username == settings.admin_username)
    ).scalar_one_or_none()
    if user is None:
        user = User(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def ensure_seed_jobs(db: Session) -> None:
    existing = db.execute(select(Job).where(Job.code == EXAMPLE_JOB_CODE)).scalar_one_or_none()
    if existing is None:
        db.add(Job(code=EXAMPLE_JOB_CODE, name="Java 开发工程师", location="厦门"))
        db.commit()


def ensure_seed_scoring_standard(db: Session) -> None:
    job = db.execute(select(Job).where(Job.code == EXAMPLE_JOB_CODE)).scalar_one_or_none()
    if job is None:
        return
    has_a = (
        db.execute(select(ScoringStandardA).where(ScoringStandardA.job_id == job.id)).first()
        is not None
    )
    if not has_a:
        db.add_all([ScoringStandardA(job_id=job.id, **row) for row in EXAMPLE_A_TABLE])
    has_b = (
        db.execute(select(ScoringStandardB).where(ScoringStandardB.job_id == job.id)).first()
        is not None
    )
    if not has_b:
        db.add_all([ScoringStandardB(job_id=job.id, **row) for row in EXAMPLE_B_TABLE])
    db.commit()


def main() -> None:
    from .db import SessionLocal

    db = SessionLocal()
    try:
        ensure_default_admin(db)
        ensure_seed_jobs(db)
        ensure_seed_scoring_standard(db)
        print("种子数据已就绪")
    finally:
        db.close()


if __name__ == "__main__":
    main()
