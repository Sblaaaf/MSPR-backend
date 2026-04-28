"""
HealthAI Admin API — routes
CRUD : utilisateurs, aliments, exercices, métriques
Extra : qualité données, workflow validation, export JSON/CSV, analytics
"""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr

from database import execute, fetch_all, fetch_one

router = APIRouter()


# ================================================================
# MODÈLES PYDANTIC
# ================================================================

class UtilisateurCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    mdp_hash: str
    sexe: str = "non_renseigne"
    poids_initial_kg: Optional[float] = None
    taille_cm: Optional[int] = None
    abonnement: str = "freemium"

class UtilisateurUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    sexe: Optional[str] = None
    poids_initial_kg: Optional[float] = None
    taille_cm: Optional[int] = None
    abonnement: Optional[str] = None
    actif: Optional[bool] = None

class AlimentCreate(BaseModel):
    nom: str
    categorie: Optional[str] = None
    calories_100g: float = 0
    proteines_g: float = 0
    glucides_g: float = 0
    lipides_g: float = 0
    fibres_g: float = 0
    sodium_mg: Optional[float] = None
    sucres_g: Optional[float] = None

class AlimentUpdate(BaseModel):
    nom: Optional[str] = None
    categorie: Optional[str] = None
    calories_100g: Optional[float] = None
    proteines_g: Optional[float] = None
    glucides_g: Optional[float] = None
    lipides_g: Optional[float] = None
    fibres_g: Optional[float] = None

class ExerciceCreate(BaseModel):
    nom: str
    type: str = "musculation"
    niveau: str = "debutant"
    equipement: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None

class ExerciceUpdate(BaseModel):
    nom: Optional[str] = None
    type: Optional[str] = None
    niveau: Optional[str] = None
    equipement: Optional[str] = None
    description: Optional[str] = None

class MetriqueCreate(BaseModel):
    utilisateur_id: int
    date_mesure: str
    poids_kg: Optional[float] = None
    bpm_repos: Optional[int] = None
    bpm_max: Optional[int] = None
    heures_sommeil: Optional[float] = None
    steps: Optional[int] = None
    calories_brulees: Optional[float] = None
    body_fat_pct: Optional[float] = None
    source: str = "admin"

class MetriqueUpdate(BaseModel):
    poids_kg: Optional[float] = None
    bpm_repos: Optional[int] = None
    bpm_max: Optional[int] = None
    heures_sommeil: Optional[float] = None
    steps: Optional[int] = None
    calories_brulees: Optional[float] = None
    body_fat_pct: Optional[float] = None


# ================================================================
# SANTÉ
# ================================================================

@router.get("/health", tags=["monitoring"])
def health():
    return {"status": "ok", "service": "healthai_admin", "version": "1.0.0"}


# ================================================================
# UTILISATEURS
# ================================================================

@router.get("/users", tags=["utilisateurs"], summary="Lister les utilisateurs")
def list_users(limit: int = 50, offset: int = 0, actif: Optional[bool] = None, search: Optional[str] = None):
    conditions = []
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if actif is not None:
        conditions.append("actif = :actif")
        params["actif"] = actif
    if search:
        conditions.append("(nom ILIKE :search OR prenom ILIKE :search OR email ILIKE :search)")
        params["search"] = f"%{search}%"
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = fetch_all(
        f"SELECT id, nom, prenom, email, sexe, poids_initial_kg, taille_cm, abonnement, actif, imc, created_at "
        f"FROM utilisateur {where} ORDER BY id LIMIT :limit OFFSET :offset",
        params,
    )
    total = fetch_one(f"SELECT COUNT(*) AS n FROM utilisateur {where}", params)
    return {"total": total["n"], "data": rows}


@router.get("/users/{user_id}", tags=["utilisateurs"])
def get_user(user_id: int):
    row = fetch_one("SELECT * FROM utilisateur WHERE id = :id", {"id": user_id})
    if not row:
        raise HTTPException(404, "Utilisateur introuvable")
    return row


@router.post("/users", tags=["utilisateurs"], status_code=201)
def create_user(body: UtilisateurCreate):
    existing = fetch_one("SELECT id FROM utilisateur WHERE email = :e", {"e": body.email})
    if existing:
        raise HTTPException(409, "Email déjà utilisé")
    row = fetch_one(
        """INSERT INTO utilisateur (nom, prenom, email, mdp_hash, sexe, poids_initial_kg, taille_cm, abonnement)
           VALUES (:nom, :prenom, :email, :mdp_hash, :sexe, :poids, :taille, :abo)
           RETURNING id""",
        {"nom": body.nom, "prenom": body.prenom, "email": body.email, "mdp_hash": body.mdp_hash,
         "sexe": body.sexe, "poids": body.poids_initial_kg, "taille": body.taille_cm, "abo": body.abonnement},
    )
    return {"id": row["id"], "message": "Utilisateur créé"}


