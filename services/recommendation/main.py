import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader

from database import close_db, connect_db, get_db
from model import load_models, predict_nutrition, predict_workout
from schemas import (
    NutritionRequest,
    NutritionResponse,
    WorkoutRequest,
    WorkoutResponse,
)

_API_KEY = os.getenv("RECOMMENDATION_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def _verify_api_key(key: str = Security(_api_key_header)) -> str:
    if not _API_KEY or key != _API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return key


@asynccontextmanager
async def _lifespan(app: FastAPI):
    await connect_db()
    load_models()
    yield
    await close_db()


app = FastAPI(
    title="HealthAI Recommendation Service",
    version="1.0.0",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "recommendation"}


@app.post("/recommend/nutrition", response_model=NutritionResponse, tags=["recommend"])
async def recommend_nutrition(
    req: NutritionRequest,
    _: str = Depends(_verify_api_key),
):
    calories, protein, carbs, fat = predict_nutrition(
        req.age, req.weight_kg, req.height_m, req.sex, req.goal
    )
    db = get_db()
    result = await db.recommendations.insert_one(
        {
            "type": "nutrition",
            "input": req.model_dump(),
            "output": {
                "daily_calories": calories,
                "protein_g": protein,
                "carbs_g": carbs,
                "fat_g": fat,
            },
            "created_at": datetime.now(timezone.utc),
        }
    )
    return NutritionResponse(
        daily_calories=calories,
        protein_g=protein,
        carbs_g=carbs,
        fat_g=fat,
        recommendation_id=str(result.inserted_id),
    )


@app.post("/recommend/workout", response_model=WorkoutResponse, tags=["recommend"])
async def recommend_workout(
    req: WorkoutRequest,
    _: str = Depends(_verify_api_key),
):
    workout_type, intensity, duration, frequency = predict_workout(
        req.age,
        req.weight_kg,
        req.height_m,
        req.sex,
        req.fat_percentage,
        req.resting_bpm,
        req.experience_level,
    )
    db = get_db()
    result = await db.recommendations.insert_one(
        {
            "type": "workout",
            "input": req.model_dump(),
            "output": {
                "workout_type": workout_type,
                "intensity": intensity,
                "duration_hours": duration,
                "frequency_per_week": frequency,
            },
            "created_at": datetime.now(timezone.utc),
        }
    )
    return WorkoutResponse(
        workout_type=workout_type,
        intensity=intensity,
        duration_hours=duration,
        frequency_per_week=frequency,
        recommendation_id=str(result.inserted_id),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
