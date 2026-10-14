from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Repository
from app.repos.schemas import RepositoryCreate


async def get_repositories(session: AsyncSession) -> list[Repository]:
    result = await session.execute(select(Repository).order_by(Repository.name))
    return list(result.scalars().all())


async def get_repository(session: AsyncSession, repo_id: UUID) -> Repository:
    repo = await session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


async def create_repository(session: AsyncSession, repo_in: RepositoryCreate) -> Repository:
    result = await session.execute(
        select(Repository).where(Repository.github_repo_id == repo_in.github_repo_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Repository already connected")

    repo = Repository(**repo_in.model_dump())
    session.add(repo)
    await session.commit()
    await session.refresh(repo)
    return repo


async def delete_repository(session: AsyncSession, repo_id: UUID) -> None:
    repo = await get_repository(session, repo_id)
    await session.delete(repo)
    await session.commit()
