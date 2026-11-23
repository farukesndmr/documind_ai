"""Mevcut tablolara geriye uyumlu (yalnızca ekleme yapan) şema güncellemeleri.

`Base.metadata.create_all` yeni tabloları oluşturur ama var olan tablolara
yeni kolon eklemez. Alembic'e geçene kadar, eklenen kolon ve indeksleri
burada idempotent (tekrar çalıştırılınca zarar vermeyen) SQL ile uyguluyoruz.
Hiçbir komut veri silmez veya değiştirmez.
"""

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine


logger = logging.getLogger(__name__)

UPGRADES = [
    "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS page_number INTEGER",
    "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100)",
    "CREATE INDEX IF NOT EXISTS ix_document_chunks_document_id "
    "ON document_chunks (document_id)",
    "CREATE INDEX IF NOT EXISTS ix_documents_owner_id ON documents (owner_id)",
]


def run_schema_upgrades(engine: Engine) -> None:
    for statement in UPGRADES:
        try:
            with engine.begin() as connection:
                connection.execute(text(statement))
        except Exception:
            logger.exception("Şema güncellemesi uygulanamadı: %s", statement)
