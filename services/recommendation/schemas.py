from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Sex(str, Enum):
    male = "male"
    female = "female"


class Goal(str, Enum):
    weight_loss = "weight_loss"
    maintenance = "maintenance"
    muscle_gain = "muscle_gain"


class ExperienceLevel(int, Enum):
    beginner = 1
    intermediate = 2
    advanced = 3


class NutritionRequest(BaseModel):
    age: int = Field(..., ge=10, le=120)
    weight_kg: float = Field(..., ge=20.0, le=300.0)
    height_m: float = Field(..., ge=1.0, le=2.5)
    sex: Sex
    goal: Goal


class NutritionResponse(BaseModel):
    daily_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    recommendation_id: str


class WorkoutRequest(BaseModel):
    age: int = Field(..., ge=10, le=120)
    weight_kg: float = Field(..., ge=20.0, le=300.0)
    height_m: float = Field(..., ge=1.0, le=2.5)
    sex: Sex
    fat_percentage: Optional[float] = Field(None, ge=1.0, le=60.0)
    resting_bpm: Optional[int] = Field(None, ge=30, le=120)
    experience_level: ExperienceLevel = ExperienceLevel.beginner


class WorkoutResponse(BaseModel):
    workout_type: str
    intensity: str
    duration_hours: float
    frequency_per_week: int
    recommendation_id: str
