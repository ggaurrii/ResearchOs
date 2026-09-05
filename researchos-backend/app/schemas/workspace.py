import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Visibility = Literal["private", "team", "public"]


class WorkspaceCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    domain: Optional[str] = Field(default=None, max_length=150)
    description: Optional[str] = None
    visibility: Visibility = "private"


class WorkspaceUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    domain: Optional[str] = Field(default=None, max_length=150)
    description: Optional[str] = None
    visibility: Optional[Visibility] = None


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    domain: Optional[str] = None
    description: Optional[str] = None
    visibility: Visibility
    status: str
    created_at: datetime
    updated_at: datetime


class WorkspaceMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    role_in_project: Optional[str] = None
    permission_level: Literal["owner", "editor", "viewer"]
    joined_at: datetime


class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID
    event_type: str
    event_data: Optional[dict[str, Any]] = None
    created_at: datetime
