import re
import unicodedata

from pypdf import PdfReader


def _clean_page_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    # Satır sonunda tireyle bölünmüş kelimeleri birleştir: "geliş-\ntirme" -> "geliştirme"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Satır içi fazla boşlukları sadeleştir, satır yapısını koru.
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pages_from_pdf(file_path: str) -> list[tuple[int, str]]:
    """PDF'i sayfa sayfa okur: [(sayfa_no, metin), ...]. Boş sayfalar atlanır."""
    reader = PdfReader(file_path)
    pages: list[tuple[int, str]] = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = _clean_page_text(page.extract_text() or "")
        if page_text:
            pages.append((page_number, page_text))

    return pages


def extract_text_from_pdf(file_path: str) -> str:
    return "\n\n".join(text for _, text in extract_pages_from_pdf(file_path))
