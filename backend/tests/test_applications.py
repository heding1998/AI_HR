from sqlalchemy import select

from app.models import Application, Job, Resume, UploadBatch


def _demo_job_id(db_session) -> int:
    return db_session.execute(select(Job).where(Job.code == "DEMO-JOB-001")).scalar_one().id


def _seed_application(db_session, name: str, score: float, job_id: int | None = None):
    if job_id is None:
        job_id = _demo_job_id(db_session)
    batch = UploadBatch(job_id=job_id, status="done")
    db_session.add(batch)
    db_session.flush()
    resume = Resume(
        batch_id=batch.id,
        job_id=job_id,
        original_filename=f"{name}.pdf",
        file_key=f"resumes/{name}.pdf",
        extracted_text="",
        status="extracted",
        extracted_content={"name": name, "contact": "13800000000"},
        score=score,
    )
    db_session.add(resume)
    db_session.flush()
    db_session.add(
        Application(
            job_id=job_id,
            resume_id=resume.id,
            candidate_name=name,
            candidate_contact="13800000000",
            score=score,
            status="passed",
        )
    )
    db_session.commit()


def test_list_applications_requires_auth(client):
    assert client.get("/api/applications").status_code == 401


def test_list_applications_sorted_by_score_desc(client, auth_headers, db_session):
    _seed_application(db_session, "甲", 8.0)
    _seed_application(db_session, "乙", 9.5)

    resp = client.get("/api/applications", headers=auth_headers)

    assert resp.status_code == 200
    assert [a["score"] for a in resp.json()] == [9.5, 8.0]
    assert [a["candidate_name"] for a in resp.json()] == ["乙", "甲"]


def test_list_applications_filter_by_job(client, auth_headers, db_session):
    job2 = Job(code="JOB-2", name="测试岗2", location="厦门")
    db_session.add(job2)
    db_session.commit()
    db_session.refresh(job2)

    _seed_application(db_session, "甲", 8.0)
    _seed_application(db_session, "乙", 9.0, job_id=job2.id)

    demo_id = _demo_job_id(db_session)
    resp_demo = client.get(
        "/api/applications", params={"job_id": demo_id}, headers=auth_headers
    )
    assert [a["candidate_name"] for a in resp_demo.json()] == ["甲"]

    resp_job2 = client.get(
        "/api/applications", params={"job_id": job2.id}, headers=auth_headers
    )
    assert [a["candidate_name"] for a in resp_job2.json()] == ["乙"]
