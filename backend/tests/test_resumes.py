from app.batch_service import process_batch
from app.routers import batches
from tests.fakes import FakeLLMClient, make_pdf, make_zip


class _SyncTask:
    """在测试中同步执行批次处理的假 Celery 任务。"""

    def __init__(self, fn):
        self._fn = fn

    def delay(self, batch_id: int) -> None:
        self._fn(batch_id)


def _demo_job_id(client, auth_headers) -> int:
    jobs = client.get("/api/jobs", headers=auth_headers).json()
    return next(j["id"] for j in jobs if j["code"] == "DEMO-JOB-001")


def _upload(client, auth_headers, job_id: int, zip_bytes: bytes):
    return client.post(
        "/api/batches",
        data={"job_id": str(job_id)},
        files={"file": ("resumes.zip", zip_bytes, "application/zip")},
        headers=auth_headers,
    )


def test_get_resume_detail(client, auth_headers, db_session, storage, monkeypatch):
    monkeypatch.setattr(
        batches,
        "process_batch_task",
        _SyncTask(lambda bid: process_batch(db_session, storage, FakeLLMClient(), bid)),
    )
    job_id = _demo_job_id(client, auth_headers)
    batch_id = _upload(
        client, auth_headers, job_id, make_zip({"a.pdf": make_pdf("Hello Alpha")})
    ).json()["id"]
    resume_id = client.get(f"/api/batches/{batch_id}", headers=auth_headers).json()[
        "resumes"
    ][0]["id"]

    resp = client.get(f"/api/resumes/{resume_id}", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["extracted_content"]["name"] == "张三"
    assert "Hello Alpha" in data["extracted_text"]


def test_get_resume_detail_requires_auth(client):
    assert client.get("/api/resumes/1").status_code == 401


def test_get_resume_detail_404(client, auth_headers):
    assert client.get("/api/resumes/999999", headers=auth_headers).status_code == 404
