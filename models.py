from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    id_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)  # ✅ 관리자 여부 추가
    plan = Column(String, default="free")     # ✅ 플랜 정보 추가

    questions = relationship("Question", back_populates="user")
    settings = relationship("Setting", back_populates="user", uselist=False)
    subscription = relationship("Subscription", back_populates="user", uselist=False)

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="questions")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_type = Column(String, default="basic")
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)

    user = relationship("User", back_populates="subscription")

class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mic_enabled = Column(Boolean, default=True)
    font_size = Column(String, default="medium")

    user = relationship("User", back_populates="settings")
