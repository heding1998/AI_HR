from sqlalchemy import delete, select

from app.batch_service import process_batch
from app.llm import LLMNotConfiguredError
from app.models import Application, Job, Resume, TalentPool, UploadBatch
from tests.fakes import FakeLLMClient, FakeStorage, make_pdf, make_zip


class _FailingResumeStorage(FakeStorage):
    """对简历对象的写入抛错，用于模拟对象存储故障。"""

    def put(self, key: str, data: bytes) -> None:
        if key.startswith("resumes/"):
            raise RuntimeError("storage down")
        super().put(key, data)


def _demo_job_id(db_session) -> int:
    return db_session.execute(select(Job).where(Job.code == "DEMO-JOB-001")).scalar_one().id


def _make_batch(db_session, job_id: int, storage: FakeStorage, zip_bytes: bytes) -> UploadBatch:
    batch = UploadBatch(job_id=job_id, status="pending")
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    storage.put(f"uploads/{batch.id}.zip", zip_bytes)
    return batch


def _resumes(db_session, batch_id: int) -> list[Resume]:
    return db_session.execute(select(Resume).where(Resume.batch_id == batch_id)).scalars().all()


def test_process_batch_creates_resumes(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    zipped = make_zip({"a.pdf": make_pdf("Hello Alpha"), "b.pdf": make_pdf("Hello Beta")})
    batch = _make_batch(db_session, job_id, storage, zipped)

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    resumes = _resumes(db_session, batch.id)
    assert len(resumes) == 2
    assert all(r.status == "extracted" for r in resumes)
    assert all(r.extracted_content is not None for r in resumes)
    assert {r.original_filename for r in resumes} == {"a.pdf", "b.pdf"}

    texts = {r.original_filename: r.extracted_text for r in resumes}
    assert "Hello Alpha" in texts["a.pdf"]
    assert "Hello Beta" in texts["b.pdf"]
    assert all(storage.get(r.file_key).startswith(b"%PDF") for r in resumes)

    db_session.refresh(batch)
    assert batch.status == "done"
    assert batch.total_count == 2
    assert batch.processed_count == 2


def test_process_batch_invalid_zip_marks_failed(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, b"not a zip at all")

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    db_session.refresh(batch)
    assert batch.status == "failed"
    assert batch.error


def test_process_batch_no_pdfs_marks_failed(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"note.txt": b"hello"}))

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    db_session.refresh(batch)
    assert batch.status == "failed"
    assert "PDF" in batch.error


def test_process_batch_skips_non_pdf(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    zipped = make_zip({"a.pdf": make_pdf("Hello Alpha"), "note.txt": b"hello"})
    batch = _make_batch(db_session, job_id, storage, zipped)

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    resumes = _resumes(db_session, batch.id)
    assert len(resumes) == 1
    assert resumes[0].original_filename == "a.pdf"

    db_session.refresh(batch)
    assert batch.status == "done"
    assert batch.total_count == 1
    assert batch.processed_count == 1


def test_process_batch_parse_error_marks_resume_failed(db_session, monkeypatch):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    zipped = make_zip({"a.pdf": make_pdf("ok"), "b.pdf": make_pdf("bad")})
    batch = _make_batch(db_session, job_id, storage, zipped)

    def boom(pdf_bytes: bytes) -> str:
        if b"bad" in pdf_bytes:
            raise RuntimeError("解析失败")
        return "ok"

    monkeypatch.setattr("app.batch_service.extract_pdf_text", boom)

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    statuses = {r.original_filename: r.status for r in _resumes(db_session, batch.id)}
    assert statuses == {"a.pdf": "extracted", "b.pdf": "failed"}
    db_session.refresh(batch)
    assert batch.status == "done"
    assert batch.processed_count == 2


def test_process_batch_storage_failure_marks_batch_failed(db_session):
    storage = _FailingResumeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"a.pdf": make_pdf("Hi")}))

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    db_session.refresh(batch)
    assert batch.status == "failed"
    assert batch.error


def test_process_batch_truncates_long_filename(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    long_name = "x" * 300 + ".pdf"
    batch = _make_batch(db_session, job_id, storage, make_zip({long_name: make_pdf("Hi")}))

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    resumes = _resumes(db_session, batch.id)
    assert len(resumes) == 1
    assert len(resumes[0].original_filename) <= 255
    db_session.refresh(batch)
    assert batch.status == "done"


def test_process_batch_oversized_entry_marks_resume_failed(db_session, monkeypatch):
    monkeypatch.setattr("app.batch_service.MAX_ENTRY_SIZE", 5)
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"a.pdf": make_pdf("Hello")}))

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    resumes = _resumes(db_session, batch.id)
    assert len(resumes) == 1
    assert resumes[0].status == "failed"
    assert "过大" in resumes[0].error
    db_session.refresh(batch)
    assert batch.status == "done"


