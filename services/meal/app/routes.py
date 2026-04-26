from datetime import date, datetime
from hashlib import sha256
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr, model_validator

from database import execute_write, fetch_all, fetch_one
from .translations import get_message
from .lang_dep import get_language

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
    nom: str = Field(..., min_length=2, example="Riz blanc", description="Nom de l'aliment")
    calories_100g: float = Field(..., ge=0, example=130, description="Calories pour 100g")
    categorie: Optional[str] = Field(None, example="Féculents", description="Catégorie de l'aliment")
    proteines_g: Optional[float] = Field(0, ge=0, example=2.7, description="Protéines pour 100g")
    glucides_g: Optional[float] = Field(0, ge=0, example=28, description="Glucides pour 100g")
    lipides_g: Optional[float] = Field(0, ge=0, example=0.3, description="Lipides pour 100g")
    fibres_g: Optional[float] = Field(0, ge=0, example=0.4, description="Fibres pour 100g")
    sodium_mg: Optional[float] = Field(0, ge=0, example=1, description="Sodium (mg)")
    sucres_g: Optional[float] = Field(0, ge=0, example=0.1, description="Sucres pour 100g")
    source_dataset: Optional[str] = Field("manual", example="manual", description="Source des données")

    class Config:
        json_schema_extra = {
            "example": {
                "nom": "Riz blanc",
                "calories_100g": 130,
                "categorie": "Féculents",
                "proteines_g": 2.7,
                "glucides_g": 28,
                "lipides_g": 0.3,
                "fibres_g": 0.4,
                "sodium_mg": 1,
                "sucres_g": 0.1,
                "source_dataset": "manual"
            }
        }


class AlimentResponse(BaseModel):
    id: int
    nom: str
    calories_100g: float
    categorie: Optional[str]
    source_dataset: Optional[str]
    created_at: datetime


class UserCreate(BaseModel):
    nom: str = Field(..., min_length=2, example="Dupont", description="Nom de famille")
    prenom: str = Field(..., min_length=2, example="Jean", description="Prénom")
    email: EmailStr = Field(..., example="jean.dupont@example.com", description="Adresse email")
    password: str = Field(..., min_length=6, example="secret123", description="Mot de passe")
    date_naissance: Optional[date] = Field(None, example="1990-01-01", description="Date de naissance")
    sexe: Optional[str] = Field("non_renseigne", example="homme", description="Sexe")
    poids_initial_kg: Optional[float] = Field(None, gt=0, example=70, description="Poids initial (kg)")
    taille_cm: Optional[int] = Field(None, ge=50, le=300, example=175, description="Taille (cm)")
    abonnement: Optional[str] = Field("freemium", example="freemium", description="Type d'abonnement")

    class Config:
        json_schema_extra = {
            "example": {
                "nom": "Dupont",
                "prenom": "Jean",
                "email": "jean.dupont@example.com",
                "password": "secret123",
                "date_naissance": "1990-01-01",
                "sexe": "homme",
                "poids_initial_kg": 70,
                "taille_cm": 175,
                "abonnement": "freemium"
            }
        }


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
    aliment_id: Optional[int] = Field(None, example=1, description="ID de l'aliment (optionnel)")
    aliment_nom: Optional[str] = Field(None, example="Riz blanc", description="Nom de l'aliment si non référencé")
    quantite_g: float = Field(..., gt=0, example=150, description="Quantité en grammes")
    calories_100g: Optional[float] = Field(None, example=130, description="Calories pour 100g si aliment_nom fourni")
    categorie: Optional[str] = Field(None, example="Féculents", description="Catégorie si aliment_nom fourni")
    source_dataset: Optional[str] = Field("manual", example="manual", description="Source des données")

    class Config:
        json_schema_extra = {
            "example": {
                "aliment_id": 1,
                "quantite_g": 150
            }
        }


class MealCreate(BaseModel):
    type_repas: str = Field(..., example="dejeuner", description="Type de repas (petit_dejeuner, dejeuner, diner, collation)")
    date_repas: Optional[date] = Field(default_factory=date.today, example="2024-04-08", description="Date du repas")
    notes: Optional[str] = Field(None, example="Repas du midi", description="Notes libres")
    items: list[MealLineCreate] = Field(..., description="Liste des aliments du repas")

    class Config:
        json_schema_extra = {
            "example": {
                "type_repas": "dejeuner",
                "date_repas": "2024-04-08",
                "notes": "Repas du midi",
                "items": [
                    {"aliment_id": 1, "quantite_g": 150}
                ]
            }
        }


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


