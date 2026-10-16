"""测试用假实现与夹具：内存对象存储、最小 PDF、ZIP 构造。"""

import io
import zipfile


class FakeStorage:
    """内存对象存储，替换 MinIO。"""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    def put(self, key: str, data: bytes) -> None:
        self._data[key] = data

    def get(self, key: str) -> bytes:
        return self._data[key]


class FakeLLMClient:
    """假 LLM：返回固定字段，或抛出指定异常。"""

    def __init__(
        self, result: dict | None = None, error: Exception | None = None
    ) -> None:
        if result is None:
            result = {"name": "张三", "contact": "13800000000"}
        self._result = result
        self._error = error

    def extract_resume_fields(self, text: str) -> dict:
        if self._error is not None:
            raise self._error
        return dict(self._result)


def make_pdf(text: str) -> bytes:
    """构造一个含指定文本的最小合法单页 PDF。"""
    catalog = b"<< /Type /Catalog /Pages 2 0 R >>"
    pages = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    page = (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>"
    )
    font = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    content = ("BT /F1 24 Tf 100 700 Td (" + text + ") Tj ET").encode()
    stream = (
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream"
    )
    objects = [catalog, pages, page, stream, font]

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += str(i).encode() + b" 0 obj\n" + obj + b"\nendobj\n"

    xref = len(out)
    out += ("xref\n0 " + str(len(objects) + 1) + "\n").encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        b"trailer\n<< /Size "
        + str(len(objects) + 1).encode()
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref).encode()
        + b"\n%%EOF\n"
    )
    return bytes(out)


def make_zip(files: dict[str, bytes]) -> bytes:
    """构造包含指定文件的 ZIP 字节。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()
