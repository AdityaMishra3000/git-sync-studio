from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from celery.utils.log import get_task_logger

from app.core.config import get_settings
from app.db.models import Job, Repository
from app.db.session import create_db_engine, create_session_factory
from app.jobs.celery_app import celery_app
from app.readme.models import ReadmeDetailLevel
from app.readme.service import (
    analyze_repo_path,
    generate_draft_from_evidence,
    persist_generation_record,
)

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="tasks.readme.generate_documentation_job")
def generate_documentation_job(
    self,
    repo_path: str,
    repository_id: str | None = None,
    detail_level: ReadmeDetailLevel = "detailed",
) -> dict[str, str]:
    path_obj = Path(repo_path).resolve()
    repo_name = path_obj.name
    return asyncio.run(
        _run_generation_job(path_obj, repo_name, repository_id, detail_level, self.request.id)
    )


async def _run_generation_job(
    path_obj: Path,
    repo_name: str,
    repository_id: str | None,
    detail_level: ReadmeDetailLevel,
    task_id: str | None,
) -> dict[str, str]:
    settings = get_settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    async with session_factory() as session:
        job = Job(
            name=f"Generate README: {repo_name}",
            status="running",
            task_id=task_id,
            created_at=datetime.now(UTC),
        )
        session.add(job)
        await session.commit()

        try:
            evidence = await asyncio.to_thread(analyze_repo_path, path_obj)
            draft, sections, validation = generate_draft_from_evidence(
                evidence, detail_level=detail_level
            )

            if repository_id:
                repo_uuid = UUID(repository_id)
                repo = await session.get(Repository, repo_uuid)
                if repo:
                    await persist_generation_record(
                        session=session,
                        repository_id=repo_uuid,
                        evidence=evidence,
                        draft_content=draft,
                        validation=validation,
                        status="draft",
                    )

            job.status = "completed"
            job.result = {
                "score": validation.score,
                "sections_count": len(sections),
                "findings_count": len(validation.findings),
            }
            await session.commit()
            return {"status": "completed"}
        except Exception as e:
            logger.exception("README generation job failed")
            job.status = "failed"
            job.error = str(e)
            await session.commit()
            raise e
        finally:
            await engine.dispose()
