
from datetime import UTC, datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.database import get_db_client

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Ping backend + MongoDB. Trả 200 nếu OK, 503 nếu Mongo down.",
)
async def health_check():
    mongo_status = "disconnected"
    mongo_error: str | None = None

    try:
        client = get_db_client()
        await client.admin.command("ping")
        mongo_status = "connected"
    except Exception as exc:
        mongo_error = f"{type(exc).__name__}: {exc}"

    payload: dict = {
        "status": "ok" if mongo_status == "connected" else "degraded",
        "mongo": mongo_status,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if mongo_error:
        payload["mongo_error"] = mongo_error

    http_code = (
        status.HTTP_200_OK
        if mongo_status == "connected"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(status_code=http_code, content=payload)