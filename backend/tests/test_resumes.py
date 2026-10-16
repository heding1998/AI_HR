from app.batch_service import process_batch
from app.deps import get_llm
from app.main import app
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


def test_rescore_sets_score_after_failure(
    client, auth_headers, db_session, storage, monkeypatch
):
    monkeypatch.setattr(
        batches,
        "process_batch_task",
        _SyncTask(
            lambda bid: process_batch(
                db_session, storage, FakeLLMClient(score_error=RuntimeError("评分超时")), bid
            )
        ),
    )
    job_id = _demo_job_id(client, auth_headers)
    batch_id = _upload(
        client, auth_headers, job_id, make_zip({"a.pdf": make_pdf("Hi")})
    ).json()["id"]
    resume = client.get(f"/api/batches/{batch_id}", headers=auth_headers).json()[
        "resumes"
    ][0]
    assert resume["score"] is None

    resp = client.post(f"/api/resumes/{resume['id']}/rescore", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()["score"] == 10.0
    assert resp.json()["score_error"] is None


def test_rescore_failure_sets_score_error(
    client, auth_headers, db_session, storage, monkeypatch
):
    monkeypatch.setattr(
        batches,
        "process_batch_task",
        _SyncTask(lambda bid: process_batch(db_session, storage, FakeLLMClient(), bid)),
    )
    monkeypatch.setitem(
        app.dependency_overrides,
        get_llm,
        lambda: FakeLLMClient(score_error=RuntimeError("评分超时")),
    )
    job_id = _demo_job_id(client, auth_headers)
    batch_id = _upload(
        client, auth_headers, job_id, make_zip({"a.pdf": make_pdf("Hi")})
    ).json()["id"]
    resume = client.get(f"/api/batches/{batch_id}", headers=auth_headers).json()[
        "resumes"
    ][0]

    resp = client.post(f"/api/resumes/{resume['id']}/rescore", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()["score"] is None
    assert "评分超时" in resp.json()["score_error"]


def test_rescore_requires_auth(client):
    assert client.post("/api/resumes/1/rescore").status_code == 401


def test_rescore_404(client, auth_headers):
    assert client.post("/api/resumes/999999/rescore", headers=auth_headers).status_code == 404


def test_rescore_not_extracted_returns_400(
    client, auth_headers, db_session, storage, monkeypatch
):
    monkeypatch.setattr(
        batches,
        "process_batch_task",
        _SyncTask(lambda bid: process_batch(db_session, storage, FakeLLMClient(), bid)),
    )
    job_id = _demo_job_id(client, auth_headers)
    batch_id = _upload(
        client, auth_headers, job_id, make_zip({"scan.pdf": make_pdf("")})
    ).json()["id"]
    resume = client.get(f"/api/batches/{batch_id}", headers=auth_headers).json()[
        "resumes"
    ][0]

    resp = client.post(f"/api/resumes/{resume['id']}/rescore", headers=auth_headers)

    assert resp.status_code == 400
