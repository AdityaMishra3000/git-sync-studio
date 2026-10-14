import asyncio
import uuid
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db.models import Repository, PullRequest
import os

# Use the Docker host mapping for the script running inside host/workspace
DATABASE_URL = "postgresql+asyncpg://gitsync:gitsync_dev_password@postgres:5432/gitsync"
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    async with async_session() as session:
        # Get first repo
        result = await session.execute(select(Repository).limit(1))
        repo = result.scalar_one_or_none()
        
        if not repo:
            print("No repos found to attach PRs to.")
            return

        print(f"Injecting mock PRs into repo: {repo.name}")

        mock_prs = [
            PullRequest(
                repository_id=repo.id,
                number=101,
                title="Refactor: Extract evidence gathering into ML pipeline",
                author="adityam",
                status="open",
                opened_at=datetime.now(UTC),
                changed_files=12,
                additions=1450,
                deletions=230,
            ),
            PullRequest(
                repository_id=repo.id,
                number=102,
                title="Fix: Resolve memory leak in Celery worker",
                author="adityam",
                status="open",
                opened_at=datetime.now(UTC),
                changed_files=2,
                additions=45,
                deletions=12,
            ),
            PullRequest(
                repository_id=repo.id,
                number=103,
                title="Chore: Update dependencies for Next.js 15",
                author="dependabot",
                status="open",
                opened_at=datetime.now(UTC),
                changed_files=5,
                additions=100,
                deletions=100,
            ),
        ]
        
        session.add_all(mock_prs)
        await session.commit()
        print("Mock PRs seeded successfully.")

asyncio.run(seed())
