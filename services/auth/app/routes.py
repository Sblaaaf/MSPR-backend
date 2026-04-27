import os
from hashlib import sha256
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException

from database import fetch_one
from .translations import get_message
from .lang_dep import get_language

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
    nom: str | None = Field(None, example="Dupont", description="Nom de famille")
    prenom: str | None = Field(None, example="Jean", description="Prénom")
    abonnement: str | None = Field(None, example="freemium", description="Type d'abonnement de l'utilisateur")

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, language: str = Depends(get_language)):
    user = fetch_one(
        "SELECT id, email, nom, prenom, mdp_hash, actif, abonnement FROM utilisateur WHERE email = :email",
        {"email": payload.email},
    )
    if not user:
        raise HTTPException(
            status_code=401,
            detail=get_message("invalid_credentials", language)
        )

    if not user["actif"]:
        raise HTTPException(
            status_code=403,
            detail=get_message("user_inactive", language)
        )

    if user["mdp_hash"] != hash_password(payload.password):
        raise HTTPException(
            status_code=401,
            detail=get_message("invalid_credentials", language)
        )

    return LoginResponse(
        success=True,
        message=get_message("login_success", language),
        user_id=user["id"],
        email=user["email"],
        nom=user["nom"],
        prenom=user["prenom"],
        abonnement=user["abonnement"],
    )


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    role: str = "admin"


@router.post("/admin-login", response_model=AdminLoginResponse)
def admin_login(payload: AdminLoginRequest):
    expected_username = os.getenv("ADMIN_USERNAME", "admin")
    expected_password = os.getenv("ADMIN_PASSWORD", "admin")

    if payload.username != expected_username or payload.password != expected_password:
        raise HTTPException(status_code=401, detail="Identifiants administrateur invalides.")

    return AdminLoginResponse(success=True, role="admin")