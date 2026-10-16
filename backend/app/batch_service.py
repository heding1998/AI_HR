"""批次异步处理核心逻辑：解压 ZIP、逐份提取 PDF 文本、落库。"""

import io
import zipfile

from sqlalchemy.orm import Session

from .models import Resume, UploadBatch
from .parsing import extract_pdf_text
from .storage import ObjectStorage

STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

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


def process_batch(session: Session, storage: ObjectStorage, batch_id: int) -> None:
    batch = session.get(UploadBatch, batch_id)
    if batch is None:
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
                    status="failed",
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
                    status="parsed",
                )
            session.add(resume)
            batch.processed_count += 1
            session.commit()
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
