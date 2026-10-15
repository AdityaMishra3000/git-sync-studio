import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from celery.utils.log import get_task_logger

from app.core.config import get_settings
from app.db.models import Repository, RepositorySync
from app.db.session import create_db_engine, create_session_factory
from app.jobs.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="tasks.repo_sync.sync_repository")
def sync_repository(self: Any, repository_id: str) -> dict[str, str]:
    return asyncio.run(_sync_repository(repository_id))


async def _sync_repository(repository_id: str) -> dict[str, str]:
    settings = get_settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    async with session_factory() as session:
        repo_uuid = UUID(repository_id)
        repo = await session.get(Repository, repo_uuid)
        if not repo:
            logger.error(f"Repository {repository_id} not found")
            return {"status": "error", "detail": "not_found"}

        sync_record = RepositorySync(repository_id=repo_uuid, status="in_progress")
        session.add(sync_record)
        repo.sync_status = "in_progress"
        await session.commit()

        try:
            # Placeholder for actual GitHub API sync logic
            # e.g., metadata, file tree, workflows, etc.

            repo.sync_status = "success"
            repo.last_synced_at = datetime.now(UTC)
            sync_record.status = "success"
            sync_record.completed_at = datetime.now(UTC)
            await session.commit()
            return {"status": "success"}
        except Exception as e:
            logger.exception("Sync failed")
            repo.sync_status = "failed"
            sync_record.status = "failed"
            sync_record.completed_at = datetime.now(UTC)
            sync_record.error_message = str(e)
            await session.commit()
            raise e
        finally:
            await engine.dispose()
