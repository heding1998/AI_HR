from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import Job, User
from .security import hash_password

EXAMPLE_JOB_CODE = "DEMO-JOB-001"


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
    existing = db.execute(
        select(Job).where(Job.code == EXAMPLE_JOB_CODE)
    ).scalar_one_or_none()
    if existing is None:
        db.add(Job(code=EXAMPLE_JOB_CODE, name="Java 开发工程师", location="厦门"))
        db.commit()


def main() -> None:
    from .db import SessionLocal

    db = SessionLocal()
    try:
        ensure_default_admin(db)
        ensure_seed_jobs(db)
        print("种子数据已就绪")
    finally:
        db.close()


if __name__ == "__main__":
    main()
