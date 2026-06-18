def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150
) -> list[str]:
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end - overlap

        if start < 0:
            start = 0

        if start >= text_length:
            break

    return chunks