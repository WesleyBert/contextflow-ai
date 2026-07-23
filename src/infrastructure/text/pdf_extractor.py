from io import BytesIO

from pypdf import PdfReader


def extract_text(content: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        reader = PdfReader(BytesIO(content))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    return content.decode("utf-8", errors="ignore")
