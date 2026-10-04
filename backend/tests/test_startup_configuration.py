import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect

from config import Settings, settings
from database import Base
from main import app


def test_required_test_configuration_and_health_startup_are_available():
    assert settings.ENVIRONMENT == "test"
    assert settings.DATABASE_URL.startswith("sqlite:///")
    assert settings.SECRET_KEY == "pytest-secret-key-with-sufficient-entropy"

    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_optional_ai_provider_configuration_can_be_absent():
    configured = Settings(
        _env_file=None,
        DATABASE_URL="sqlite:///:memory:",
        ENVIRONMENT="test",
        SECRET_KEY="test-secret",
        HF_TOKEN=None,
        GEMINI_API_KEY=None,
    )
    assert configured.HF_TOKEN is None
    assert configured.GEMINI_API_KEY is None


def test_production_rejects_the_default_secret_predictably():
    with pytest.raises(ValidationError, match="SECRET_KEY must be configured in production"):
        Settings(
            _env_file=None,
            DATABASE_URL="sqlite:///:memory:",
            ENVIRONMENT="production",
            SECRET_KEY="mindscreen-default-secret-change-in-production",
        )

    with pytest.raises(ValidationError, match="SECRET_KEY must be configured in production"):
        Settings(
            _env_file=None,
            DATABASE_URL="sqlite:///:memory:",
            ENVIRONMENT="production",
            SECRET_KEY="your-super-secret-key-here-change-this",
        )

    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            _env_file=None,
            DATABASE_URL="sqlite:///:memory:",
            ENVIRONMENT="production",
            SECRET_KEY="too-short",
        )


def test_production_rejects_wildcard_cors_and_accepts_explicit_origins():
    strong_secret = "production-secret-with-at-least-32-characters"
    with pytest.raises(ValidationError, match="ALLOWED_ORIGINS cannot contain a wildcard"):
        Settings(
            _env_file=None,
            DATABASE_URL="sqlite:///:memory:",
            ENVIRONMENT="production",
            SECRET_KEY=strong_secret,
            ALLOWED_ORIGINS="*",
        )

    configured = Settings(
        _env_file=None,
        DATABASE_URL="sqlite:///:memory:",
        ENVIRONMENT="production",
        SECRET_KEY=strong_secret,
        ALLOWED_ORIGINS="https://mindscreen.vercel.app",
    )
    assert configured.ALLOWED_ORIGINS == "https://mindscreen.vercel.app"


def test_existing_create_all_schema_initialization_succeeds():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    table_names = set(inspect(test_engine).get_table_names())
    assert {"users", "assessments", "mood_logs"}.issubset(table_names)
