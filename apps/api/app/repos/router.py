from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.repos import service
from app.repos.schemas import RepositoryCreate, RepositoryRead

router = APIRouter(prefix="/repos", tags=["repositories"])


@router.get("", response_model=list[RepositoryRead])
async def list_repositories(
    session: AsyncSession = Depends(get_db_session),
) -> list[RepositoryRead]:
    return await service.get_repositories(session)


@router.get("/{repo_id}", response_model=RepositoryRead)
async def get_repository(
    repo_id: UUID, session: AsyncSession = Depends(get_db_session)
) -> RepositoryRead:
    return await service.get_repository(session, repo_id)


@router.post("", response_model=RepositoryRead, status_code=201)
async def create_repository(
    repo_in: RepositoryCreate, session: AsyncSession = Depends(get_db_session)
) -> RepositoryRead:
    return await service.create_repository(session, repo_in)



@router.get("/{repo_id}/prs")
async def list_prs(repo_id: UUID, session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    from sqlalchemy import select
    from app.db.models import PullRequest
    result = await session.execute(select(PullRequest).where(PullRequest.repository_id == repo_id))
    prs = result.scalars().all()
    return [{"id": str(pr.id), "title": pr.title, "state": pr.status, "author": pr.author, "additions": pr.additions, "deletions": pr.deletions, "changed_files": pr.changed_files} for pr in prs]
@router.delete("/{repo_id}", status_code=204)
async def delete_repository(repo_id: UUID, session: AsyncSession = Depends(get_db_session)) -> None:
    await service.delete_repository(session, repo_id)
