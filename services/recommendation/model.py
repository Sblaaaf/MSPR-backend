import os
import pickle
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

MODELS_DIR = Path(os.getenv("MODELS_DIR", "/app/models"))

_nutrition_model: RandomForestRegressor = None
_workout_model: RandomForestClassifier = None
_workout_encoder: LabelEncoder = None

_GOAL_TO_LEVEL = {"weight_loss": 1, "maintenance": 2, "muscle_gain": 3}
_INTENSITY_MAP = {1: "Low", 2: "Moderate", 3: "High"}
_DURATION_MAP = {1: 0.75, 2: 1.0, 3: 1.5}
_FREQ_MAP = {1: 3, 2: 4, 3: 5}


def load_models() -> None:
    global _nutrition_model, _workout_model, _workout_encoder

    nut_path = MODELS_DIR / "nutrition_model.pkl"
    work_path = MODELS_DIR / "workout_model.pkl"
    enc_path = MODELS_DIR / "workout_encoder.pkl"

    if not (nut_path.exists() and work_path.exists() and enc_path.exists()):
        from train import train_and_save
        train_and_save()

    with open(nut_path, "rb") as fh:
        _nutrition_model = pickle.load(fh)
    with open(work_path, "rb") as fh:
        _workout_model = pickle.load(fh)
    with open(enc_path, "rb") as fh:
        _workout_encoder = pickle.load(fh)


def predict_nutrition(
    age: int,
    weight_kg: float,
    height_m: float,
    sex: str,
    goal: str,
) -> tuple[float, float, float, float]:
    sex_enc = 1 if sex == "male" else 0
    goal_level = _GOAL_TO_LEVEL[goal]
    bmi = weight_kg / (height_m ** 2)

    X = np.array([[age, sex_enc, weight_kg, height_m, bmi, goal_level]])
    calories = float(_nutrition_model.predict(X)[0])

    # Macro split varies by goal
    splits = {
        "weight_loss": (0.35, 0.35, 0.30),
        "maintenance": (0.25, 0.45, 0.30),
        "muscle_gain": (0.30, 0.45, 0.25),
    }
    p_pct, c_pct, f_pct = splits[goal]
    protein_g = round(calories * p_pct / 4, 1)
    carbs_g = round(calories * c_pct / 4, 1)
    fat_g = round(calories * f_pct / 9, 1)

    return round(calories, 1), protein_g, carbs_g, fat_g


def predict_workout(
    age: int,
    weight_kg: float,
    height_m: float,
    sex: str,
    fat_percentage: float | None,
    resting_bpm: int | None,
    experience_level: int,
) -> tuple[str, str, float, int]:
    sex_enc = 1 if sex == "male" else 0
    bmi = weight_kg / (height_m ** 2)
    fat_pct = fat_percentage if fat_percentage is not None else bmi * 0.8
    bpm = resting_bpm if resting_bpm is not None else 70

    X = np.array([[age, sex_enc, weight_kg, height_m, bmi, fat_pct, bpm, experience_level]])
    encoded = _workout_model.predict(X)[0]
    workout_type: str = _workout_encoder.inverse_transform([encoded])[0]

    return (
        workout_type,
        _INTENSITY_MAP[experience_level],
        _DURATION_MAP[experience_level],
        _FREQ_MAP[experience_level],
    )
