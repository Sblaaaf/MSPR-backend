from datetime import date, datetime
from hashlib import sha256
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr, model_validator

from database import execute_write, fetch_all, fetch_one

router = APIRouter()

ALLOWED_REPAS = [
    "petit_dejeuner",
    "dejeuner",
    "diner",
    "collation",
]

ALLOWED_SEXE = ["homme", "femme", "autre", "non_renseigne"]
ALLOWED_ABONNEMENT = ["freemium", "premium", "premium_plus"]


def hash_password(raw_password: str) -> str:
    return sha256(raw_password.encode("utf-8")).hexdigest()


class AlimentCreate(BaseModel):
    nom: str = Field(..., min_length=2)
    calories_100g: float = Field(..., ge=0)
    categorie: Optional[str] = None
    proteines_g: Optional[float] = Field(0, ge=0)
    glucides_g: Optional[float] = Field(0, ge=0)
    lipides_g: Optional[float] = Field(0, ge=0)
    fibres_g: Optional[float] = Field(0, ge=0)
    sodium_mg: Optional[float] = Field(0, ge=0)
    sucres_g: Optional[float] = Field(0, ge=0)
    source_dataset: Optional[str] = "manual"


class AlimentResponse(BaseModel):
    id: int
    nom: str
    calories_100g: float
    categorie: Optional[str]
    source_dataset: Optional[str]
    created_at: datetime


class UserCreate(BaseModel):
    nom: str = Field(..., min_length=2)
    prenom: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    date_naissance: Optional[date] = None
    sexe: Optional[str] = "non_renseigne"
    poids_initial_kg: Optional[float] = Field(None, gt=0)
    taille_cm: Optional[int] = Field(None, ge=50, le=300)
    abonnement: Optional[str] = "freemium"

    @model_validator(mode="after")
    def check_enums(self):
        if self.sexe not in ALLOWED_SEXE:
            raise ValueError(f"sexe doit être dans {ALLOWED_SEXE}")
        if self.abonnement not in ALLOWED_ABONNEMENT:
            raise ValueError(f"abonnement doit être dans {ALLOWED_ABONNEMENT}")
        return self


class UserResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    email: EmailStr
    sexe: str
    abonnement: str
    date_inscription: datetime
    actif: bool


class MealLineCreate(BaseModel):
    aliment_id: Optional[int] = None
    aliment_nom: Optional[str] = None
    quantite_g: float = Field(..., gt=0)
    calories_100g: Optional[float] = None
    categorie: Optional[str] = None
    source_dataset: Optional[str] = "manual"

    @model_validator(mode="after")
    def require_aliment_reference(self):
        if not self.aliment_id and not self.aliment_nom:
            raise ValueError("aliment_id ou aliment_nom est requis")
        if self.aliment_nom and self.calories_100g is None:
            raise ValueError("calories_100g est requis lorsque aliment_nom est fourni")
        return self


class MealCreate(BaseModel):
    type_repas: str
    date_repas: Optional[date] = Field(default_factory=date.today)
    notes: Optional[str] = None
    items: list[MealLineCreate]

    @model_validator(mode="after")
    def check_type_repas(self):
        if self.type_repas not in ALLOWED_REPAS:
            raise ValueError(f"type_repas doit être dans {ALLOWED_REPAS}")
        if not self.items:
            raise ValueError("Au moins un aliment doit être fourni")
        return self


class MealLineResponse(BaseModel):
    id: int
    aliment_id: int
    aliment_nom: str
    quantite_g: float
    calories_calculees: float
    calories_100g: float
    categorie: Optional[str]
    source_dataset: Optional[str]


class MealResponse(BaseModel):
    id: int
    utilisateur_id: int
    date_repas: date
    type_repas: str
    notes: Optional[str]
    created_at: datetime
    total_calories: float
    items: list[MealLineResponse]


@router.post("/aliments", response_model=AlimentResponse)
def create_aliment(payload: AlimentCreate):
    existing = fetch_one(
        "SELECT id FROM aliment WHERE LOWER(nom) = LOWER(:nom)",
        {"nom": payload.nom},
    )
    if existing:
        raise HTTPException(400, "Cet aliment existe déjà")

    result = execute_write(
        "INSERT INTO aliment (nom, categorie, calories_100g, proteines_g, glucides_g, lipides_g, fibres_g, sodium_mg, sucres_g, source_dataset)"
        " VALUES (:nom, :categorie, :calories_100g, :proteines_g, :glucides_g, :lipides_g, :fibres_g, :sodium_mg, :sucres_g, :source_dataset)"
        " RETURNING id, nom, calories_100g, categorie, source_dataset, created_at",
        payload.model_dump(),
    )
    row = result.mappings().first()
    return AlimentResponse(**dict(row))


@router.get("/aliments", response_model=list[AlimentResponse])
def list_aliments(query: Optional[str] = Query(None, description="Filtrer par nom d'aliment")):
    sql = "SELECT id, nom, calories_100g, categorie, source_dataset, created_at FROM aliment"
    params = {}
    if query:
        sql += " WHERE LOWER(nom) LIKE LOWER(:query)"
        params["query"] = f"%{query}%"
    sql += " ORDER BY nom LIMIT 200"
    return [AlimentResponse(**row) for row in fetch_all(sql, params)]


