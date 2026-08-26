from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    login = Column(String, unique=True, index=True, nullable=True)
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    usernameid = Column(String, unique=True, index=True, nullable=True)
    accountid = Column(String, unique=True, index=True, nullable=False)

    bio = Column(String, default="")
    birthday = Column(String, default="")
    avatar = Column(String, nullable=True)

    status = Column(String, default="offline")
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # отношения
    messages = relationship("Message", back_populates="user")
    chats = relationship("Chat", secondary="chat_members", back_populates="members")