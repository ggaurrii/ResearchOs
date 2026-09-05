"""
User Management models — matches the Database Design Document, Section 3.3
(users, mentor_profiles, refresh_tokens).
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('student','researcher','mentor','admin')", name="ck_users_role"),
        CheckConstraint("status IN ('active','locked','deactivated')", name="ck_users_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    institution: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    failed_login_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    mentor_profile: Mapped[Optional["MentorProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class MentorProfile(Base):
    __tablename__ = "mentor_profiles"
    __table_args__ = (
        CheckConstraint(
            "availability IN ('available','limited','unavailable')", name="ck_mentor_availability"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    research_interests: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    expertise: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    publications_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    availability: Mapped[str] = mapped_column(String(20), nullable=False, default="available")
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="mentor_profile")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
