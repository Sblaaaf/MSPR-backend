"""Pytest suite for the recommendation service.

All external dependencies (MongoDB, sklearn models) are mocked so tests
run without a live database or pre-trained pkl files.
"""
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Make the service package importable when running from this directory
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("RECOMMENDATION_API_KEY", "test-secret-key")

VALID_HEADERS = {"X-API-Key": "test-secret-key"}
INVALID_HEADERS = {"X-API-Key": "wrong-key"}

MOCK_DB_ID = "507f1f77bcf86cd799439011"


def _make_mock_db() -> AsyncMock:
    db = AsyncMock()
    db.recommendations.insert_one.return_value = MagicMock(inserted_id=MOCK_DB_ID)
    return db


@pytest_asyncio.fixture
async def client():
    mock_db = _make_mock_db()

    with (
        patch("main.connect_db", AsyncMock()),
        patch("main.close_db", AsyncMock()),
        patch("main.load_models", MagicMock()),
        patch("main.get_db", return_value=mock_db),
        patch("main.predict_nutrition", return_value=(2000.0, 175.0, 175.0, 66.7)),
        patch("main.predict_workout", return_value=("Cardio", "Moderate", 1.0, 4)),
    ):
        from main import app  # import after patches so lifespan uses mocks

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Authentication guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nutrition_missing_key(client: AsyncClient):
    resp = await client.post(
        "/recommend/nutrition",
        json={"age": 30, "weight_kg": 75, "height_m": 1.75, "sex": "male", "goal": "maintenance"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_nutrition_wrong_key(client: AsyncClient):
    resp = await client.post(
        "/recommend/nutrition",
        headers=INVALID_HEADERS,
        json={"age": 30, "weight_kg": 75, "height_m": 1.75, "sex": "male", "goal": "maintenance"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_workout_missing_key(client: AsyncClient):
    resp = await client.post(
        "/recommend/workout",
        json={"age": 25, "weight_kg": 70, "height_m": 1.75, "sex": "female"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /recommend/nutrition – happy paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nutrition_weight_loss(client: AsyncClient):
    resp = await client.post(
        "/recommend/nutrition",
        headers=VALID_HEADERS,
        json={"age": 30, "weight_kg": 80, "height_m": 1.75, "sex": "female", "goal": "weight_loss"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["daily_calories"] == 2000.0
    assert body["protein_g"] == 175.0
    assert body["carbs_g"] == 175.0
    assert body["fat_g"] == 66.7
    assert body["recommendation_id"] == MOCK_DB_ID


@pytest.mark.asyncio
async def test_nutrition_muscle_gain(client: AsyncClient):
    resp = await client.post(
        "/recommend/nutrition",
        headers=VALID_HEADERS,
        json={"age": 22, "weight_kg": 75, "height_m": 1.80, "sex": "male", "goal": "muscle_gain"},
    )
    assert resp.status_code == 200
    assert "daily_calories" in resp.json()


# ---------------------------------------------------------------------------
# POST /recommend/workout – happy paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_workout_basic(client: AsyncClient):
    resp = await client.post(
        "/recommend/workout",
        headers=VALID_HEADERS,
        json={"age": 28, "weight_kg": 70, "height_m": 1.70, "sex": "male"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["workout_type"] == "Cardio"
    assert body["intensity"] == "Moderate"
    assert body["duration_hours"] == 1.0
    assert body["frequency_per_week"] == 4
    assert body["recommendation_id"] == MOCK_DB_ID


@pytest.mark.asyncio
async def test_workout_with_optional_fields(client: AsyncClient):
    resp = await client.post(
        "/recommend/workout",
        headers=VALID_HEADERS,
        json={
            "age": 35,
            "weight_kg": 85,
            "height_m": 1.80,
            "sex": "female",
            "fat_percentage": 22.5,
            "resting_bpm": 65,
            "experience_level": 3,
        },
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nutrition_invalid_age(client: AsyncClient):
    resp = await client.post(
        "/recommend/nutrition",
        headers=VALID_HEADERS,
        json={"age": 5, "weight_kg": 70, "height_m": 1.75, "sex": "male", "goal": "maintenance"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_nutrition_invalid_goal(client: AsyncClient):
    resp = await client.post(
        "/recommend/nutrition",
        headers=VALID_HEADERS,
        json={"age": 30, "weight_kg": 70, "height_m": 1.75, "sex": "male", "goal": "bulk"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_workout_invalid_sex(client: AsyncClient):
    resp = await client.post(
        "/recommend/workout",
        headers=VALID_HEADERS,
        json={"age": 30, "weight_kg": 70, "height_m": 1.75, "sex": "other"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_workout_height_out_of_range(client: AsyncClient):
    resp = await client.post(
        "/recommend/workout",
        headers=VALID_HEADERS,
        json={"age": 30, "weight_kg": 70, "height_m": 0.5, "sex": "male"},
    )
    assert resp.status_code == 422
