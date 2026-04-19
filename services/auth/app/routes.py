from hashlib import sha256
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, HTTPException

from database import fetch_one

router = APIRouter()


def hash_password(raw_password: str) -> str:
    return sha256(raw_password.encode("utf-8")).hexdigest()


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="jean.dupont@example.com", description="Adresse email de l'utilisateur")
    password: str = Field(..., min_length=6, example="secret123", description="Mot de passe de l'utilisateur")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "jean.dupont@example.com",
                "password": "secret123"
            }
        }


class LoginResponse(BaseModel):
    success: bool = Field(..., example=True, description="Succès de l'authentification")
    message: str = Field(..., example="Authentification réussie.", description="Message de retour")
    user_id: int | None = Field(None, example=1, description="ID utilisateur si succès")
    email: EmailStr | None = Field(None, example="jean.dupont@example.com", description="Email utilisateur si succès")
    abonnement: str | None = Field(None, example="freemium", description="Type d'abonnement de l'utilisateur") # NOUVEAU

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    # Ajout de 'abonnement' dans le SELECT
    user = fetch_one(
        "SELECT id, email, mdp_hash, actif, abonnement FROM utilisateur WHERE email = :email",
        {"email": payload.email},
    )
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")

    if not user["actif"]:
        raise HTTPException(status_code=403, detail="Utilisateur inactif.")

    if user["mdp_hash"] != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")

    return LoginResponse(
        success=True,
        message="Authentification réussie.",
        user_id=user["id"],
        email=user["email"],
        abonnement=user["abonnement"], # NOUVEAU
    )