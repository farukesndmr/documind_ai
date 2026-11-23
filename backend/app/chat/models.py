from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database.connection import Base


class ChatMessage(Base):
    """Bir kullanıcının bir belgeyle yaptığı sohbetin tek bir mesajı.

    Her (kullanıcı, belge) çifti için tek bir sohbet akışı vardır.
    Belge silinince mesajları da veritabanı tarafından silinir (CASCADE).
    """

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(16), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    # Asistan mesajlarında cevabın dayandığı kaynak parçalar (SourceChunk listesi).
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
