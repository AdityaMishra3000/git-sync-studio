from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.readme.models import RepositoryEvidence
from app.readme.service import analyze_repo_path, generate_draft_from_evidence


def extract_evidence(repo_path: Path) -> dict[str, Any]:
    """Legacy compatibility bridge to new typed evidence analyzer."""
    evidence = analyze_repo_path(repo_path)
    return evidence.model_dump()


def generate_readme(evidence: dict[str, Any] | RepositoryEvidence) -> str:
    """Legacy compatibility bridge to new section-based generator."""
    if isinstance(evidence, dict):
        try:
            typed_evidence = RepositoryEvidence.model_validate(evidence)
        except (ValueError, TypeError, ValidationError):
            typed_evidence = RepositoryEvidence(name="Project")
    else:
        typed_evidence = evidence

    draft, _, _ = generate_draft_from_evidence(typed_evidence, detail_level="detailed")
    return draft