def test_process_batch_extraction_failure_marks_anomaly(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"a.pdf": make_pdf("Hi")}))

    process_batch(db_session, storage, FakeLLMClient(error=RuntimeError("LLM 超时")), batch.id)

    resumes = _resumes(db_session, batch.id)
    assert resumes[0].status == "anomaly"
    assert "LLM 超时" in resumes[0].error
    assert resumes[0].extracted_content is None
    db_session.refresh(batch)
    assert batch.status == "done"


def test_process_batch_llm_unconfigured_marks_anomaly(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"a.pdf": make_pdf("Hi")}))

    process_batch(
        db_session,
        storage,
        FakeLLMClient(error=LLMNotConfiguredError("未配置 DEEPSEEK_API_KEY")),
        batch.id,
    )

    resumes = _resumes(db_session, batch.id)
    assert resumes[0].status == "anomaly"
    assert "DEEPSEEK_API_KEY" in resumes[0].error
    db_session.refresh(batch)
    assert batch.status == "done"


def test_process_batch_empty_text_marks_anomaly(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"scan.pdf": make_pdf("")}))

    process_batch(
        db_session,
        storage,
        FakeLLMClient(error=RuntimeError("不应调用 LLM")),
        batch.id,
    )

    resumes = _resumes(db_session, batch.id)
    assert resumes[0].status == "anomaly"
    assert "文本" in resumes[0].error
    assert resumes[0].extracted_content is None
    db_session.refresh(batch)
    assert batch.status == "done"


def test_process_batch_idempotent_when_resumes_exist(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"a.pdf": make_pdf("Hi")}))

    process_batch(db_session, storage, FakeLLMClient(), batch.id)
    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    resumes = _resumes(db_session, batch.id)
    assert len(resumes) == 1
    assert resumes[0].status == "extracted"
    assert len(db_session.execute(select(Application)).scalars().all()) == 1
    db_session.refresh(batch)
    assert batch.status == "done"


def test_process_batch_redelivery_regenerates_derived_data(db_session):
    """简历已建但派生数据缺失时（评分后崩溃），重投递应补跑应聘记录与人才库。"""
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"a.pdf": make_pdf("Hi")}))

    process_batch(db_session, storage, FakeLLMClient(), batch.id)
    db_session.execute(delete(Application))
    db_session.execute(delete(TalentPool))
    db_session.commit()

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    assert len(db_session.execute(select(Application)).scalars().all()) == 1
    assert len(db_session.execute(select(TalentPool)).scalars().all()) == 1
    db_session.refresh(batch)
    assert batch.status == "done"


def test_process_batch_scores_resume(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"a.pdf": make_pdf("Hi")}))

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    resume = _resumes(db_session, batch.id)[0]
    assert resume.status == "extracted"
    assert resume.score == 10.0
    assert resume.score_error is None


def test_process_batch_scoring_failure_keeps_batch_done(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"a.pdf": make_pdf("Hi")}))

    process_batch(
        db_session,
        storage,
        FakeLLMClient(score_error=RuntimeError("评分超时")),
        batch.id,
    )

    resume = _resumes(db_session, batch.id)[0]
    assert resume.status == "extracted"
    assert resume.score is None
    assert "评分超时" in resume.score_error
    db_session.refresh(batch)
    assert batch.status == "done"


def test_process_batch_no_standard_sets_score_error(db_session):
    storage = FakeStorage()
    job = Job(code="NO-STD-1", name="无标准岗位", location="厦门")
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    batch = _make_batch(db_session, job.id, storage, make_zip({"a.pdf": make_pdf("Hi")}))

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    resume = _resumes(db_session, batch.id)[0]
    assert resume.score is None
    assert resume.score_error == "岗位未配置评分标准"
    db_session.refresh(batch)
    assert batch.status == "done"


def test_process_batch_generates_application_and_pool(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"a.pdf": make_pdf("Hi")}))

    process_batch(db_session, storage, FakeLLMClient(), batch.id)

    apps = db_session.execute(select(Application)).scalars().all()
    assert len(apps) == 1
    assert apps[0].status == "passed"
    assert apps[0].score == 10.0
    assert apps[0].candidate_name == "张三"

    pool = db_session.execute(select(TalentPool)).scalars().all()
    assert len(pool) == 1
    assert pool[0].name == "张三"
    assert pool[0].score == 10.0
    assert pool[0].tier == "特别优秀"


def test_process_batch_low_score_marks_failed_and_skips_pool(db_session):
    storage = FakeStorage()
    job_id = _demo_job_id(db_session)
    batch = _make_batch(db_session, job_id, storage, make_zip({"a.pdf": make_pdf("Hi")}))

    process_batch(db_session, storage, FakeLLMClient(match_weights={}), batch.id)

    apps = db_session.execute(select(Application)).scalars().all()
    assert len(apps) == 1
    assert apps[0].status == "failed"
    assert apps[0].score == 0.0

    assert db_session.execute(select(TalentPool)).scalars().all() == []
