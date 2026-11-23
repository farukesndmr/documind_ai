from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.database.connection import Base


class OpenAIUsage(Base):
    """Aylık OpenAI kullanım ve maliyet sayacı.

    Daha önce bu bilgi sunucu diskindeki bir JSON dosyasında tutuluyordu.
    Render gibi platformlarda disk kalıcı olmadığı için her deploy'da
    sıfırlanıyordu; artık veritabanında saklanıyor.
    """

    __tablename__ = "openai_usage"

    month = Column(String(7), primary_key=True)  # "2026-11"
    spent_usd = Column(Float, nullable=False, default=0.0)
    input_tokens = Column(BigInteger, nullable=False, default=0)
    output_tokens = Column(BigInteger, nullable=False, default=0)
    request_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
