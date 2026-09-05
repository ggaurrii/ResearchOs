"""
Import every ORM model here so that:
  1. Alembic's autogenerate can discover them via Base.metadata.
  2. SQLAlchemy can resolve string-based relationship() forward references
     (e.g. Mapped["Workspace"]) across modules regardless of import order.
"""
from app.models.user import MentorProfile, RefreshToken, User  # noqa: F401
from app.models.workspace import ActivityLog, Workspace, WorkspaceMember  # noqa: F401
from app.models.paper import Paper  # noqa: F401

__all__ = [
    "User",
    "MentorProfile",
    "RefreshToken",
    "Workspace",
    "WorkspaceMember",
    "ActivityLog",
    "Paper",
]
