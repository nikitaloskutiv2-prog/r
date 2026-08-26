from sqlalchemy import Column, Integer, String, Table, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# Таблица для связи многие-ко-многим
chat_members = Table(
    'chat_members',
    Base.metadata,
    Column('chat_id', Integer, ForeignKey('chats.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    is_private = Column(Boolean, default=True)  # ✅ Теперь Boolean импортирован
    name = Column(String, nullable=True)
    is_favorite = Column(Boolean, default=False, nullable=False)
    
    members = relationship("User", secondary=chat_members, back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")