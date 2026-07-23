from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Access control
    role = Column(String(20), nullable=False, default="user")

    email_verified = Column(Boolean, nullable=False, default=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)

    email_verification_token_hash = Column(Text, nullable=True)
    email_verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    last_verification_email_sent_at = Column(DateTime(timezone=True), nullable=True)

    is_approved = Column(Boolean, nullable=False, default=False)
    approval_status = Column(String(20), nullable=False, default="pending")

    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Lifetime demo usage counters
    pdf_upload_count = Column(Integer, nullable=False, default=0)
    question_count = Column(Integer, nullable=False, default=0)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def can_use_app(self) -> bool:
        return self.email_verified

    @property
    def is_active(self) -> bool:
        return self.is_admin or self.can_use_app