@router.patch("/users/{user_id}", tags=["utilisateurs"])
def update_user(user_id: int, body: UtilisateurUpdate):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "Aucun champ à mettre à jour")
    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = user_id
    n = execute(f"UPDATE utilisateur SET {set_clause} WHERE id = :id", fields)
    if n == 0:
        raise HTTPException(404, "Utilisateur introuvable")
    return {"message": "Mis à jour"}


@router.delete("/users/{user_id}", tags=["utilisateurs"])
def delete_user(user_id: int):
    n = execute("DELETE FROM utilisateur WHERE id = :id", {"id": user_id})
    if n == 0:
        raise HTTPException(404, "Utilisateur introuvable")
    return {"message": "Supprimé"}


# ================================================================
# ALIMENTS
# ================================================================

@router.get("/foods", tags=["aliments"], summary="Lister les aliments")
def list_foods(limit: int = 50, offset: int = 0, categorie: Optional[str] = None, search: Optional[str] = None):
    conditions = []
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if categorie:
        conditions.append("categorie = :cat")
        params["cat"] = categorie
    if search:
        conditions.append("(nom ILIKE :search OR categorie ILIKE :search)")
        params["search"] = f"%{search}%"
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = fetch_all(
        f"SELECT id, nom, categorie, calories_100g, proteines_g, glucides_g, lipides_g, fibres_g, source_dataset "
        f"FROM aliment {where} ORDER BY nom LIMIT :limit OFFSET :offset",
        params,
    )
    total = fetch_one(f"SELECT COUNT(*) AS n FROM aliment {where}", params)
    return {"total": total["n"], "data": rows}


@router.get("/foods/{food_id}", tags=["aliments"])
def get_food(food_id: int):
    row = fetch_one("SELECT * FROM aliment WHERE id = :id", {"id": food_id})
    if not row:
        raise HTTPException(404, "Aliment introuvable")
    return row


@router.post("/foods", tags=["aliments"], status_code=201)
def create_food(body: AlimentCreate):
    row = fetch_one(
        """INSERT INTO aliment (nom, categorie, calories_100g, proteines_g, glucides_g, lipides_g, fibres_g, sodium_mg, sucres_g)
           VALUES (:nom, :cat, :cal, :prot, :gluc, :lip, :fib, :sod, :suc)
           RETURNING id""",
        {"nom": body.nom, "cat": body.categorie, "cal": body.calories_100g,
         "prot": body.proteines_g, "gluc": body.glucides_g, "lip": body.lipides_g,
         "fib": body.fibres_g, "sod": body.sodium_mg, "suc": body.sucres_g},
    )
    return {"id": row["id"], "message": "Aliment créé"}


@router.patch("/foods/{food_id}", tags=["aliments"])
def update_food(food_id: int, body: AlimentUpdate):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "Aucun champ à mettre à jour")
    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = food_id
    n = execute(f"UPDATE aliment SET {set_clause} WHERE id = :id", fields)
    if n == 0:
        raise HTTPException(404, "Aliment introuvable")
    return {"message": "Mis à jour"}


@router.delete("/foods/{food_id}", tags=["aliments"])
def delete_food(food_id: int):
    n = execute("DELETE FROM aliment WHERE id = :id", {"id": food_id})
    if n == 0:
        raise HTTPException(404, "Aliment introuvable")
    return {"message": "Supprimé"}


# ================================================================
# EXERCICES
# ================================================================

@router.get("/exercises", tags=["exercices"])
def list_exercises(limit: int = 50, offset: int = 0, niveau: Optional[str] = None, type: Optional[str] = None, search: Optional[str] = None):
    conditions = []
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if niveau:
        conditions.append("niveau = :niveau")
        params["niveau"] = niveau
    if type:
        conditions.append("type = :type")
        params["type"] = type
    if search:
        conditions.append("(nom ILIKE :search OR type ILIKE :search OR equipement ILIKE :search)")
        params["search"] = f"%{search}%"
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = fetch_all(
        f"SELECT id, nom, type, niveau, equipement, source_dataset FROM exercice {where} ORDER BY nom LIMIT :limit OFFSET :offset",
        params,
    )
    total = fetch_one(f"SELECT COUNT(*) AS n FROM exercice {where}", params)
    return {"total": total["n"], "data": rows}


