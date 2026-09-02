"""Settings behaviour.

Constructed with ``_env_file=None`` so the developer's local ``.env`` cannot
change the outcome of a test.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def test_cors_origins_are_parsed_from_a_comma_separated_string() -> None:
    settings = _settings(cors_allow_origins=" http://a.test , http://b.test ,, ")

    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_log_level_is_normalised_to_upper_case() -> None:
    assert _settings(log_level="debug").log_level == "DEBUG"


def test_unknown_log_level_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _settings(log_level="chatty")


def test_unknown_environment_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _settings(app_env="staging")


def test_docs_are_disabled_in_production() -> None:
    assert _settings(app_env="production").docs_url is None
    assert _settings(app_env="development").docs_url == "/docs"


def test_database_password_is_never_logged() -> None:
    settings = _settings(
        database_url="postgresql+asyncpg://gitsync:sup3rs3cret@db.internal:5432/gitsync"
    )

    sanitised = settings.sanitised_database_url

    assert "sup3rs3cret" not in sanitised
    assert sanitised == "postgresql+asyncpg://gitsync:***@db.internal:5432/gitsync"


def test_secret_key_does_not_leak_through_repr() -> None:
    settings = _settings(secret_key="hunter2")

    assert "hunter2" not in repr(settings)
    assert settings.secret_key.get_secret_value() == "hunter2"


def test_sanitised_url_tolerates_a_url_without_credentials() -> None:
    assert _settings(database_url="sqlite+aiosqlite:///./local.db").sanitised_database_url == (
        "sqlite+aiosqlite:///./local.db"
    )
