from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ConfidenceLevel = Literal["verified", "inferred", "unknown", "conflicting"]
ReadmeDetailLevel = Literal["detailed", "standard", "minimal"]


class EvidenceProvenance(BaseModel):
    model_config = ConfigDict(extra="ignore")

    path: str
    symbol: str | None = None
    section: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    evidence_type: str = "source_code"
    confidence: ConfidenceLevel = "verified"
    detail: str | None = None


class CommandEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    category: str
    command: str
    working_dir: str = "."
    description: str = ""
    confidence: ConfidenceLevel = "verified"
    provenance: list[EvidenceProvenance] = Field(default_factory=list)
    verified: bool = True
    missing_prerequisites: list[str] = Field(default_factory=list)


class EnvVarEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    purpose: str
    required: bool = False
    default_value: str | None = None
    example_value: str | None = None
    provenance: list[EvidenceProvenance] = Field(default_factory=list)


class EndpointEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    path: str
    method: str
    summary: str | None = None
    auth_required: bool = False
    request_schema: dict[str, Any] | None = None
    response_schema: dict[str, Any] | None = None
    provenance: list[EvidenceProvenance] = Field(default_factory=list)


class ServiceEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    image_or_build: str
    ports: list[str] = Field(default_factory=list)
    role: str = ""
    depends_on: list[str] = Field(default_factory=list)
    healthcheck: str | None = None
    environment_keys: list[str] = Field(default_factory=list)
    provenance: list[EvidenceProvenance] = Field(default_factory=list)


class ArchitectureComponent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    role: str
    technologies: list[str] = Field(default_factory=list)
    entrypoint: str | None = None
    source_paths: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = "verified"


class RelationshipEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str
    target: str
    relationship_type: str
    description: str
    confidence: ConfidenceLevel = "verified"
    provenance: list[EvidenceProvenance] = Field(default_factory=list)


class TestEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    frameworks: list[str] = Field(default_factory=list)
    test_dirs: list[str] = Field(default_factory=list)
    test_files_sample: list[str] = Field(default_factory=list)
    test_commands: list[CommandEvidence] = Field(default_factory=list)
    has_unit_tests: bool = False
    has_integration_tests: bool = False
    has_e2e_tests: bool = False


class RepositoryEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0.0"
    name: str
    description: str | None = None
    relative_path: str = ""
    primary_language: str | None = None
    languages: dict[str, float] = Field(default_factory=dict)
    frameworks: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    is_monorepo: bool = False
    monorepo_workspaces: list[str] = Field(default_factory=list)
    entrypoints: list[str] = Field(default_factory=list)
    commands: list[CommandEvidence] = Field(default_factory=list)
    environment_variables: list[EnvVarEvidence] = Field(default_factory=list)
    architecture_components: list[ArchitectureComponent] = Field(default_factory=list)
    relationships: list[RelationshipEvidence] = Field(default_factory=list)
    endpoints: list[EndpointEvidence] = Field(default_factory=list)
    database_technologies: list[str] = Field(default_factory=list)
    database_migrations: str | None = None
    background_workers: list[str] = Field(default_factory=list)
    services: list[ServiceEvidence] = Field(default_factory=list)
    tests: TestEvidence = Field(default_factory=TestEvidence)
    ci_cd_workflows: list[str] = Field(default_factory=list)
    license_type: str | None = None
    existing_docs: list[str] = Field(default_factory=list)
    troubleshooting_hints: list[dict[str, str]] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    extracted_at: str = ""


class ValidationFinding(BaseModel):
    model_config = ConfigDict(extra="ignore")

    severity: Literal["error", "warning", "info"]
    dimension: str
    section: str
    explanation: str
    suggested_correction: str


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    score: int
    dimension_scores: dict[str, int] = Field(default_factory=dict)
    findings: list[ValidationFinding] = Field(default_factory=list)
    is_valid: bool = True
    has_unverified_claims: bool = False


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repo_path: str
    repository_id: str | None = None
    detail_level: ReadmeDetailLevel = "detailed"


class RegenerateSectionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repo_path: str
    section_id: str
    current_draft: str
    detail_level: ReadmeDetailLevel = "detailed"


class SaveRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repo_path: str
    content: str
    repository_id: str | None = None
    status: str = "draft"


class ApproveRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repo_path: str
    repository_id: str | None = None
    content: str
