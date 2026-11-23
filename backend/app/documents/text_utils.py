"""Metni anlamlı sınırlardan (paragraf, satır, cümle, kelime) bölen chunking araçları."""

from dataclasses import dataclass


# Önce en "büyük" sınırdan bölmeyi dener; parça hâlâ büyükse bir sonrakine geçer.
SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]


@dataclass(frozen=True)
class TextChunk:
    content: str
    page_number: int | None = None


def _split_recursive(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    """Metni chunk_size'ı aşmayan, mümkün olduğunca büyük doğal parçalara ayırır."""
    if len(text) <= chunk_size:
        return [text]

    if not separators:
        # Hiçbir ayırıcı işe yaramadıysa sabit boyutta kes (çok nadir).
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    separator, rest = separators[0], separators[1:]
    if separator not in text:
        return _split_recursive(text, chunk_size, rest)

    pieces = text.split(separator)
    pieces = [p + separator for p in pieces[:-1]] + [pieces[-1]]

    result: list[str] = []
    for piece in pieces:
        if len(piece) > chunk_size:
            result.extend(_split_recursive(piece, chunk_size, rest))
        elif piece:
            result.append(piece)
    return result


def _merge_with_overlap(pieces: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Küçük parçaları chunk_size'a kadar birleştirir; ardışık chunk'lar arasında overlap bırakır."""
    chunks: list[str] = []
    current = ""

    for piece in pieces:
        if current and len(current) + len(piece) > chunk_size:
            chunks.append(current.strip())
            # Önceki chunk'ın sonundan, kelime sınırına hizalı bir örtüşme al.
            tail = current[-overlap:] if overlap > 0 else ""
            if tail and " " in tail:
                tail = tail[tail.index(" ") + 1:]
            current = tail
            if len(current) + len(piece) > chunk_size:
                current = ""
        current += piece

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if c]


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[str]:
    if not text or not text.strip():
        return []
    pieces = _split_recursive(text, chunk_size, SEPARATORS)
    return _merge_with_overlap(pieces, chunk_size, overlap)


def split_pages_into_chunks(
    pages: list[tuple[int, str]],
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[TextChunk]:
    """Her sayfayı ayrı böler; böylece her chunk'ın hangi sayfadan geldiği bilinir."""
    chunks: list[TextChunk] = []
    for page_number, page_text in pages:
        for content in split_text_into_chunks(page_text, chunk_size, overlap):
            chunks.append(TextChunk(content=content, page_number=page_number))
    return chunks
