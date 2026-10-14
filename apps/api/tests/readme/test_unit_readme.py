from __future__ import annotations

from pathlib import Path

import pytest

from app.readme.analyzer import analyze_repository
from app.readme.generator import build_sections
from app.readme.models import RepositoryEvidence
from app.readme.scanner import scan_repository
from app.readme.service import regenerate_single_section
from app.readme.validator import validate_readme
from tests.readme.fixtures_builder import create_all_fixtures


@pytest.fixture(scope="session")
def fixtures_map(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    tmp_dir = tmp_path_factory.mktemp("repos")
    return create_all_fixtures(tmp_dir)


def test_scanner_inventory(fixtures_map: dict[str, Path]) -> None:
    inv = scan_repository(fixtures_map["python_fastapi"])
    assert "pyproject.toml" in [Path(f).name for f in inv.manifest_files]
    assert "app/main.py" in inv.files
    assert inv.language_counts.get("Python", 0) > 0


def test_python_fastapi_inference(fixtures_map: dict[str, Path]) -> None:
    inv = scan_repository(fixtures_map["python_fastapi"])
    evidence = analyze_repository(inv, "fastapi-demo")

    assert "FastAPI" in evidence.frameworks
    assert "SQLAlchemy (ORM)" in evidence.database_technologies
    assert any(c.command == "pytest" for c in evidence.commands)

    # Verify environment variables were extracted and sanitized
    secret_var = next((v for v in evidence.environment_variables if v.name == "SECRET_KEY"), None)
    assert secret_var is not None
    assert secret_var.example_value == "******** (secret)"


def test_python_uv_poetry(fixtures_map: dict[str, Path]) -> None:
    inv = scan_repository(fixtures_map["python_uv_poetry"])
    evidence = analyze_repository(inv, "uv-poetry")

    # Should detect uv package manager
    assert "uv" in evidence.package_managers
    assert any("uv sync" in c.command for c in evidence.commands)


def test_nextjs_typescript(fixtures_map: dict[str, Path]) -> None:
    inv = scan_repository(fixtures_map["nextjs_ts"])
    evidence = analyze_repository(inv, "nextjs-dashboard")

    assert "Next.js" in evidence.frameworks
    assert "React" in evidence.frameworks
    assert "npm" in evidence.package_managers
    assert any(c.command == "npm run dev" for c in evidence.commands)
    assert any(c.command == "npm run build" for c in evidence.commands)
    assert any(c.command in {"npm test", "npm run test"} for c in evidence.commands)


def test_go_module_inference(fixtures_map: dict[str, Path]) -> None:
    inv = scan_repository(fixtures_map["go"])
    evidence = analyze_repository(inv, "go-service")

    assert "Go" in evidence.languages
    assert any("go mod download" in c.command for c in evidence.commands)
    assert any("go test" in c.command for c in evidence.commands)


def test_rust_cargo_inference(fixtures_map: dict[str, Path]) -> None:
    inv = scan_repository(fixtures_map["rust"])
    evidence = analyze_repository(inv, "rust-engine")

    assert "Rust" in evidence.languages
    assert any("cargo build" in c.command for c in evidence.commands)
    assert any("cargo test" in c.command for c in evidence.commands)


def test_java_and_cmake_inference(fixtures_map: dict[str, Path]) -> None:
    inv_java = scan_repository(fixtures_map["java_gradle"])
    evidence_java = analyze_repository(inv_java)
    assert any("./gradlew build" in c.command for c in evidence_java.commands)

    inv_cmake = scan_repository(fixtures_map["cpp_cmake"])
    evidence_cmake = analyze_repository(inv_cmake)
    assert any("cmake --build" in c.command for c in evidence_cmake.commands)
    assert any("ctest" in c.command for c in evidence_cmake.commands)


def test_docker_compose_detection(fixtures_map: dict[str, Path]) -> None:
    inv = scan_repository(fixtures_map["docker_compose"])
    evidence = analyze_repository(inv)

    assert any(s.name == "web" for s in evidence.services)
    assert any(s.name == "api" for s in evidence.services)
    assert any("docker compose" in c.command for c in evidence.commands)


def test_monorepo_detection(fixtures_map: dict[str, Path]) -> None:
    inv = scan_repository(fixtures_map["monorepo"])
    evidence = analyze_repository(inv)

    assert evidence.is_monorepo is True
    assert len(evidence.monorepo_workspaces) > 0


def test_malformed_and_empty_handling(fixtures_map: dict[str, Path]) -> None:
    inv_broken = scan_repository(fixtures_map["conflicting_config"])
    # Should not crash on malformed JSON
    evidence_broken = analyze_repository(inv_broken)
    assert evidence_broken.name is not None

    inv_empty = scan_repository(fixtures_map["no_manifest"])
    evidence_empty = analyze_repository(inv_empty)
    assert len(evidence_empty.missing_evidence) > 0


def test_generator_detail_levels(fixtures_map: dict[str, Path]) -> None:
    inv = scan_repository(fixtures_map["nextjs_ts"])
    evidence = analyze_repository(inv)

    sec_detailed = build_sections(evidence, detail_level="detailed")
    sec_minimal = build_sections(evidence, detail_level="minimal")

    assert "architecture" in sec_detailed
    assert "troubleshooting" in sec_detailed
    assert "architecture" not in sec_minimal
    assert "overview" in sec_minimal


def test_validator_detects_secrets_and_unbalanced_fences() -> None:
    evidence = RepositoryEvidence(name="TestProj")
    sections = {"overview": "Hello"}

    # Leaked secret
    bad_draft = "Here is my secret token: ghp_123456789012345678901234567890123456"
    val = validate_readme(bad_draft, sections, evidence, detail_level="minimal")
    assert any(f.dimension == "security" for f in val.findings)
    assert val.is_valid is False

    # Unbalanced fences
    unbalanced_draft = "```bash\n npm install\n"
    val2 = validate_readme(unbalanced_draft, sections, evidence, detail_level="minimal")
    assert any(f.dimension == "syntax" for f in val2.findings)


def test_section_regeneration(fixtures_map: dict[str, Path]) -> None:
    inv = scan_repository(fixtures_map["python_fastapi"])
    evidence = analyze_repository(inv)

    custom_draft = "# Custom Title\n\nUser customized text here.\n\n---\n\n## Testing\nold tests"
    _, sections, val = regenerate_single_section(
        evidence=evidence,
        section_id="testing",
        current_draft=custom_draft,
        detail_level="detailed",
    )

    assert "pytest" in sections["testing"]
    assert val.score > 0