@router.get("/exercises/{ex_id}", tags=["exercices"])
def get_exercise(ex_id: int):
    row = fetch_one("SELECT * FROM exercice WHERE id = :id", {"id": ex_id})
    if not row:
        raise HTTPException(404, "Exercice introuvable")
    return row


@router.post("/exercises", tags=["exercices"], status_code=201)
def create_exercise(body: ExerciceCreate):
    row = fetch_one(
        """INSERT INTO exercice (nom, type, niveau, equipement, description, instructions)
           VALUES (:nom, :type, :niveau, :equipement, :description, :instructions)
           RETURNING id""",
        body.model_dump(),
    )
    return {"id": row["id"], "message": "Exercice créé"}


@router.patch("/exercises/{ex_id}", tags=["exercices"])
def update_exercise(ex_id: int, body: ExerciceUpdate):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "Aucun champ à mettre à jour")
    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = ex_id
    n = execute(f"UPDATE exercice SET {set_clause} WHERE id = :id", fields)
    if n == 0:
        raise HTTPException(404, "Exercice introuvable")
    return {"message": "Mis à jour"}


@router.delete("/exercises/{ex_id}", tags=["exercices"])
def delete_exercise(ex_id: int):
    n = execute("DELETE FROM exercice WHERE id = :id", {"id": ex_id})
    if n == 0:
        raise HTTPException(404, "Exercice introuvable")
    return {"message": "Supprimé"}


# ================================================================
# MÉTRIQUES
# ================================================================

@router.get("/metrics", tags=["métriques"])
def list_metrics(utilisateur_id: Optional[int] = None, limit: int = 100, offset: int = 0):
    where = "WHERE utilisateur_id = :uid" if utilisateur_id else ""
    params: dict[str, Any] = {"limit": limit, "offset": offset, "uid": utilisateur_id}
    rows = fetch_all(
        f"SELECT * FROM metrique_quotidienne {where} ORDER BY date_mesure DESC LIMIT :limit OFFSET :offset",
        params,
    )
    total = fetch_one(f"SELECT COUNT(*) AS n FROM metrique_quotidienne {where}", params)
    return {"total": total["n"], "data": rows}


@router.post("/metrics", tags=["métriques"], status_code=201)
def create_metric(body: MetriqueCreate):
    row = fetch_one(
        """INSERT INTO metrique_quotidienne
           (utilisateur_id, date_mesure, poids_kg, bpm_repos, bpm_max, heures_sommeil, steps, calories_brulees, body_fat_pct, source)
           VALUES (:utilisateur_id, :date_mesure, :poids_kg, :bpm_repos, :bpm_max, :heures_sommeil, :steps, :calories_brulees, :body_fat_pct, :source)
           ON CONFLICT (utilisateur_id, date_mesure) DO UPDATE SET
               poids_kg = EXCLUDED.poids_kg, bpm_repos = EXCLUDED.bpm_repos,
               bpm_max = EXCLUDED.bpm_max, calories_brulees = EXCLUDED.calories_brulees
           RETURNING id""",
        body.model_dump(),
    )
    return {"id": row["id"], "message": "Métrique enregistrée"}


@router.patch("/metrics/{metric_id}", tags=["métriques"])
def update_metric(metric_id: int, body: MetriqueUpdate):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "Aucun champ à mettre à jour")
    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = metric_id
    n = execute(f"UPDATE metrique_quotidienne SET {set_clause} WHERE id = :id", fields)
    if n == 0:
        raise HTTPException(404, "Métrique introuvable")
    return {"message": "Mis à jour"}


@router.delete("/metrics/{metric_id}", tags=["métriques"])
def delete_metric(metric_id: int):
    n = execute("DELETE FROM metrique_quotidienne WHERE id = :id", {"id": metric_id})
    if n == 0:
        raise HTTPException(404, "Métrique introuvable")
    return {"message": "Supprimé"}


# ================================================================
# QUALITÉ DES DONNÉES
# ================================================================

