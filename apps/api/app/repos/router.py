from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.db.models import PullRequest
from app.repos import service
from app.repos.schemas import RepositoryCreate, RepositoryRead

router = APIRouter(prefix="/repos", tags=["repositories"])


@router.get("", response_model=list[RepositoryRead])
async def list_repositories(
    session: AsyncSession = Depends(get_db_session),
) -> list[RepositoryRead]:
    repos = await service.get_repositories(session)
    return [RepositoryRead.model_validate(r) for r in repos]


@router.get("/{repo_id}", response_model=RepositoryRead)
async def get_repository(
    repo_id: UUID, session: AsyncSession = Depends(get_db_session)
) -> RepositoryRead:
    repo = await service.get_repository(session, repo_id)
    return RepositoryRead.model_validate(repo)


@router.post("", response_model=RepositoryRead, status_code=201)
async def create_repository(
    repo_in: RepositoryCreate, session: AsyncSession = Depends(get_db_session)
) -> RepositoryRead:
    repo = await service.create_repository(session, repo_in)
    return RepositoryRead.model_validate(repo)


@router.get("/{repo_id}/prs")
async def list_prs(
    repo_id: UUID, session: AsyncSession = Depends(get_db_session)
) -> list[dict[str, Any]]:
    result = await session.execute(select(PullRequest).where(PullRequest.repository_id == repo_id))
    prs = result.scalars().all()
    return [
        {
            "id": str(pr.id),
            "title": pr.title,
            "state": pr.status,
            "author": pr.author,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files,
        }
        for pr in prs
    ]


@router.delete("/{repo_id}", status_code=204)
async def delete_repository(
    repo_id: UUID, session: AsyncSession = Depends(get_db_session)
) -> None:
    await service.delete_repository(session, repo_id)
