from fastapi import APIRouter, BackgroundTasks
from etl_pipeline import run_pipeline

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "healthai_etl"}

@router.post("/etl/run")
async def run_etl(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_pipeline)
    return {
        "status": "started",
        "message": "ETL pipeline has been started in the background. Check logs for progress."
    }
