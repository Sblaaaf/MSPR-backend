"""
HealthAI Coach — Backend API
Point d'entrée minimal : un seul endpoint qui appelle le module IA.

Run: uvicorn main:app --reload
Doc: http://localhost:8000/docs
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent / "ia-kcal"))

from analyze import analyze

app = FastAPI(
    title="HealthAI Coach",
    description="API d'analyse nutritionnelle par IA",
    version="1.0.0"
)

# CORS — autorise le front Vercel à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # remplacer par l'URL Vercel exacte
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schémas ───────────────────────────────────────────────────────────────────

class MealRequest(BaseModel):
    text: str

    class Config:
        json_schema_extra = {
            "example": {
                "text": "2 eggs and a banana"
            }
        }


class FoodItemResponse(BaseModel):
    food: str
    grams: float
    kcal: float


class MealResponse(BaseModel):
    total_kcal: float
    message: str
    items: list[FoodItemResponse]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "HealthAI Coach API"}


@app.post("/analyze", response_model=MealResponse)
def analyze_meal(request: MealRequest):
    """
    Analyse un repas décrit en texte libre et retourne les kcal.

    - **text** : description libre du repas en anglais
      ex: "200g of grilled chicken with brown rice and broccoli"
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Meal text cannot be empty.")

    try:
        result = analyze(request.text)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI model not ready: {str(e)}. Run python nlp/train_ner.py first."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return MealResponse(
        total_kcal=result.total_kcal,
        message=result.message,
        items=[
            FoodItemResponse(
                food=item["food"],
                grams=item["grams"],
                kcal=item["kcal"]
            )
            for item in result.items
        ]
    )