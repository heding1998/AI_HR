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


def test_upload_batch_creates_batch(client, auth_headers, storage, monkeypatch):
    monkeypatch.setattr(batches, "process_batch_task", _SyncTask(lambda _: None))
    job_id = _demo_job_id(client, auth_headers)

    resp = _upload(client, auth_headers, job_id, make_zip({"a.pdf": make_pdf("Hi")}))

    assert resp.status_code == 201
    body = resp.json()
    assert body["job_id"] == job_id
    assert body["status"] == "pending"
    assert storage.get(f"uploads/{body['id']}.zip").startswith(b"PK")


def test_upload_batch_invalid_zip_returns_400(client, auth_headers, monkeypatch):
    monkeypatch.setattr(batches, "process_batch_task", _SyncTask(lambda _: None))
    job_id = _demo_job_id(client, auth_headers)

    resp = _upload(client, auth_headers, job_id, b"not a zip")

    assert resp.status_code == 400


def test_upload_batch_requires_auth(client):
    assert client.post("/api/batches", data={}, files={}).status_code == 401


def test_list_batches(client, auth_headers, storage, monkeypatch):
    monkeypatch.setattr(batches, "process_batch_task", _SyncTask(lambda _: None))
    job_id = _demo_job_id(client, auth_headers)
    _upload(client, auth_headers, job_id, make_zip({"a.pdf": make_pdf("Hi")}))

    resp = client.get("/api/batches", headers=auth_headers)

    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_batch_detail_with_resumes(client, auth_headers, db_session, storage, monkeypatch):
    monkeypatch.setattr(
        batches,
        "process_batch_task",
        _SyncTask(lambda bid: process_batch(db_session, storage, FakeLLMClient(), bid)),
    )
    job_id = _demo_job_id(client, auth_headers)
    batch_id = _upload(
        client, auth_headers, job_id, make_zip({"a.pdf": make_pdf("Hello Alpha")})
    ).json()["id"]

    resp = client.get(f"/api/batches/{batch_id}", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert len(data["resumes"]) == 1
    assert data["resumes"][0]["original_filename"] == "a.pdf"


def test_upload_batch_storage_failure_returns_503(client, auth_headers, storage, monkeypatch):
    monkeypatch.setattr(batches, "process_batch_task", _SyncTask(lambda _: None))

    def boom(key, data):
        raise RuntimeError("minio down")

    monkeypatch.setattr(storage, "put", boom)
    job_id = _demo_job_id(client, auth_headers)

    resp = _upload(client, auth_headers, job_id, make_zip({"a.pdf": make_pdf("Hi")}))

    assert resp.status_code == 503
    listed = client.get("/api/batches", headers=auth_headers).json()
    assert len(listed) == 1
    assert listed[0]["status"] == "failed"


def test_upload_batch_too_large_returns_413(client, auth_headers, monkeypatch):
    monkeypatch.setattr(batches, "process_batch_task", _SyncTask(lambda _: None))
    monkeypatch.setattr(batches, "MAX_UPLOAD_BYTES", 10)
    job_id = _demo_job_id(client, auth_headers)

    resp = _upload(client, auth_headers, job_id, make_zip({"a.pdf": make_pdf("Hi")}))

    assert resp.status_code == 413
