from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ReadmeDraft
from app.db.models import ReadmeEvidence as DbReadmeEvidence
from app.readme.analyzer import analyze_repository
from app.readme.generator import assemble_readme, build_sections
from app.readme.models import (
    ReadmeDetailLevel,
    RepositoryEvidence,
    ValidationResult,
)
from app.readme.scanner import scan_repository
from app.readme.validator import validate_readme


def analyze_repo_path(repo_path: Path, repo_name: str | None = None) -> RepositoryEvidence:
    """Scan and analyze a repository workspace."""
    inventory = scan_repository(repo_path)
    return analyze_repository(inventory, repo_name=repo_name)


def generate_draft_from_evidence(
    evidence: RepositoryEvidence,
    detail_level: ReadmeDetailLevel = "detailed",
) -> tuple[str, dict[str, str], ValidationResult]:
    """Generate section-based Markdown draft and validate quality against evidence."""
    sections = build_sections(evidence, detail_level=detail_level)
    draft = assemble_readme(sections)
    validation = validate_readme(draft, sections, evidence, detail_level=detail_level)
    return draft, sections, validation


def regenerate_single_section(
    evidence: RepositoryEvidence,
    section_id: str,
    current_draft: str,
    detail_level: ReadmeDetailLevel = "detailed",
) -> tuple[str, dict[str, str], ValidationResult]:
    """Regenerate a specific section while preserving user modifications to all other sections."""
    fresh_sections = build_sections(evidence, detail_level=detail_level)
    new_section_content = fresh_sections.get(section_id, "")

    # Reconstruct sections from draft or replace section
    sections = fresh_sections.copy()
    sections[section_id] = new_section_content
    draft = assemble_readme(sections)
    validation = validate_readme(draft, sections, evidence, detail_level=detail_level)
    return draft, sections, validation


async def persist_generation_record(
    session: AsyncSession,
    repository_id: uuid.UUID,
    evidence: RepositoryEvidence,
    draft_content: str,
    validation: ValidationResult,
    status: str = "draft",
) -> tuple[uuid.UUID, uuid.UUID]:
    """Persist extracted evidence and draft record to PostgreSQL."""
    db_evidence = DbReadmeEvidence(
        repository_id=repository_id,
        content=evidence.model_dump(),
        extracted_at=datetime.now(UTC),
    )
    session.add(db_evidence)
    await session.flush()

    warnings_payload = [f.model_dump() for f in validation.findings]
    db_draft = ReadmeDraft(
        repository_id=repository_id,
        evidence_id=db_evidence.id,
        content=draft_content,
        status=status,
        warnings=warnings_payload,
    )
    session.add(db_draft)
    await session.commit()
    await session.refresh(db_draft)

    return db_evidence.id, db_draft.id