@router.get("/data-quality", tags=["administration"], summary="Dashboard qualité des données")
def data_quality():
    stats = fetch_one("""
        SELECT
            (SELECT COUNT(*) FROM utilisateur)                                     AS nb_utilisateurs,
            (SELECT COUNT(*) FROM utilisateur WHERE actif)                         AS nb_actifs,
            (SELECT COUNT(*) FROM utilisateur WHERE poids_initial_kg IS NULL)      AS users_sans_poids,
            (SELECT COUNT(*) FROM utilisateur WHERE taille_cm IS NULL)             AS users_sans_taille,
            (SELECT COUNT(*) FROM aliment)                                         AS nb_aliments,
            (SELECT COUNT(*) FROM aliment WHERE calories_100g = 0)                 AS aliments_calories_nulles,
            (SELECT COUNT(*) FROM exercice)                                        AS nb_exercices,
            (SELECT COUNT(*) FROM metrique_quotidienne)                            AS nb_metriques,
            (SELECT COUNT(*) FROM metrique_quotidienne WHERE poids_kg IS NULL)     AS metriques_sans_poids,
            (SELECT COUNT(*) FROM etl_run_log)                                     AS nb_runs_etl
    """)

    dernier_run = fetch_one(
        "SELECT run_id, started_at, statut, duree_secondes, nb_etl_succes, nb_etl_erreur "
        "FROM etl_run_log ORDER BY started_at DESC LIMIT 1"
    )

    return {
        "statistiques":  stats,
        "dernier_run_etl": dernier_run,
        "score_qualite": _calcul_score(stats),
    }


def _calcul_score(s: dict | None) -> int:
    if not s:
        return 0
    nb_u = s["nb_utilisateurs"] or 1
    nb_a = s["nb_aliments"] or 1
    nb_m = s["nb_metriques"] or 1
    score = 100
    score -= min(30, int((s["users_sans_poids"] / nb_u) * 30))
    score -= min(20, int((s["aliments_calories_nulles"] / nb_a) * 20))
    score -= min(20, int((s["metriques_sans_poids"] / nb_m) * 20))
    return max(0, score)


# ================================================================
# WORKFLOW VALIDATION / APPROBATION
# ================================================================

# Table légère en mémoire pour la démo (en prod : table DB dédiée)
_pending_approvals: list[dict] = []


@router.get("/approvals", tags=["administration"], summary="Anomalies en attente de validation")
def list_approvals():
    """Retourne les anomalies détectées nécessitant une action manuelle."""
    anomalies = fetch_all("""
        SELECT 'utilisateur' AS table_cible, id AS record_id,
               email AS detail, 'poids manquant' AS motif
        FROM utilisateur WHERE poids_initial_kg IS NULL
        UNION ALL
        SELECT 'aliment', id, nom, 'calories à 0'
        FROM aliment WHERE calories_100g = 0
        LIMIT 100
    """)
    return {"anomalies": anomalies, "total": len(anomalies)}


@router.post("/approvals/{table}/{record_id}/approve", tags=["administration"])
def approve_record(table: str, record_id: int, valeur: float = Query(..., description="Valeur corrigée")):
    """Corrige manuellement une anomalie et l'approuve."""
    allowed = {
        "utilisateur": "UPDATE utilisateur SET poids_initial_kg = :v WHERE id = :id",
        "aliment":     "UPDATE aliment SET calories_100g = :v WHERE id = :id",
    }
    if table not in allowed:
        raise HTTPException(400, f"Table non supportée : {table}")
    n = execute(allowed[table], {"v": valeur, "id": record_id})
    if n == 0:
        raise HTTPException(404, "Enregistrement introuvable")
    return {"message": f"{table} #{record_id} corrigé → {valeur}"}


# ================================================================
# EXPORT JSON / CSV
# ================================================================

EXPORT_QUERIES: dict[str, str] = {
    "utilisateurs": "SELECT id, nom, prenom, email, sexe, poids_initial_kg, taille_cm, abonnement, imc, actif FROM utilisateur ORDER BY id",
    "aliments":     "SELECT id, nom, categorie, calories_100g, proteines_g, glucides_g, lipides_g, fibres_g, source_dataset FROM aliment ORDER BY nom",
    "exercices":    "SELECT id, nom, type, niveau, equipement, description, source_dataset FROM exercice ORDER BY nom",
    "metriques":    "SELECT id, utilisateur_id, date_mesure, poids_kg, bpm_repos, bpm_max, calories_brulees, body_fat_pct FROM metrique_quotidienne ORDER BY date_mesure DESC",
}


@router.get("/export/{dataset}", tags=["export"], summary="Exporter un dataset (JSON ou CSV)")
def export_dataset(dataset: str, format: str = Query("json", enum=["json", "csv"])):
    if dataset not in EXPORT_QUERIES:
        raise HTTPException(400, f"Dataset inconnu. Choix : {list(EXPORT_QUERIES)}")

    rows = fetch_all(EXPORT_QUERIES[dataset])

    if format == "json":
        content = json.dumps(rows, ensure_ascii=False, indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={dataset}.json"},
        )

    # CSV
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={dataset}.csv"},
    )


