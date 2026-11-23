import logging
import re
from typing import Sequence

from sqlalchemy.orm import Session

from app.documents.embedding_utils import (
    EmbeddingError,
    current_embedding_model,
    embed_query,
)
from app.documents.models import DocumentChunk
from app.documents.service import ensure_document_embeddings


logger = logging.getLogger(__name__)

# Hibrit aramada vektör ve anahtar kelime listelerinden kaçar aday alınacağı.
CANDIDATE_POOL = 20
# Reciprocal Rank Fusion sabiti (literatürdeki yaygın değer).
RRF_K = 60


SUMMARY_KEYWORDS = [
    "özet",
    "özetle",
    "özetini",
    "summary",
    "summarize",
    "ders notu",
    "sınav",
    "exam",
    "çalışma notu",
    "konu anlatımı",
    "detaylı anlat",
    "detaylı özet",
]


# Belgenin geneline yayılan ama "ders notu" formatı istemeyen görevler.
# Bunlarda parçalar belgeye eşit dağılarak seçilir, cevap formatı soruya göre belirlenir.
BROAD_KEYWORDS = [
    "flashcard",
    "quiz",
    "key concepts",
    "important concepts",
    "main concepts",
    "overview",
    "whole document",
    "entire document",
    "önemli kavram",
    "temel kavram",
    "tüm belge",
    "belgenin tamamı",
    "genel bakış",
]


STOP_WORDS = {
    "bana",
    "şunu",
    "bunu",
    "için",
    "olan",
    "nedir",
    "midir",
    "pdf",
    "doküman",
    "döküman",
    "belge",
    "çıkar",
    "çıkarır",
    "misin",
    "musun",
    "kısa",
    "detaylı",
    "türkçe",
    "ingilizce",
    "cümle",
    "kullanma",
}


def is_summary_request(question: str) -> bool:
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in SUMMARY_KEYWORDS)


def is_broad_request(question: str) -> bool:
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in BROAD_KEYWORDS)


def tokenize(text: str) -> list[str]:
    cleaned_text = re.sub(
        r"[^a-zA-Z0-9ğüşöçıİĞÜŞÖÇ]+",
        " ",
        text.lower(),
    )

    return [
        word
        for word in cleaned_text.split()
        if len(word) > 2 and word not in STOP_WORDS
    ]


def score_chunk(content: str, question_tokens: list[str]) -> int:
    content_lower = content.lower()
    score = 0

    for token in question_tokens:
        score += content_lower.count(token)

    return score


def get_document_chunks(
    db: Session,
    document_id: int,
) -> list[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )


def limit_by_char_count(
    chunks: Sequence[DocumentChunk],
    max_chars: int,
) -> list[DocumentChunk]:
    selected_chunks: list[DocumentChunk] = []
    total_chars = 0

    for chunk in chunks:
        content = chunk.content or ""
        content_length = len(content)

        if selected_chunks and total_chars + content_length > max_chars:
            break

        selected_chunks.append(chunk)
        total_chars += content_length

    return selected_chunks