class MetricCreate(BaseModel):
    date_mesure: date = Field(..., description="Date de la mesure")
    poids_kg: Optional[float] = Field(None, description="Poids en kg")
    heures_sommeil: Optional[float] = Field(None, description="Heures de sommeil")
    bpm_repos: Optional[int] = Field(None, description="BPM au repos")


class MetricResponse(BaseModel):
    date_mesure: date = Field(..., description="Date de la mesure")
    poids_kg: Optional[float] = Field(None, description="Poids en kg")
    heures_sommeil: Optional[float] = Field(None, description="Heures de sommeil")
    bpm_repos: Optional[int] = Field(None, description="Battements par minute au repos")

    class Config:
        json_schema_extra = {
            "example": {
                "date_mesure": "2024-05-01",
                "poids_kg": 78.5,
                "heures_sommeil": 7.5,
                "bpm_repos": 62
            }
        }

class ObjectifResponse(BaseModel):
    id: int
    libelle: str
    description: str
    date_debut: date
    actif: bool

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "libelle": "perte_de_poids",
                "description": "Réduire la masse graisseuse",
                "date_debut": "2024-05-01",
                "actif": True
            }
        }


@router.post("/aliments", response_model=AlimentResponse)
def create_aliment(payload: AlimentCreate, language: str = Depends(get_language)):
    existing = fetch_one(
        "SELECT id FROM aliment WHERE LOWER(nom) = LOWER(:nom)",
        {"nom": payload.nom},
    )
    if existing:
        raise HTTPException(400, get_message("aliment_already_exists", language))

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
def create_user(payload: UserCreate, language: str = Depends(get_language)):
    existing = fetch_one("SELECT id FROM utilisateur WHERE email = :email", {"email": payload.email})
    if existing:
        raise HTTPException(400, get_message("email_already_used", language))

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
def get_user(user_id: int, language: str = Depends(get_language)):
    user = fetch_one(
        "SELECT id, nom, prenom, email, sexe, abonnement, date_inscription, actif FROM utilisateur WHERE id = :user_id",
        {"user_id": user_id},
    )
    if not user:
        raise HTTPException(404, get_message("user_not_found", language))
    return UserResponse(**user)


def resolve_aliment(item: MealLineCreate, language: str = "EN") -> dict:
    if item.aliment_id:
        aliment = fetch_one("SELECT id, nom, calories_100g, categorie, source_dataset FROM aliment WHERE id = :id", {"id": item.aliment_id})
        if not aliment:
            raise HTTPException(404, get_message("aliment_not_found", language, id=item.aliment_id))
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


def get_meal_response(journal_id: int, language: str = "EN") -> MealResponse:
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
        raise HTTPException(404, get_message("meal_not_found", language))

    items = []
    total = 0.0
    for row in rows:
        kcal = round(float(row["quantite_g"]) * float(row["calories_100g"]) / 100.0, 2)
        items.append(
            MealLineResponse(
                id=row["ligne_id"],
                aliment_id=row["aliment_id"],
                aliment_nom=row["aliment_nom"],
                quantite_g=float(row["quantite_g"]),
                calories_calculees=kcal,
                calories_100g=float(row["calories_100g"]),
                categorie=row["categorie"],
                source_dataset=row["source_dataset"],
            )
        )
        total += kcal

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
def create_meal(user_id: int, payload: MealCreate, language: str = Depends(get_language)):
    user = fetch_one("SELECT id FROM utilisateur WHERE id = :user_id", {"user_id": user_id})
    if not user:
        raise HTTPException(404, get_message("user_not_found", language))

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
        aliment = resolve_aliment(item, language)
        execute_write(
            "INSERT INTO ligne_repas (journal_id, aliment_id, quantite_g) "
            "VALUES (:journal_id, :aliment_id, :quantite_g)",
            {
                "journal_id": journal_id,
                "aliment_id": aliment["id"],
                "quantite_g": item.quantite_g,
            },
        )

    return get_meal_response(journal_id, language)


@router.get("/users/{user_id}/meals", response_model=list[MealResponse])
def list_meals(user_id: int, language: str = Depends(get_language)):
    user = fetch_one("SELECT id FROM utilisateur WHERE id = :user_id", {"user_id": user_id})
    if not user:
        raise HTTPException(404, get_message("user_not_found", language))

    journals = fetch_all(
        "SELECT id FROM journal_repas WHERE utilisateur_id = :user_id ORDER BY date_repas DESC, id",
        {"user_id": user_id},
    )
    return [get_meal_response(j["id"], language) for j in journals]


