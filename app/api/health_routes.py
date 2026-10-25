from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.contracts import Classifier

SERVICE_NAME = "ai-service"
SERVICE_VERSION = "1.0.0"


def create_health_router(classifier: Classifier) -> APIRouter:
    router = APIRouter(tags=["Health"])

    @router.get(
        "/health",
        responses={
            200: {"description": "Model is loaded and service is ready"},
            503: {"description": "Model is still starting"},
        },
    )
    def health() -> JSONResponse:
        if not classifier.is_ready():
            return JSONResponse(
                status_code=503,
                content={
                    "service": SERVICE_NAME,
                    "status": "DOWN",
                    "error": "MODEL_STARTING",
                    "version": SERVICE_VERSION,
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "service": SERVICE_NAME,
                "status": "UP",
                "version": SERVICE_VERSION,
            },
        )

    return router
