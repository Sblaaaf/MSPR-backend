from fastapi import APIRouter, Request, Response
import httpx
import os

router = APIRouter()

KCAL_SERVICE_URL = os.getenv("KCAL_SERVICE_URL", "http://kcal:8001")

@router.api_route("/kcal/predict", methods=["POST"])
async def predict_kcal(request: Request):
    async with httpx.AsyncClient() as client:
        # Forward the request to the kcal service
        url = f"{KCAL_SERVICE_URL}/analyze"
        headers = dict(request.headers)
        # Remove host header to avoid issues
        headers.pop("host", None)
        body = await request.body()
        response = await client.post(url, headers=headers, content=body)
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))