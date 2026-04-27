from fastapi import APIRouter, Request, Response
import httpx
import os

router = APIRouter()

KCAL_SERVICE_URL = os.getenv("KCAL_SERVICE_URL", "http://kcal:8001")
MEAL_SERVICE_URL = os.getenv("MEAL_SERVICE_URL", "http://meal:8003")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8004")
ETL_SERVICE_URL   = os.getenv("ETL_SERVICE_URL",   "http://etl:8002")
ADMIN_SERVICE_URL = os.getenv("ADMIN_SERVICE_URL", "http://admin:8005")

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


async def proxy_request(base_url: str, request: Request):
    async with httpx.AsyncClient() as client:
        url = f"{base_url}{request.url.path}"
        headers = dict(request.headers)
        headers.pop("host", None)
        body = await request.body()
        response = await client.request(
            request.method,
            url,
            headers=headers,
            content=body,
            params=request.query_params,
        )
        excluded_headers = {"content-encoding", "transfer-encoding", "content-length", "connection"}
        response_headers = {
            k: v
            for k, v in response.headers.items()
            if k.lower() not in excluded_headers
        }
        return Response(content=response.content, status_code=response.status_code, headers=response_headers)


@router.api_route("/meal", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def meal_root(request: Request):
    return await proxy_request(MEAL_SERVICE_URL, request)


@router.api_route("/meal/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def meal_proxy(path: str, request: Request):
    return await proxy_request(MEAL_SERVICE_URL, request)


@router.api_route("/auth", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def auth_root(request: Request):
    return await proxy_request(AUTH_SERVICE_URL, request)


@router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def auth_proxy(path: str, request: Request):
    return await proxy_request(AUTH_SERVICE_URL, request)


@router.api_route("/etl", methods=["GET", "POST"])
async def etl_root(request: Request):
    return await proxy_request(ETL_SERVICE_URL, request)


@router.api_route("/etl/{path:path}", methods=["GET", "POST"])
async def etl_proxy(path: str, request: Request):
    return await proxy_request(ETL_SERVICE_URL, request)


@router.api_route("/admin", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def admin_root(request: Request):
    return await proxy_request(ADMIN_SERVICE_URL, request)


@router.api_route("/admin/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def admin_proxy(path: str, request: Request):
    return await proxy_request(ADMIN_SERVICE_URL, request)