# ================================================================
# ANALYTICS
# ================================================================

@router.get("/analytics/users", tags=["analytics"], summary="Répartition utilisateurs")
def analytics_users():
    return {
        "par_abonnement": fetch_all(
            "SELECT abonnement, COUNT(*) AS nb FROM utilisateur GROUP BY abonnement ORDER BY nb DESC"
        ),
        "par_sexe": fetch_all(
            "SELECT sexe, COUNT(*) AS nb FROM utilisateur GROUP BY sexe ORDER BY nb DESC"
        ),
        "par_objectif": fetch_all("""
            SELECT o.libelle, COUNT(*) AS nb
            FROM utilisateur_objectif uo
            JOIN objectif o ON o.id = uo.objectif_id
            GROUP BY o.libelle ORDER BY nb DESC
        """),
        "tranches_age": fetch_all("""
            SELECT
                CASE
                    WHEN age < 25 THEN '< 25'
                    WHEN age BETWEEN 25 AND 34 THEN '25-34'
                    WHEN age BETWEEN 35 AND 44 THEN '35-44'
                    WHEN age BETWEEN 45 AND 54 THEN '45-54'
                    ELSE '55+'
                END AS tranche,
                COUNT(*) AS nb
            FROM utilisateur
            WHERE age IS NOT NULL
            GROUP BY tranche ORDER BY tranche
        """),
    }


@router.get("/analytics/nutrition", tags=["analytics"], summary="Tendances nutritionnelles")
def analytics_nutrition():
    return {
        "top_calories": fetch_all(
            "SELECT nom, categorie, calories_100g FROM aliment ORDER BY calories_100g DESC LIMIT 10"
        ),
        "top_proteines": fetch_all(
            "SELECT nom, categorie, proteines_g FROM aliment ORDER BY proteines_g DESC LIMIT 10"
        ),
        "par_categorie": fetch_all("""
            SELECT categorie,
                   COUNT(*) AS nb_aliments,
                   ROUND(AVG(calories_100g)::numeric, 1) AS cal_moy,
                   ROUND(AVG(proteines_g)::numeric, 1) AS prot_moy
            FROM aliment WHERE categorie IS NOT NULL
            GROUP BY categorie ORDER BY nb_aliments DESC
        """),
    }


@router.get("/analytics/fitness", tags=["analytics"], summary="Statistiques fitness")
def analytics_fitness():
    return {
        "par_type": fetch_all(
            "SELECT type, COUNT(*) AS nb FROM exercice GROUP BY type ORDER BY nb DESC"
        ),
        "par_niveau": fetch_all(
            "SELECT niveau, COUNT(*) AS nb FROM exercice GROUP BY niveau ORDER BY nb DESC"
        ),
        "top_muscles": fetch_all("""
            SELECT gm.nom AS muscle, COUNT(*) AS nb_exercices
            FROM exercice_muscle em
            JOIN groupe_musculaire gm ON gm.id = em.muscle_id
            WHERE em.role = 'principal'
            GROUP BY gm.nom ORDER BY nb_exercices DESC LIMIT 10
        """),
        "calories_brulees_moy": fetch_one(
            "SELECT ROUND(AVG(calories_brulees)::numeric, 1) AS moy FROM metrique_quotidienne WHERE calories_brulees IS NOT NULL"
        ),
    }


@router.get("/analytics/kpis", tags=["analytics"], summary="KPIs business")
def analytics_kpis():
    return fetch_one("""
        SELECT
            COUNT(*)                                                                        AS total_utilisateurs,
            COUNT(*) FILTER (WHERE abonnement = 'freemium')                                AS nb_freemium,
            COUNT(*) FILTER (WHERE abonnement = 'premium')                                 AS nb_premium,
            COUNT(*) FILTER (WHERE abonnement = 'premium_plus')                            AS nb_premium_plus,
            ROUND(
                COUNT(*) FILTER (WHERE abonnement IN ('premium','premium_plus'))::numeric
                / NULLIF(COUNT(*),0) * 100, 2
            )                                                                              AS taux_conversion_pct,
            COUNT(*) FILTER (WHERE actif)                                                  AS utilisateurs_actifs,
            ROUND(AVG(imc)::numeric, 2)                                                    AS imc_moyen
        FROM utilisateur
    """)
