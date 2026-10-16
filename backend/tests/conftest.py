import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  注册模型到 Base.metadata
from app.config import settings
from app.db import Base
from app.deps import get_db
from app.main import app
from app.seed import ensure_default_admin, ensure_seed_jobs, ensure_seed_scoring_standard

TEST_DB_NAME = "aihr_test"


@pytest.fixture(scope="session")
def engine():
    base_url = make_url(settings.database_url)

    # 用已有库建测试库（AUTOCOMMIT 下执行 CREATE DATABASE）
    admin_url = base_url.set(database=base_url.database or "aihr")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB_NAME},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin_engine.dispose()

    test_engine = create_engine(base_url.set(database=TEST_DB_NAME), pool_pre_ping=True)
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


def _reset_and_seed(engine):
    table_names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))
    session = sessionmaker(bind=engine)()
    try:
        ensure_default_admin(session)
        ensure_seed_jobs(session)
        ensure_seed_scoring_standard(session)
    finally:
        session.close()


@pytest.fixture()
def db_session(engine):
    _reset_and_seed(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    resp = client.post(
        "/api/auth/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
