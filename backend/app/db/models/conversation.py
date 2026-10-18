from typing import Optional, Dict, Any
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.schemas.common import Channel


class ConversationSession(Base, TimestampMixin):
    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    channel: Mapped[str] = mapped_column(String(20), default=Channel.IVR.value, nullable=False)
    case_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    state: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    context_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    last_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
