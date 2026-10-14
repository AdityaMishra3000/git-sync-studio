from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.core.logging import get_logger
from app.db.models import ReadmeDraft, Repository
from app.readme.models import (
    ApproveRequest,
    GenerateRequest,
    ReadmeDetailLevel,
    RegenerateSectionRequest,
    RepositoryEvidence,
    SaveRequest,
)
from app.readme.service import (
    analyze_repo_path,
    generate_draft_from_evidence,
    persist_generation_record,
    regenerate_single_section,
)
from app.readme.validator import validate_readme

logger = get_logger("app.readme.router")
router = APIRouter(prefix="/readme", tags=["readme"])


def _resolve_safe_path(raw_path: str) -> Path:
    p = Path(raw_path).resolve()
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=404, detail=f"Repository path not found: {raw_path}")
    return p


@router.post("/analyze", response_model=RepositoryEvidence)
async def analyze_endpoint(req: GenerateRequest) -> RepositoryEvidence:
    """Extract grounded technical evidence from a repository workspace."""
    safe_path = _resolve_safe_path(req.repo_path)
    return analyze_repo_path(safe_path)


@router.post("/generate")
async def generate_readme_endpoint(
    req: GenerateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Generate evidence-grounded README draft with validation findings and section breakdown."""
    safe_path = _resolve_safe_path(req.repo_path)
    evidence = analyze_repo_path(safe_path)
    draft, sections, validation = generate_draft_from_evidence(
        evidence, detail_level=req.detail_level
    )

    draft_id = None
    if req.repository_id:
        try:
            repo_uuid = uuid.UUID(req.repository_id)
            repo_res = await session.execute(select(Repository).where(Repository.id == repo_uuid))
            if repo_res.scalar_one_or_none():
                _, d_id = await persist_generation_record(
                    session=session,
                    repository_id=repo_uuid,
                    evidence=evidence,
                    draft_content=draft,
                    validation=validation,
                    status="draft",
                )
                draft_id = str(d_id)
        except (ValueError, SQLAlchemyError) as err:
            logger.warning("readme.persist_draft_failed", error=str(err))

    return {
        "draft": draft,
        "sections": sections,
        "evidence": evidence.model_dump(),
        "validation": validation.model_dump(),
        "warnings": [f.model_dump() for f in validation.findings],
        "status": "draft",
        "draft_id": draft_id,
    }


@router.post("/regenerate-section")
async def regenerate_section_endpoint(
    req: RegenerateSectionRequest,
) -> dict[str, Any]:
    """Regenerate a specific section while preserving manual edits in other sections."""
    safe_path = _resolve_safe_path(req.repo_path)
    evidence = analyze_repo_path(safe_path)
    draft, sections, validation = regenerate_single_section(
        evidence=evidence,
        section_id=req.section_id,
        current_draft=req.current_draft,
        detail_level=req.detail_level,
    )

    return {
        "draft": draft,
        "sections": sections,
        "validation": validation.model_dump(),
        "warnings": [f.model_dump() for f in validation.findings],
    }


@router.post("/validate")
async def validate_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a modified draft against evidence."""
    draft = payload.get("draft", "")
    evidence_data = payload.get("evidence", {})
    detail_level: ReadmeDetailLevel = payload.get("detail_level", "detailed")

    try:
        evidence = RepositoryEvidence.model_validate(evidence_data)
    except (ValueError, TypeError, ValidationError):
        evidence = RepositoryEvidence(name="Project")

    sections = payload.get("sections", {})
    validation = validate_readme(draft, sections, evidence, detail_level=detail_level)
    return validation.model_dump()


@router.post("/save")
async def save_readme(
    req: SaveRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """Save the edited README draft to repository file and update database record."""
    safe_path = _resolve_safe_path(req.repo_path)
    readme_path = safe_path / "README.md"
    readme_path.write_text(req.content, encoding="utf-8")

    if req.repository_id:
        try:
            repo_uuid = uuid.UUID(req.repository_id)
            res = await session.execute(
                select(ReadmeDraft)
                .where(ReadmeDraft.repository_id == repo_uuid)
                .order_by(ReadmeDraft.created_at.desc())
                .limit(1)
            )
            draft = res.scalar_one_or_none()
            if draft:
                draft.content = req.content
                draft.status = req.status
                await session.commit()
        except (ValueError, SQLAlchemyError) as err:
            logger.warning("readme.save_draft_record_failed", error=str(err))

    return {"status": "success", "message": "README.md saved to repository"}


@router.post("/approve")
async def approve_readme(
    req: ApproveRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """Explicitly approve a README draft and mark it approved in the database."""
    safe_path = _resolve_safe_path(req.repo_path)
    readme_path = safe_path / "README.md"
    readme_path.write_text(req.content, encoding="utf-8")

    if req.repository_id:
        try:
            repo_uuid = uuid.UUID(req.repository_id)
            res = await session.execute(
                select(ReadmeDraft)
                .where(ReadmeDraft.repository_id == repo_uuid)
                .order_by(ReadmeDraft.created_at.desc())
                .limit(1)
            )
            draft = res.scalar_one_or_none()
            if draft:
                draft.status = "approved"
                await session.commit()
        except (ValueError, SQLAlchemyError) as err:
            logger.warning("readme.approve_draft_record_failed", error=str(err))

    return {"status": "approved", "message": "README draft has been verified and approved"}
