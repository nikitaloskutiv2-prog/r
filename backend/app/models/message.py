from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Index, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    content = Column(String)  # ✅ Было: text
    sender_id = Column(Integer, ForeignKey("users.id"))  # ✅ Было: user_id
    chat_id = Column(Integer, ForeignKey("chats.id"))
    reply_to_id = Column(Integer,ForeignKey("messages.id"),nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)  # ✅ Новое поле
    is_read = Column(Boolean, default=False)  # ✅ Статус прочтения
    read_at = Column(DateTime, nullable=True)  # ✅ Время прочтения
    edited = Column(Boolean, default=False)
    file_id = Column(Integer,ForeignKey("files.id"),nullable=True)
    voice_duration = Column(Integer, nullable=True)
    waveform = Column(JSON, nullable=True)
    voice_played = Column(Boolean,default=False,nullable=False)

    # связи
    user = relationship("User", back_populates="messages")
    chat = relationship("Chat", back_populates="messages")
    file = relationship("File")

    reply_to = relationship("Message",remote_side=[id])
    # 🔹 Индекс для быстрого поиска непрочитанных сообщений
    __table_args__ = (
        Index(
            "idx_chat_unread",
            "chat_id",
            "is_read"
        ),
        {
            "sqlite_autoincrement": True
        }
    )