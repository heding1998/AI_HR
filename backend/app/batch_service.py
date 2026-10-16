"""批次异步处理核心逻辑：解压 ZIP、逐份提取 PDF 文本、AI 提取字段、落库。"""

import io
import zipfile
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from .extraction import normalize_resume_fields
from .llm import LLMClient
from .models import Resume, ScoringStandardA, ScoringStandardB, UploadBatch
from .parsing import extract_pdf_text
from .recruitment import record_application_and_pool
from .schemas import ScoringStandardAIn, ScoringStandardBIn
from .scoring import compute_resume_score
from .storage import ObjectStorage

STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

RESUME_STATUS_PARSED = "parsed"
RESUME_STATUS_FAILED = "failed"
RESUME_STATUS_EXTRACTED = "extracted"
RESUME_STATUS_ANOMALY = "anomaly"

MAX_ENTRY_SIZE = 20 * 1024 * 1024  # 单个 PDF 解压后最大 20MB
MAX_TOTAL_SIZE = 200 * 1024 * 1024  # 单批解压后合计最大 200MB
MAX_ENTRIES = 200  # 单批最多 200 份 PDF
FILENAME_LIMIT = 255


def _truncate(value: str, limit: int = FILENAME_LIMIT) -> str:
    return value[:limit]


def _basename(name: str) -> str:
    """取 ZIP 条目名最后一个路径段，归一化 Windows/Unix 分隔符。"""
    normalized = name.replace("\\", "/")
    return normalized.rsplit("/", 1)[-1]


def load_scoring_standard(
    session: Session, job_id: int
) -> tuple[list[ScoringStandardAIn], list[ScoringStandardBIn]]:
    """按岗位一次性加载 A/B 评分标准，转为 schema 供评分计算使用。"""
    a_orm = session.execute(
        select(ScoringStandardA).where(ScoringStandardA.job_id == job_id)
    ).scalars().all()
    b_orm = session.execute(
        select(ScoringStandardB).where(ScoringStandardB.job_id == job_id)
    ).scalars().all()
    a_rows = [
        ScoringStandardAIn(
            category=r.category,
            subcategory=r.subcategory,
            category_score=r.category_score,
            subcategory_score=r.subcategory_score,
        )
        for r in a_orm
    ]
    b_rows = [
        ScoringStandardBIn(
            category=r.category,
            subcategory=r.subcategory,
            level1_indicator=r.level1_indicator,
            level2_indicator=r.level2_indicator,
            weight=r.weight,
        )
        for r in b_orm
    ]
    return a_rows, b_rows


def score_resume_record(
    llm: LLMClient,
    resume: Resume,
    a_rows: Sequence[ScoringStandardAIn],
    b_rows: Sequence[ScoringStandardBIn],
) -> None:
    """按已加载的评分标准为简历打分，写入 score/score_error（不提交）。"""
    if not a_rows:
        resume.score = None
        resume.score_error = "岗位未配置评分标准"
        return

    try:
        weights = llm.score_resume(resume.extracted_content or {}, a_rows, b_rows)
        resume.score = compute_resume_score(a_rows, weights)
        resume.score_error = None
    except Exception as exc:
        resume.score = None
        resume.score_error = _truncate(str(exc) or "评分失败")


def _generate_applications_and_pool(session: Session, batch_id: int) -> None:
    """为批次中已评分的简历生成应聘记录与人才库条目（幂等）。"""
    scored_resumes = session.execute(
        select(Resume)
        .where(Resume.batch_id == batch_id, Resume.status == RESUME_STATUS_EXTRACTED)
        .order_by(Resume.id)
    ).scalars().all()
    for resume in scored_resumes:
        record_application_and_pool(session, resume)
        session.commit()


