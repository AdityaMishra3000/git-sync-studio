import asyncio
from typing import Any
from uuid import UUID

from celery.utils.log import get_task_logger

from app.core.config import get_settings
from app.db.models import Repository
from app.db.session import create_db_engine, create_session_factory
from app.jobs.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="tasks.pr_ingestion.ingest_historical_prs")
def ingest_historical_prs(
    self: Any, repository_id: str, cursor: str | None = None
) -> dict[str, str | None]:
    return asyncio.run(_ingest_historical_prs(repository_id, cursor))


async def _ingest_historical_prs(repository_id: str, cursor: str | None) -> dict[str, str | None]:
    settings = get_settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    async with session_factory() as session:
        repo_uuid = UUID(repository_id)
        repo = await session.get(Repository, repo_uuid)
        if not repo:
            logger.error(f"Repository {repository_id} not found")
            return {"status": "error", "detail": "not_found"}

        # Placeholder for pagination logic through GitHub PR API
        # e.g., fetching PRs, persisting them to the database

        # When paginating, if there's a next page, enqueue the next task
        # next_cursor = "..."
        # if next_cursor:
        #     ingest_historical_prs.delay(repository_id, next_cursor)

        return {"status": "success", "next_cursor": None}
