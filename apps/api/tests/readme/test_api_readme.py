from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.core.dependencies import get_db_session
from tests.readme.fixtures_builder import create_all_fixtures


@pytest.fixture(scope="session")
def fixtures_map(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    tmp_dir = tmp_path_factory.mktemp("api_repos")
    return create_all_fixtures(tmp_dir)


@pytest.fixture(autouse=True)
def override_db_dependency(app: FastAPI):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_session.commit = AsyncMock()

    async def _mock_get_db_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = _mock_get_db_session
    yield
    app.dependency_overrides.pop(get_db_session, None)


async def test_api_readme_analyze(client: AsyncClient, fixtures_map: dict[str, Path]) -> None:
    repo_path = str(fixtures_map["python_fastapi"])
    resp = await client.post("/api/v1/readme/analyze", json={"repo_path": repo_path})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "python_fastapi_pyproject"
    assert "FastAPI" in data["frameworks"]


async def test_api_readme_generate(client: AsyncClient, fixtures_map: dict[str, Path]) -> None:
    repo_path = str(fixtures_map["nextjs_ts"])
    resp = await client.post(
        "/api/v1/readme/generate",
        json={"repo_path": repo_path, "detail_level": "detailed"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "draft" in data
    assert "sections" in data
    assert "validation" in data
    assert data["validation"]["score"] > 50
    assert "Next.js" in data["draft"]


async def test_api_readme_regenerate_section(
    client: AsyncClient, fixtures_map: dict[str, Path]
) -> None:
    repo_path = str(fixtures_map["nextjs_ts"])
    resp = await client.post(
        "/api/v1/readme/regenerate-section",
        json={
            "repo_path": repo_path,
            "section_id": "running",
            "current_draft": "# Existing Draft",
            "detail_level": "detailed",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "running" in data["sections"]


async def test_api_readme_validate(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/readme/validate",
        json={
            "draft": "Here is a secret: ghp_111122223333444455556666777788889999",
            "evidence": {"name": "TestRepo"},
            "sections": {},
            "detail_level": "minimal",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is False
    assert any(f["dimension"] == "security" for f in data["findings"])


async def test_api_readme_save_and_approve(
    client: AsyncClient, fixtures_map: dict[str, Path]
) -> None:
    repo_path = str(fixtures_map["python_requirements"])

    save_resp = await client.post(
        "/api/v1/readme/save",
        json={"repo_path": repo_path, "content": "# Saved Title\n\nContent."},
    )
    assert save_resp.status_code == 200
    assert (fixtures_map["python_requirements"] / "README.md").exists()
    assert "Saved Title" in (fixtures_map["python_requirements"] / "README.md").read_text()

    approve_resp = await client.post(
        "/api/v1/readme/approve",
        json={"repo_path": repo_path, "content": "# Approved Title\n\nApproved."},
    )
    assert approve_resp.status_code == 200
    assert "Approved Title" in (fixtures_map["python_requirements"] / "README.md").read_text()


async def test_api_readme_not_found(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/readme/generate",
        json={"repo_path": "/path/does/not/exist/ever"},
    )
    assert resp.status_code == 404