def process_batch(
    session: Session, storage: ObjectStorage, llm: LLMClient, batch_id: int
) -> None:
    batch = session.get(UploadBatch, batch_id)
    if batch is None:
        return

    # 幂等保护：批次已生成过简历时直接跳过，避免任务重投递导致重复。
    already_processed = session.execute(
        select(Resume.id).where(Resume.batch_id == batch_id).limit(1)
    ).scalar_one_or_none()
    if already_processed is not None:
        # 简历已建（任务重投递/崩溃恢复）：仅补跑派生数据，幂等。
        _generate_applications_and_pool(session, batch.id)
        batch.status = STATUS_DONE
        session.commit()
        return

    batch.status = STATUS_PROCESSING
    session.commit()

    try:
        zip_bytes = storage.get(f"uploads/{batch_id}.zip")
    except Exception:
        batch.status = STATUS_FAILED
        batch.error = "上传文件不存在或无法读取"
        session.commit()
        return

    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        batch.status = STATUS_FAILED
        batch.error = "不是有效的 ZIP 文件"
        session.commit()
        return

    try:
        pdf_infos = [
            (name, zf.getinfo(name))
            for name in zf.namelist()
            if name.lower().endswith(".pdf")
        ]
        if not pdf_infos:
            batch.status = STATUS_FAILED
            batch.error = "ZIP 中未找到 PDF 文件"
            session.commit()
            return

        if len(pdf_infos) > MAX_ENTRIES:
            batch.status = STATUS_FAILED
            batch.error = f"ZIP 中 PDF 数量超过上限（{MAX_ENTRIES} 份）"
            session.commit()
            return

        if sum(info.file_size for _, info in pdf_infos) > MAX_TOTAL_SIZE:
            batch.status = STATUS_FAILED
            batch.error = "ZIP 解压后总大小超过上限"
            session.commit()
            return

        batch.total_count = len(pdf_infos)
        batch.processed_count = 0
        session.commit()

        for index, (name, info) in enumerate(pdf_infos):
            basename = _truncate(_basename(name))
            file_key = _truncate(f"resumes/{batch_id}/{index:03d}_{basename}")
            try:
                if info.file_size > MAX_ENTRY_SIZE:
                    raise ValueError("文件过大")
                pdf_bytes = zf.read(name)
                text = extract_pdf_text(pdf_bytes)
            except Exception as exc:
                resume = Resume(
                    batch_id=batch.id,
                    job_id=batch.job_id,
                    original_filename=basename,
                    file_key=file_key,
                    extracted_text="",
                    status=RESUME_STATUS_FAILED,
                    error=_truncate(str(exc) or "解析失败"),
                )
            else:
                storage.put(file_key, pdf_bytes)
                resume = Resume(
                    batch_id=batch.id,
                    job_id=batch.job_id,
                    original_filename=basename,
                    file_key=file_key,
                    extracted_text=text or "",
                    status=RESUME_STATUS_PARSED,
                )
            session.add(resume)
            batch.processed_count += 1
            session.commit()

        # 提取阶段：对已解析的简历调用 LLM，逐份容错。
        resumes = session.execute(
            select(Resume)
            .where(Resume.batch_id == batch_id, Resume.status == RESUME_STATUS_PARSED)
            .order_by(Resume.id)
        ).scalars().all()
        for resume in resumes:
            if not resume.extracted_text.strip():
                resume.status = RESUME_STATUS_ANOMALY
                resume.error = "未提取到文本"
                session.commit()
                continue
            try:
                fields = normalize_resume_fields(
                    llm.extract_resume_fields(resume.extracted_text)
                )
            except Exception as exc:
                resume.status = RESUME_STATUS_ANOMALY
                resume.error = _truncate(str(exc) or "提取失败")
            else:
                resume.extracted_content = fields
                resume.status = RESUME_STATUS_EXTRACTED
            session.commit()

        # 评分阶段：对已提取的简历按岗位评分标准打分，逐份容错。
        a_rows, b_rows = load_scoring_standard(session, batch.job_id)
        scored_resumes = session.execute(
            select(Resume)
            .where(Resume.batch_id == batch_id, Resume.status == RESUME_STATUS_EXTRACTED)
            .order_by(Resume.id)
        ).scalars().all()
        for resume in scored_resumes:
            score_resume_record(llm, resume, a_rows, b_rows)
            session.commit()

        # 应聘记录与人才库：按分数阈值生成应聘记录，达标者写入高分人才库。
        _generate_applications_and_pool(session, batch.id)
    except Exception as exc:
        session.rollback()
        batch.status = STATUS_FAILED
        batch.error = _truncate(str(exc) or "处理失败")
        session.commit()
        return
    finally:
        zf.close()

    batch.status = STATUS_DONE
    session.commit()