@router.get("/meals/{meal_id}", response_model=MealResponse)
def get_meal(meal_id: int, language: str = Depends(get_language)):
    return get_meal_response(meal_id, language)


@router.delete("/meals/{meal_id}")
def delete_meal(meal_id: int, language: str = Depends(get_language)):
    meal = fetch_one("SELECT id FROM journal_repas WHERE id = :meal_id", {"meal_id": meal_id})
    if not meal:
        raise HTTPException(404, get_message("meal_not_found", language))
    execute_write("DELETE FROM journal_repas WHERE id = :meal_id", {"meal_id": meal_id})
    return {"status": "deleted", "meal_id": meal_id}

@router.get("/users/{user_id}/metrics", response_model=list[MetricResponse])
def get_user_metrics(user_id: int, language: str = Depends(get_language)):
    user = fetch_one("SELECT id FROM utilisateur WHERE id = :user_id", {"user_id": user_id})
    if not user:
        raise HTTPException(404, get_message("user_not_found", language))

    sql = """
        SELECT date_mesure, poids_kg, heures_sommeil, bpm_repos
        FROM metrique_quotidienne
        WHERE utilisateur_id = :user_id
        ORDER BY date_mesure ASC
        LIMIT 90
    """
    rows = fetch_all(sql, {"user_id": user_id})
    return [MetricResponse(**dict(row)) for row in rows]


@router.post("/users/{user_id}/metrics", response_model=MetricResponse)
def create_user_metric(user_id: int, payload: MetricCreate, language: str = Depends(get_language)):
    user = fetch_one("SELECT id FROM utilisateur WHERE id = :user_id", {"user_id": user_id})
    if not user:
        raise HTTPException(404, get_message("user_not_found", language))

    execute_write(
        """
        INSERT INTO metrique_quotidienne (utilisateur_id, date_mesure, poids_kg, heures_sommeil, bpm_repos)
        VALUES (:user_id, :date_mesure, :poids_kg, :heures_sommeil, :bpm_repos)
        ON CONFLICT (utilisateur_id, date_mesure)
        DO UPDATE SET
            poids_kg = COALESCE(EXCLUDED.poids_kg, metrique_quotidienne.poids_kg),
            heures_sommeil = COALESCE(EXCLUDED.heures_sommeil, metrique_quotidienne.heures_sommeil),
            bpm_repos = COALESCE(EXCLUDED.bpm_repos, metrique_quotidienne.bpm_repos)
        """,
        {
            "user_id": user_id,
            "date_mesure": payload.date_mesure,
            "poids_kg": payload.poids_kg,
            "heures_sommeil": payload.heures_sommeil,
            "bpm_repos": payload.bpm_repos,
        },
    )
    row = fetch_one(
        "SELECT date_mesure, poids_kg, heures_sommeil, bpm_repos FROM metrique_quotidienne WHERE utilisateur_id = :user_id AND date_mesure = :date_mesure",
        {"user_id": user_id, "date_mesure": payload.date_mesure},
    )
    return MetricResponse(**dict(row))


class SubscriptionUpdate(BaseModel):
    abonnement: str


@router.patch("/users/{user_id}/subscription", response_model=UserResponse)
def update_subscription(user_id: int, payload: SubscriptionUpdate, language: str = Depends(get_language)):
    if payload.abonnement not in ALLOWED_ABONNEMENT:
        raise HTTPException(400, get_message("invalid_subscription", language, values=", ".join(ALLOWED_ABONNEMENT)))
    user = fetch_one("SELECT id FROM utilisateur WHERE id = :user_id", {"user_id": user_id})
    if not user:
        raise HTTPException(404, get_message("user_not_found", language))
    result = execute_write(
        "UPDATE utilisateur SET abonnement = :abonnement WHERE id = :user_id"
        " RETURNING id, nom, prenom, email, sexe, abonnement, date_inscription, actif",
        {"abonnement": payload.abonnement, "user_id": user_id},
    )
    row = result.mappings().first()
    return UserResponse(**dict(row))


@router.get("/users/{user_id}/objectives", response_model=list[ObjectifResponse])
def get_user_objectives(user_id: int, language: str = Depends(get_language)):
    user = fetch_one("SELECT id FROM utilisateur WHERE id = :user_id", {"user_id": user_id})
    if not user:
        raise HTTPException(404, get_message("user_not_found", language))

    sql = """
        SELECT o.id, o.libelle, o.description, uo.date_debut, uo.actif
        FROM utilisateur_objectif uo
        JOIN objectif o ON uo.objectif_id = o.id
        WHERE uo.utilisateur_id = :user_id
        ORDER BY uo.date_debut DESC
    """
    rows = fetch_all(sql, {"user_id": user_id})
    return [ObjectifResponse(**row) for row in rows]