@router.post("/users", response_model=UserResponse)
def create_user(payload: UserCreate):
    existing = fetch_one("SELECT id FROM utilisateur WHERE email = :email", {"email": payload.email})
    if existing:
        raise HTTPException(400, "Email déjà utilisé")

    params = payload.model_dump(exclude={"password"})
    params["mdp_hash"] = hash_password(payload.password)
    result = execute_write(
        "INSERT INTO utilisateur (nom, prenom, email, mdp_hash, date_naissance, sexe, poids_initial_kg, taille_cm, abonnement)"
        " VALUES (:nom, :prenom, :email, :mdp_hash, :date_naissance, :sexe, :poids_initial_kg, :taille_cm, :abonnement)"
        " RETURNING id, nom, prenom, email, sexe, abonnement, date_inscription, actif",
        params,
    )
    row = result.mappings().first()
    return UserResponse(**dict(row))


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = fetch_one(
        "SELECT id, nom, prenom, email, sexe, abonnement, date_inscription, actif FROM utilisateur WHERE id = :user_id",
        {"user_id": user_id},
    )
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    return UserResponse(**user)


def resolve_aliment(item: MealLineCreate) -> dict:
    if item.aliment_id:
        aliment = fetch_one("SELECT id, nom, calories_100g, categorie, source_dataset FROM aliment WHERE id = :id", {"id": item.aliment_id})
        if not aliment:
            raise HTTPException(404, f"Aliment introuvable id={item.aliment_id}")
        return aliment

    aliment = fetch_one(
        "SELECT id, nom, calories_100g, categorie, source_dataset FROM aliment WHERE LOWER(nom) = LOWER(:nom)",
        {"nom": item.aliment_nom},
    )
    if aliment:
        return aliment

    result = execute_write(
        "INSERT INTO aliment (nom, categorie, calories_100g, source_dataset)"
        " VALUES (:nom, :categorie, :calories_100g, :source_dataset)"
        " RETURNING id, nom, calories_100g, categorie, source_dataset",
        {
            "nom": item.aliment_nom,
            "categorie": item.categorie,
            "calories_100g": item.calories_100g,
            "source_dataset": item.source_dataset,
        },
    )
    return dict(result.mappings().first())


def get_meal_response(journal_id: int) -> MealResponse:
    rows = fetch_all(
        "SELECT jr.id AS meal_id, jr.utilisateur_id, jr.date_repas, jr.type_repas, jr.notes, jr.created_at, "
        " lr.id AS ligne_id, lr.quantite_g, lr.calories_calculees, "
        " a.id AS aliment_id, a.nom AS aliment_nom, a.calories_100g, a.categorie, a.source_dataset "
        "FROM journal_repas jr "
        "JOIN ligne_repas lr ON lr.journal_id = jr.id "
        "JOIN aliment a ON a.id = lr.aliment_id "
        "WHERE jr.id = :journal_id "
        "ORDER BY lr.id",
        {"journal_id": journal_id},
    )
    if not rows:
        raise HTTPException(404, "Repas introuvable")

    items = []
    total = 0.0
    for row in rows:
        items.append(
            MealLineResponse(
                id=row["ligne_id"],
                aliment_id=row["aliment_id"],
                aliment_nom=row["aliment_nom"],
                quantite_g=float(row["quantite_g"]),
                calories_calculees=float(row["calories_calculees"]),
                calories_100g=float(row["calories_100g"]),
                categorie=row["categorie"],
                source_dataset=row["source_dataset"],
            )
        )
        total += float(row["calories_calculees"])

    first = rows[0]
    return MealResponse(
        id=first["meal_id"],
        utilisateur_id=first["utilisateur_id"],
        date_repas=first["date_repas"],
        type_repas=first["type_repas"],
        notes=first["notes"],
        created_at=first["created_at"],
        total_calories=round(total, 2),
        items=items,
    )


@router.post("/users/{user_id}/meals", response_model=MealResponse)
def create_meal(user_id: int, payload: MealCreate):
    user = fetch_one("SELECT id FROM utilisateur WHERE id = :user_id", {"user_id": user_id})
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")

    journal_result = execute_write(
        "INSERT INTO journal_repas (utilisateur_id, date_repas, type_repas, notes) "
        "VALUES (:user_id, :date_repas, :type_repas, :notes) RETURNING id",
        {
            "user_id": user_id,
            "date_repas": payload.date_repas,
            "type_repas": payload.type_repas,
            "notes": payload.notes,
        },
    )
    journal_id = journal_result.scalar_one()

    for item in payload.items:
        aliment = resolve_aliment(item)
        execute_write(
            "INSERT INTO ligne_repas (journal_id, aliment_id, quantite_g) "
            "VALUES (:journal_id, :aliment_id, :quantite_g)",
            {
                "journal_id": journal_id,
                "aliment_id": aliment["id"],
                "quantite_g": item.quantite_g,
            },
        )

    return get_meal_response(journal_id)


@router.get("/users/{user_id}/meals", response_model=list[MealResponse])
def list_meals(user_id: int):
    user = fetch_one("SELECT id FROM utilisateur WHERE id = :user_id", {"user_id": user_id})
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")

    journals = fetch_all(
        "SELECT id FROM journal_repas WHERE utilisateur_id = :user_id ORDER BY date_repas DESC, id",
        {"user_id": user_id},
    )
    return [get_meal_response(j["id"]) for j in journals]


@router.get("/meals/{meal_id}", response_model=MealResponse)
def get_meal(meal_id: int):
    return get_meal_response(meal_id)


@router.delete("/meals/{meal_id}")
def delete_meal(meal_id: int):
    meal = fetch_one("SELECT id FROM journal_repas WHERE id = :meal_id", {"meal_id": meal_id})
    if not meal:
        raise HTTPException(404, "Repas introuvable")
    execute_write("DELETE FROM journal_repas WHERE id = :meal_id", {"meal_id": meal_id})
    return {"status": "deleted", "meal_id": meal_id}
