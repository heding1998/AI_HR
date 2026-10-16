from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import User
from .security import hash_password


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


def main() -> None:
    from .db import SessionLocal

    db = SessionLocal()
    try:
        ensure_default_admin(db)
        print(f"默认管理员 {settings.admin_username} 已就绪")
    finally:
        db.close()


if __name__ == "__main__":
    main()
