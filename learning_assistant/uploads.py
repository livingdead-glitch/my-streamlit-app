"""Upload identity and temporary files, independent of Streamlit and API clients."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile


def document_signature(files):
    if not files:
        return None
    entries = sorted((name, hashlib.sha256(data).hexdigest()) for name, data in files)
    return hashlib.sha256(json.dumps(entries, ensure_ascii=False).encode()).hexdigest()


@contextmanager
def temporary_pdfs(files):
    if sum(len(data) for _, data in files) > 30 * 1024 * 1024:
        raise ValueError("PDF 합계가 30MB를 넘습니다. 파일 수나 크기를 줄여 주세요.")
    with tempfile.TemporaryDirectory(prefix="aivle_pdf_") as directory:
        paths = []
        for index, (name, data) in enumerate(files):
            if not data.startswith(b"%PDF-"):
                raise ValueError(f"{name}: 올바른 PDF 파일이 아닙니다.")
            path = Path(directory) / f"document_{index}.pdf"
            path.write_bytes(data)
            paths.append((name, path))
        yield paths
