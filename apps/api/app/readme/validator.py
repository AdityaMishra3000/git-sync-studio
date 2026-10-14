from __future__ import annotations

import re

from app.readme.models import (
    ReadmeDetailLevel,
    RepositoryEvidence,
    ValidationFinding,
    ValidationResult,
)

SECRET_PATTERNS = [
    (r"ghp_[0-9a-zA-Z]{36}", "GitHub Personal Access Token"),
    (r"gho_[0-9a-zA-Z]{36}", "GitHub OAuth Access Token"),
    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI API Secret Key"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"-----BEGIN (?:RSA )?PRIVATE KEY-----", "Private Key"),
    (
        r"eyJ[a-zA-Z0-9_-]{20,}\.eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}",
        "JSON Web Token (JWT)",
    ),
]

REQUIRED_SECTIONS: dict[ReadmeDetailLevel, list[str]] = {
    "detailed": [
        "overview",
        "features",
        "architecture",
        "tech_stack",
        "prerequisites",
        "installation",
        "configuration",
        "running",
        "api_reference",
        "testing",
        "troubleshooting",
        "license",
    ],
    "standard": [
        "overview",
        "features",
        "architecture",
        "prerequisites",
        "installation",
        "configuration",
        "running",
        "testing",
        "license",
    ],
    "minimal": [
        "overview",
        "prerequisites",
        "installation",
        "running",
        "testing",
        "license",
    ],
}


def validate_readme(
    draft: str,
    sections: dict[str, str],
    evidence: RepositoryEvidence,
    detail_level: ReadmeDetailLevel = "detailed",
) -> ValidationResult:
    """Validate documentation quality, security, and factual alignment with repository evidence."""
    findings: list[ValidationFinding] = []
    has_unverified = False

    # 1. Check for required sections
    expected = REQUIRED_SECTIONS.get(detail_level, REQUIRED_SECTIONS["detailed"])
    for req in expected:
        if req not in sections or not sections[req].strip():
            findings.append(
                ValidationFinding(
                    severity="error",
                    dimension="setup_completeness",
                    section=req,
                    explanation=f"Required section '{req}' is missing or empty.",
                    suggested_correction=f"Regenerate section '{req}' using extracted evidence.",
                )
            )

    # 2. Check for leaked secrets
    for pattern, sec_type in SECRET_PATTERNS:
        if re.search(pattern, draft):
            findings.append(
                ValidationFinding(
                    severity="error",
                    dimension="security",
                    section="global",
                    explanation=f"Potential secret detected in draft: {sec_type}.",
                    suggested_correction=(
                        "Replace secret token with safe placeholders or env references."
                    ),
                )
            )

    # 3. Check for balanced Markdown code fences
    fence_count = draft.count("```")
    if fence_count % 2 != 0:
        findings.append(
            ValidationFinding(
                severity="error",
                dimension="syntax",
                section="global",
                explanation="Unbalanced Markdown code fences (```) detected.",
                suggested_correction="Ensure code fences are closed with three backticks.",
            )
        )

    # 4. Check for duplicate Markdown headers
    headers = re.findall(r"^#{1,3}\s+(.+)$", draft, flags=re.MULTILINE)
    seen_headers = set()
    for h in headers:
        clean_h = h.strip().lower()
        if clean_h in seen_headers and clean_h not in {"overview", "notes"}:
            findings.append(
                ValidationFinding(
                    severity="warning",
                    dimension="accuracy",
                    section="headers",
                    explanation=f"Duplicate heading found: '{h}'.",
                    suggested_correction="Rename or consolidate identical sub-sections.",
                )
            )
        seen_headers.add(clean_h)

    # 5. Check for unverified execution commands
    for cmd in evidence.commands:
        if not cmd.verified or cmd.confidence != "verified":
            has_unverified = True
            findings.append(
                ValidationFinding(
                    severity="warning",
                    dimension="execution_reproducibility",
                    section="running",
                    explanation=(
                        f"Command '{cmd.command}' is inferred rather than directly verified."
                    ),
                    suggested_correction="Verify target execution entrypoint in manifests.",
                )
            )

    # 6. Check Mermaid syntax
    if "```mermaid" in draft:
        mermaid_blocks = re.findall(r"```mermaid\n(.*?)\n```", draft, flags=re.DOTALL)
        for b in mermaid_blocks:
            open_brackets = b.count("[") + b.count("(")
            close_brackets = b.count("]") + b.count(")")
            if open_brackets != close_brackets:
                findings.append(
                    ValidationFinding(
                        severity="error",
                        dimension="syntax",
                        section="architecture",
                        explanation="Unbalanced node brackets in Mermaid architecture diagram.",
                        suggested_correction="Verify bracket syntax in flowchart definition.",
                    )
                )

    # 7. Check for empty or placeholder content
    if "# Setup instructions here" in draft:
        findings.append(
            ValidationFinding(
                severity="warning",
                dimension="setup_completeness",
                section="installation",
                explanation="Placeholder text found in installation instructions.",
                suggested_correction="Inspect manifests to provide concrete setup commands.",
            )
        )

    # 8. Score Calculation
    error_count = sum(1 for f in findings if f.severity == "error")
    warning_count = sum(1 for f in findings if f.severity == "warning")

    acc_deduct = 5 * sum(1 for f in findings if f.dimension == "accuracy")
    setup_deduct = 5 * sum(1 for f in findings if f.dimension == "setup_completeness")
    exec_deduct = 5 * sum(1 for f in findings if f.dimension == "execution_reproducibility")

    dim_scores = {
        "accuracy": max(0, 20 - acc_deduct),
        "setup_completeness": max(0, 20 - setup_deduct),
        "execution_reproducibility": max(0, 20 - exec_deduct),
        "architectural_coverage": 15 if "architecture" in sections else 5,
        "usage_coverage": 10 if "api_reference" in sections or "running" in sections else 5,
        "configuration_completeness": 10 if "configuration" in sections else 5,
        "security": 5 if not any(f.dimension == "security" for f in findings) else 0,
    }

    total_score = sum(dim_scores.values())
    total_score = max(10, min(100, total_score - (error_count * 15) - (warning_count * 3)))

    return ValidationResult(
        score=total_score,
        dimension_scores=dim_scores,
        findings=findings,
        is_valid=error_count == 0,
        has_unverified_claims=has_unverified,
    )