def select_summary_chunks(
    chunks: Sequence[DocumentChunk],
    limit: int = 12,
) -> list[DocumentChunk]:
    if not chunks:
        return []

    total_chunks = len(chunks)

    if total_chunks <= limit:
        return limit_by_char_count(chunks, max_chars=14000)

    selected_indexes = set()

    # Başlangıç kısmı genelde konu başlığı ve giriş içerir.
    selected_indexes.add(0)

    # PDF'in geneline yayılmış chunk seç.
    step = max(total_chunks // limit, 1)

    for index in range(0, total_chunks, step):
        selected_indexes.add(index)

        if len(selected_indexes) >= limit:
            break

    selected_chunks = [
        chunks[index]
        for index in sorted(selected_indexes)
        if index < total_chunks
    ]

    return limit_by_char_count(selected_chunks, max_chars=14000)


def keyword_ranking(
    chunks: Sequence[DocumentChunk],
    question: str,
) -> list[int]:
    """Soru kelimelerinin geçme sıklığına göre chunk id'lerini sıralar (puanı 0 olanlar hariç)."""
    question_tokens = tokenize(question)
    if not question_tokens:
        return []

    scored = [
        (score_chunk(chunk.content or "", question_tokens), chunk.chunk_index, chunk.id)
        for chunk in chunks
    ]
    scored = [item for item in scored if item[0] > 0]
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [chunk_id for _, _, chunk_id in scored[:CANDIDATE_POOL]]


def vector_ranking(
    db: Session,
    document_id: int,
    question: str,
) -> list[int]:
    """Soruya anlamca en yakın chunk id'lerini döndürür (pgvector, kosinüs mesafesi).

    Arama tek bir belgenin parçaları içinde yapıldığı için (genelde birkaç yüz
    parça) tam (exact) arama hem hızlı hem kesin sonuç verir. HNSW gibi yaklaşık
    indeksler, document_id filtresiyle birlikte k'dan az sonuç döndürebileceği
    için burada bilinçli olarak kullanılmıyor.
    """
    if not ensure_document_embeddings(db, document_id):
        return []

    try:
        query_vector = embed_query(question)
    except EmbeddingError:
        return []

    rows = (
        db.query(DocumentChunk.id)
        .filter(DocumentChunk.document_id == document_id)
        .filter(DocumentChunk.embedding.isnot(None))
        .filter(DocumentChunk.embedding_model == current_embedding_model())
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(CANDIDATE_POOL)
        .all()
    )
    return [row.id for row in rows]


def reciprocal_rank_fusion(*rankings: list[int], k: int = RRF_K) -> list[int]:
    """Birden çok sıralı listeyi, skorları değil sıraları kullanarak birleştirir."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda chunk_id: -scores[chunk_id])


def select_question_chunks(
    db: Session,
    document_id: int,
    chunks: Sequence[DocumentChunk],
    question: str,
    limit: int = 8,
) -> list[DocumentChunk]:
    if not chunks:
        return []

    if len(chunks) <= limit:
        return limit_by_char_count(chunks, max_chars=10000)

    vector_ids = vector_ranking(db, document_id, question)
    keyword_ids = keyword_ranking(chunks, question)
    fused_ids = reciprocal_rank_fusion(vector_ids, keyword_ids)

    logger.info(
        "Belge %s retrieval: vektör=%d, anahtar kelime=%d aday",
        document_id, len(vector_ids), len(keyword_ids),
    )

    by_id = {chunk.id: chunk for chunk in chunks}
    selected = [by_id[chunk_id] for chunk_id in fused_ids[:limit] if chunk_id in by_id]

    if not selected:
        # Ne vektör ne anahtar kelime sonuç verdiyse belgenin başından başla.
        selected = list(chunks[:limit])

    # Karakter sınırı önem sırasına göre uygulanır (en alakalılar kesilmesin),
    # ardından okuma akışı bozulmasın diye LLM'e belge sırasıyla verilir.
    selected = limit_by_char_count(selected, max_chars=10000)
    selected.sort(key=lambda chunk: chunk.chunk_index)
    return selected


def retrieve_context_chunks(
    db: Session,
    document_id: int,
    question: str,
    limit: int = 8,
    search_query: str | None = None,
) -> tuple[list[DocumentChunk], str]:
    """Soruya uygun parçaları ve modu ("summary", "broad", "qa") döndürür.

    search_query verilirse arama onunla yapılır (ör. takip sorusu + önceki soru);
    mod ise her zaman kullanıcının asıl sorusundan belirlenir.
    """
    chunks = get_document_chunks(
        db=db,
        document_id=document_id,
    )

    if is_summary_request(question):
        return select_summary_chunks(chunks=chunks, limit=max(limit, 12)), "summary"

    if is_broad_request(question):
        return select_summary_chunks(chunks=chunks, limit=max(limit, 12)), "broad"

    selected_chunks = select_question_chunks(
        db=db,
        document_id=document_id,
        chunks=chunks,
        question=search_query or question,
        limit=min(limit, 8),
    )

    return selected_chunks, "qa"
