from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RepositoryBase(BaseModel):
    owner: str
    name: str
    github_repo_id: int
    default_branch: str = "main"
    visibility: str = "private"


class RepositoryCreate(RepositoryBase):
    installation_id: UUID | None = None


class RepositoryRead(RepositoryBase):
    id: UUID
    sync_status: str
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
