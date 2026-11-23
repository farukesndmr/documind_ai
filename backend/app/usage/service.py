"""OpenAI kullanım bütçesinin takibi (veritabanı tabanlı)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.database.connection import SessionLocal
from app.usage.models import OpenAIUsage


logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]
LEGACY_USAGE_FILE = BACKEND_DIR / "data" / "openai_usage.json"


class BudgetExceededError(RuntimeError):
    """Aylık OpenAI bütçe limiti dolduğunda fırlatılır."""


def current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _legacy_seed(month: str) -> dict[str, Any]:
    """Eski JSON dosyasındaki bu ayın kullanımını ilk kayıtta içeri alır."""
    try:
        data = json.loads(LEGACY_USAGE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

    if data.get("month") != month:
        return {}

    return {
        "spent_usd": float(data.get("spent_usd", 0.0)),
        "input_tokens": int(data.get("input_tokens", 0)),
        "output_tokens": int(data.get("output_tokens", 0)),
        "request_count": int(data.get("request_count", 0)),
    }


def _ensure_row(db, month: str) -> None:
    seed = _legacy_seed(month)
    stmt = (
        insert(OpenAIUsage)
        .values(
            month=month,
            spent_usd=seed.get("spent_usd", 0.0),
            input_tokens=seed.get("input_tokens", 0),
            output_tokens=seed.get("output_tokens", 0),
            request_count=seed.get("request_count", 0),
        )
        .on_conflict_do_nothing(index_elements=["month"])
    )
    db.execute(stmt)


def calculate_chat_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens / 1_000_000 * settings.OPENAI_INPUT_PRICE_PER_1M
        + output_tokens / 1_000_000 * settings.OPENAI_OUTPUT_PRICE_PER_1M
    )


def calculate_embedding_cost(tokens: int) -> float:
    return tokens / 1_000_000 * settings.OPENAI_EMBEDDING_PRICE_PER_1M


def get_usage() -> dict[str, Any]:
    month = current_month()
    with SessionLocal() as db:
        _ensure_row(db, month)
        db.commit()
        row = db.get(OpenAIUsage, month)
        spent = float(row.spent_usd)
        return {
            "month": month,
            "spent_usd": round(spent, 8),
            "input_tokens": int(row.input_tokens),
            "output_tokens": int(row.output_tokens),
            "request_count": int(row.request_count),
            "hard_limit_usd": settings.OPENAI_HARD_LIMIT_USD,
            "remaining_usd": round(
                max(settings.OPENAI_HARD_LIMIT_USD - spent, 0.0), 8
            ),
            "model": settings.OPENAI_MODEL,
        }


def ensure_budget_available(estimated_cost_usd: float) -> None:
    """İstek gönderilmeden önce, olası en yüksek maliyetin bütçeye sığdığını kontrol eder."""
    usage = get_usage()
    if usage["spent_usd"] + estimated_cost_usd > settings.OPENAI_HARD_LIMIT_USD:
        raise BudgetExceededError(
            "DocuMind için belirlenen aylık yapay zekâ kullanım limiti doldu. "
            "Lütfen daha sonra tekrar deneyin."
        )


def record_usage(input_tokens: int, output_tokens: int, cost_usd: float) -> None:
    """Gerçekleşen kullanımı atomik olarak sayaca ekler."""
    month = current_month()
    try:
        with SessionLocal() as db:
            _ensure_row(db, month)
            row = db.get(OpenAIUsage, month, with_for_update=True)
            row.spent_usd = float(row.spent_usd) + cost_usd
            row.input_tokens = int(row.input_tokens) + input_tokens
            row.output_tokens = int(row.output_tokens) + output_tokens
            row.request_count = int(row.request_count) + 1
            db.commit()
    except Exception:
        # Sayaç yazılamadı diye kullanıcının cevabını kaybetmeyelim; sadece logla.
        logger.exception("OpenAI kullanım kaydı veritabanına yazılamadı.")
