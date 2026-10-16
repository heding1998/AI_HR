from sqlalchemy import select

from app.models import Application, Job, Resume, TalentPool, UploadBatch
from app.recruitment import record_application_and_pool


def _demo_job_id(db_session) -> int:
    return db_session.execute(select(Job).where(Job.code == "DEMO-JOB-001")).scalar_one().id


def test_list_talent_pool_requires_auth(client):
    assert client.get("/api/talent-pool").status_code == 401


def test_list_talent_pool_filter_by_tier(client, auth_headers, db_session):
    db_session.add_all(
        [
            TalentPool(name="甲", contact="p1", score=9.5, tier="特别优秀"),
            TalentPool(name="乙", contact="p2", score=8.5, tier="中等优秀"),
            TalentPool(name="丙", contact="p3", score=7.5, tier="一般优秀"),
        ]
    )
    db_session.commit()

    resp = client.get("/api/talent-pool", params={"tier": "特别优秀"}, headers=auth_headers)
    assert [p["name"] for p in resp.json()] == ["甲"]

    resp_all = client.get("/api/talent-pool", headers=auth_headers)
    assert [p["name"] for p in resp_all.json()] == ["甲", "乙", "丙"]


def test_record_application_and_pool_keeps_highest_score(db_session):
    job_id = _demo_job_id(db_session)
    batch = UploadBatch(job_id=job_id, status="done")
    db_session.add(batch)
    db_session.flush()

    def make_resume(score: float) -> Resume:
        resume = Resume(
            batch_id=batch.id,
            job_id=job_id,
            original_filename="r.pdf",
            file_key="resumes/r.pdf",
            extracted_text="",
            status="extracted",
            extracted_content={"name": "张三", "contact": "13800000000"},
            score=score,
        )
        db_session.add(resume)
        db_session.flush()
        return resume

    record_application_and_pool(db_session, make_resume(8.0))
    db_session.commit()
    high = make_resume(9.5)
    record_application_and_pool(db_session, high)
    db_session.commit()
    record_application_and_pool(db_session, make_resume(8.2))
    db_session.commit()

    pool = db_session.execute(select(TalentPool)).scalars().all()
    assert len(pool) == 1
    assert pool[0].score == 9.5
    assert pool[0].tier == "特别优秀"
    assert pool[0].resume_id == high.id


def test_record_application_and_pool_skips_missing_contact(db_session):
    job_id = _demo_job_id(db_session)
    batch = UploadBatch(job_id=job_id, status="done")
    db_session.add(batch)
    db_session.flush()
    resume = Resume(
        batch_id=batch.id,
        job_id=job_id,
        original_filename="r.pdf",
        file_key="resumes/r.pdf",
        extracted_text="",
        status="extracted",
        extracted_content={"name": "张三", "contact": None},
        score=9.0,
    )
    db_session.add(resume)
    db_session.flush()

    record_application_and_pool(db_session, resume)
    db_session.commit()

    assert len(db_session.execute(select(Application)).scalars().all()) == 1
    assert db_session.execute(select(TalentPool)).scalars().all() == []
