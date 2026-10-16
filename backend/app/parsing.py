"""PDF 文本提取。"""

import io

import pdfplumber


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """从 PDF 字节中提取全文文本；解析失败时抛出异常由调用方处理。"""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)
