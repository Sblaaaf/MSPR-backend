"""Standalone training script. Run directly or imported by model.py on first start."""
import os
import pickle
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", "/app/models"))


def _load_dataframe() -> pd.DataFrame:
    paths = [
        DATA_DIR / "gym_members_exercise.csv",
        DATA_DIR / "fitness_tracker.csv",
    ]
    frames = []
    for p in paths:
        if p.exists():
            frames.append(pd.read_csv(p))
        else:
            print(f"Warning: {p} not found, skipping.", file=sys.stderr)
    if not frames:
        raise FileNotFoundError(f"No training CSV found in {DATA_DIR}")
    df = pd.concat(frames, ignore_index=True)
    df["Gender_enc"] = (df["Gender"] == "Male").astype(int)
    # BMI column already present in CSVs; recompute to ensure consistency
    df["BMI"] = df["Weight (kg)"] / (df["Height (m)"] ** 2)
    return df


def train_and_save() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = _load_dataframe()

    # --- Nutrition model (regressor) ---
    # Predict Calories_Burned as proxy for recommended daily energy expenditure.
    # Experience_Level (1-3) is used as the "goal intensity" feature.
    nut_features = [
        "Age", "Gender_enc", "Weight (kg)", "Height (m)", "BMI", "Experience_Level",
    ]
    nut_df = df[nut_features + ["Calories_Burned"]].dropna()
    X_nut = nut_df[nut_features].values
    y_nut = nut_df["Calories_Burned"].values

    X_tr, X_te, y_tr, y_te = train_test_split(X_nut, y_nut, test_size=0.2, random_state=42)
    nut_model = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
    nut_model.fit(X_tr, y_tr)
    y_pred = nut_model.predict(X_te)
    print(f"[Nutrition] MAE={mean_absolute_error(y_te, y_pred):.1f} kcal  R²={r2_score(y_te, y_pred):.3f}")

    # --- Workout model (classifier) ---
    work_features = [
        "Age", "Gender_enc", "Weight (kg)", "Height (m)",
        "BMI", "Fat_Percentage", "Resting_BPM", "Experience_Level",
    ]
    work_df = df[work_features + ["Workout_Type"]].dropna()
    le = LabelEncoder()
    y_work = le.fit_transform(work_df["Workout_Type"].values)
    X_work = work_df[work_features].values

    X_tr, X_te, y_tr, y_te = train_test_split(X_work, y_work, test_size=0.2, random_state=42, stratify=y_work)
    work_model = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
    work_model.fit(X_tr, y_tr)
    y_pred = work_model.predict(X_te)
    print("\n[Workout] Classification report:")
    print(classification_report(y_te, y_pred, target_names=le.classes_))

    # Save artefacts
    for name, obj in [
        ("nutrition_model.pkl", nut_model),
        ("workout_model.pkl", work_model),
        ("workout_encoder.pkl", le),
    ]:
        with open(MODELS_DIR / name, "wb") as fh:
            pickle.dump(obj, fh)

    print(f"\nModels saved to {MODELS_DIR}")


if __name__ == "__main__":
    train_and_save()
