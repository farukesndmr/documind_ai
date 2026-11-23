"""OpenAI ile gerçek (anlamsal) embedding üretimi.

Embedding, bir metnin anlamını sayı vektörüne çevirir: anlamca benzer metinler
birbirine yakın vektörler üretir ("araba" ≈ "otomobil"). Daha önce burada
kelimelerin MD5 hash'iyle üretilen ve anlam taşımayan bir vektör vardı.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from openai import OpenAI

from app.core.config import settings
from app.usage.service import (
    calculate_embedding_cost,
    ensure_budget_available,
    record_usage,
)


logger = logging.getLogger(__name__)

# Tek istekte gönderilecek en fazla metin sayısı (API sınırının altında kalır).
BATCH_SIZE = 96
# Çok uzun bir parça API sınırını aşmasın diye güvenli üst sınır (karakter).
MAX_CHARS_PER_INPUT = 8000


class EmbeddingError(RuntimeError):
    """Embedding üretilemediğinde fırlatılır; çağıran taraf anahtar kelime aramasına düşebilir."""


def current_embedding_model() -> str:
    """Veritabanında, parçanın hangi modelle ve kaç boyutla embed edildiğini işaretlemek için."""
    return f"{settings.OPENAI_EMBEDDING_MODEL}:{settings.EMBEDDING_DIMENSIONS}"


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    if settings.OPENAI_API_KEY is None:
        raise EmbeddingError("OPENAI_API_KEY tanımlı değil.")
    api_key = settings.OPENAI_API_KEY.get_secret_value().strip()
    if not api_key:
        raise EmbeddingError("OPENAI_API_KEY boş.")
    return OpenAI(api_key=api_key, timeout=60.0, max_retries=2)


def _prepare(text: str) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned[:MAX_CHARS_PER_INPUT] or " "


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Metin listesini toplu (batch) olarak embed eder. Sıra korunur."""
    if not texts:
        return []

    prepared = [_prepare(t) for t in texts]

    # Embedding çok ucuzdur ama bütçe limiti dolduysa yine de istek atmayalım.
    estimated_tokens = sum(len(t) for t in prepared) // 3 + 1
    try:
        ensure_budget_available(calculate_embedding_cost(estimated_tokens))
    except RuntimeError as exc:
        raise EmbeddingError(str(exc)) from exc

    vectors: list[list[float]] = []
    total_tokens = 0

    try:
        client = _client()
        for start in range(0, len(prepared), BATCH_SIZE):
            batch = prepared[start:start + BATCH_SIZE]
            response = client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=batch,
                dimensions=settings.EMBEDDING_DIMENSIONS,
            )
            # API sonuçları "index" alanıyla döndürür; sırayı garanti altına al.
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors.extend(item.embedding for item in ordered)
            usage = getattr(response, "usage", None)
            total_tokens += int(getattr(usage, "total_tokens", 0) or 0)
    except EmbeddingError:
        raise
    except Exception as exc:
        logger.warning("Embedding üretilemedi: %s: %s", type(exc).__name__, exc)
        raise EmbeddingError("Embedding servisine ulaşılamadı.") from exc

    if total_tokens:
        record_usage(
            input_tokens=total_tokens,
            output_tokens=0,
            cost_usd=calculate_embedding_cost(total_tokens),
        )

    logger.info(
        "Embedding üretildi: %d metin, %d token, model=%s",
        len(vectors), total_tokens, current_embedding_model(),
    )
    return vectors


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
