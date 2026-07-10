from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    notes: Mapped[list["ClinicalNote"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    chats: Mapped[list["Chat"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__ = "user_sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    extractor_backend: Mapped[str] = mapped_column(String(64), nullable=False)
    warnings_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="notes")
    reasoning_output: Mapped["ReasoningOutput"] = relationship(back_populates="note", uselist=False, cascade="all, delete-orphan")
    chats: Mapped[list["Chat"]] = relationship(back_populates="note")


class ReasoningOutput(Base):
    __tablename__ = "reasoning_outputs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    note_id: Mapped[str] = mapped_column(ForeignKey("clinical_notes.id", ondelete="CASCADE"), unique=True, nullable=False)
    timeline_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    differentials_json: Mapped[list] = mapped_column(JSON, default=list)
    contradictions_json: Mapped[list] = mapped_column(JSON, default=list)
    confidence_json: Mapped[list] = mapped_column(JSON, default=list)
    reasoning_trace_json: Mapped[list] = mapped_column(JSON, default=list)
    orchestration_trace_json: Mapped[list] = mapped_column(JSON, default=list)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    note: Mapped[ClinicalNote] = relationship(back_populates="reasoning_output")


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    note_id: Mapped[str] = mapped_column(ForeignKey("clinical_notes.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="chats")
    note: Mapped[ClinicalNote] = relationship(back_populates="chats")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="chat", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    chat_id: Mapped[str] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)  # 'user', 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_name: Mapped[str] = mapped_column(String(255), nullable=True)
    media_content: Mapped[str] = mapped_column(Text, nullable=True)  # Extracted text context
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat: Mapped[Chat] = relationship(back_populates="messages")

