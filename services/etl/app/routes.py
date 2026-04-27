import os
import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from etl_pipeline import run_pipeline, get_run_en_cours

router = APIRouter()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     os.getenv("DB_PORT",     "5432"),
    "dbname":   os.getenv("DB_NAME",     "healthai"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def _get_engine():
    url = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )
    return create_engine(url, pool_pre_ping=True)


# ------------------------------------------------------------------
# Santé du service
# ------------------------------------------------------------------

@router.get("/health", tags=["monitoring"])
async def health_check():
    return {"status": "ok", "service": "healthai_etl", "version": "2.0.0"}


# ------------------------------------------------------------------
# Déclenchement du pipeline
# ------------------------------------------------------------------

@router.post("/etl/run", tags=["etl"], summary="Déclenche le pipeline ETL en arrière-plan")
async def run_etl(background_tasks: BackgroundTasks):
    if get_run_en_cours():
        raise HTTPException(status_code=409, detail="Un pipeline est déjà en cours d'exécution.")
    background_tasks.add_task(run_pipeline, "manuel")
    return {
        "status":  "started",
        "message": "Pipeline ETL démarré en arrière-plan. Consultez /etl/status pour suivre l'avancement.",
    }


# ------------------------------------------------------------------
# Statut du run en cours
# ------------------------------------------------------------------

@router.get("/etl/status", tags=["etl"], summary="Statut du pipeline (run en cours ou dernier run)")
async def etl_status():
    run_actif = get_run_en_cours()
    if run_actif:
        return {"en_cours": True, **run_actif}

    # Pas de run actif → retourner le dernier run depuis la base
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT run_id, started_at, finished_at, statut,
                       nb_etl_total, nb_etl_succes, nb_etl_erreur,
                       duree_secondes, declencheur
                FROM etl_run_log
                ORDER BY started_at DESC
                LIMIT 1
            """)).mappings().fetchone()

        if row is None:
            return {"en_cours": False, "message": "Aucun run enregistré."}

        return {"en_cours": False, **dict(row)}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur base de données : {e}")


# ------------------------------------------------------------------
# Historique des runs
# ------------------------------------------------------------------

@router.get("/etl/history", tags=["etl"], summary="Historique des exécutions ETL")
async def etl_history(limit: int = 20):
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT run_id, started_at, finished_at, statut,
                       nb_etl_total, nb_etl_succes, nb_etl_erreur,
                       duree_secondes, declencheur
                FROM etl_run_log
                ORDER BY started_at DESC
                LIMIT :limit
            """), {"limit": limit}).mappings().fetchall()

        return {"runs": [dict(r) for r in rows], "total": len(rows)}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur base de données : {e}")


# ------------------------------------------------------------------
# Rapport de qualité du dernier run
# ------------------------------------------------------------------

@router.get("/etl/quality", tags=["etl"], summary="Rapport qualité du dernier run ETL")
async def etl_quality_report() -> Any:
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT run_id, started_at, statut, rapport_json
                FROM etl_run_log
                ORDER BY started_at DESC
                LIMIT 1
            """)).mappings().fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Aucun rapport disponible.")

        rapport = row["rapport_json"]
        if isinstance(rapport, str):
            rapport = json.loads(rapport)

        return {
            "run_id":     row["run_id"],
            "started_at": row["started_at"],
            "statut":     row["statut"],
            "rapports":   rapport,
        }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur base de données : {e}")


# ------------------------------------------------------------------
# Métriques de qualité en base (vue synthétique par table)
# ------------------------------------------------------------------

@router.get("/etl/data-quality", tags=["etl"], summary="Métriques de qualité des données en base")
async def data_quality_metrics():
    queries: dict[str, str] = {
        "utilisateurs":         "SELECT COUNT(*) FROM utilisateur",
        "aliments":             "SELECT COUNT(*) FROM aliment",
        "exercices":            "SELECT COUNT(*) FROM exercice",
        "metriques":            "SELECT COUNT(*) FROM metrique_quotidienne",
        "utilisateurs_actifs":  "SELECT COUNT(*) FROM utilisateur WHERE actif = TRUE",
        "nulls_poids_users":    "SELECT COUNT(*) FROM utilisateur WHERE poids_initial_kg IS NULL",
        "nulls_calories_alim":  "SELECT COUNT(*) FROM aliment WHERE calories_100g IS NULL OR calories_100g = 0",
    }

    try:
        engine = _get_engine()
        result: dict[str, Any] = {}
        with engine.connect() as conn:
            for cle, sql in queries.items():
                val = conn.execute(text(sql)).scalar()
                result[cle] = val
        return result

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Erreur base de données : {e}")