class AvailableObjectif(BaseModel):
    id: int
    libelle: str
    description: str


@router.get("/objectifs", response_model=list[AvailableObjectif])
def list_available_objectifs():
    rows = fetch_all("SELECT id, libelle, description FROM objectif ORDER BY id", {})
    return [AvailableObjectif(**row) for row in rows]


class ObjectiveAdd(BaseModel):
    objectif_id: int


@router.post("/users/{user_id}/objectives", response_model=ObjectifResponse)
def add_user_objective(user_id: int, payload: ObjectiveAdd, language: str = Depends(get_language)):
    user = fetch_one("SELECT id FROM utilisateur WHERE id = :user_id", {"user_id": user_id})
    if not user:
        raise HTTPException(404, get_message("user_not_found", language))

    objectif = fetch_one("SELECT id, libelle, description FROM objectif WHERE id = :id", {"id": payload.objectif_id})
    if not objectif:
        raise HTTPException(404, get_message("objective_not_found", language))

    existing = fetch_one(
        "SELECT 1 FROM utilisateur_objectif WHERE utilisateur_id = :user_id AND objectif_id = :objectif_id",
        {"user_id": user_id, "objectif_id": payload.objectif_id},
    )
    if existing:
        raise HTTPException(400, get_message("objective_already_set", language))

    execute_write(
        "INSERT INTO utilisateur_objectif (utilisateur_id, objectif_id, date_debut, actif)"
        " VALUES (:user_id, :objectif_id, CURRENT_DATE, true)",
        {"user_id": user_id, "objectif_id": payload.objectif_id},
    )
    row = fetch_one(
        "SELECT o.id, o.libelle, o.description, uo.date_debut, uo.actif"
        " FROM utilisateur_objectif uo JOIN objectif o ON uo.objectif_id = o.id"
        " WHERE uo.utilisateur_id = :user_id AND uo.objectif_id = :objectif_id",
        {"user_id": user_id, "objectif_id": payload.objectif_id},
    )
    return ObjectifResponse(**row)


class ObjectiveToggle(BaseModel):
    actif: bool


@router.patch("/users/{user_id}/objectives/{objectif_id}", response_model=ObjectifResponse)
def toggle_user_objective(user_id: int, objectif_id: int, payload: ObjectiveToggle, language: str = Depends(get_language)):
    existing = fetch_one(
        "SELECT 1 FROM utilisateur_objectif WHERE utilisateur_id = :user_id AND objectif_id = :objectif_id",
        {"user_id": user_id, "objectif_id": objectif_id},
    )
    if not existing:
        raise HTTPException(404, get_message("user_objective_not_found", language))

    execute_write(
        "UPDATE utilisateur_objectif SET actif = :actif WHERE utilisateur_id = :user_id AND objectif_id = :objectif_id",
        {"actif": payload.actif, "user_id": user_id, "objectif_id": objectif_id},
    )
    row = fetch_one(
        "SELECT o.id, o.libelle, o.description, uo.date_debut, uo.actif"
        " FROM utilisateur_objectif uo JOIN objectif o ON uo.objectif_id = o.id"
        " WHERE uo.utilisateur_id = :user_id AND uo.objectif_id = :objectif_id",
        {"user_id": user_id, "objectif_id": objectif_id},
    )
    return ObjectifResponse(**row)


@router.delete("/users/{user_id}")
def delete_user(user_id: int, language: str = Depends(get_language)):
    user = fetch_one("SELECT id FROM utilisateur WHERE id = :user_id", {"user_id": user_id})
    if not user:
        raise HTTPException(404, get_message("user_not_found", language))

    execute_write(
        "DELETE FROM ligne_repas WHERE journal_id IN (SELECT id FROM journal_repas WHERE utilisateur_id = :user_id)",
        {"user_id": user_id},
    )
    execute_write("DELETE FROM journal_repas WHERE utilisateur_id = :user_id", {"user_id": user_id})
    execute_write("DELETE FROM utilisateur_objectif WHERE utilisateur_id = :user_id", {"user_id": user_id})
    execute_write("DELETE FROM metrique_quotidienne WHERE utilisateur_id = :user_id", {"user_id": user_id})
    execute_write("DELETE FROM utilisateur WHERE id = :user_id", {"user_id": user_id})
    return {"status": "deleted", "user_id": user_id}