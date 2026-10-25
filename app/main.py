
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.api.classify_routes import create_classify_router
from app.exceptions import ModelUnavailableError
from app.models.classifier import MDeBERTaClassifier
from app.services.fake_classifier import FakeClassifier
from app.services.inference_service import InferenceService


logger = logging.getLogger(__name__)


# Varsayilan: FakeClassifier
# CLASSIFIER_BACKEND=real ise gercek AI modeli kullanilir.
classifier = (
    MDeBERTaClassifier()
    if os.getenv("CLASSIFIER_BACKEND", "fake").lower() == "real"
    else FakeClassifier()
)

service = InferenceService(classifier)


# Gercek modeli uygulama baslarken bir kez yukle.
@asynccontextmanager
async def lifespan(app: FastAPI):
    if isinstance(classifier, MDeBERTaClassifier):
        classifier.load()

    yield


app = FastAPI(
    title="CampusHub AI Service",
    version="1.0.0",
    description="CampusHub etkinlik siniflandirma API'si.",
    lifespan=lifespan,
)

app.include_router(create_classify_router(service))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request body must contain a non-empty string field: text",
        },
    )


@app.exception_handler(ModelUnavailableError)
async def model_unavailable_handler(
    request: Request,
    exc: ModelUnavailableError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "MODEL_UNAVAILABLE",
            "message": "AI model is not ready",
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unexpected error while processing request",
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
        },
    )


def custom_openapi():
    if app.openapi_schema is not None:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    responses = schema["paths"]["/ai/classify"]["post"]["responses"]
    responses.pop("422", None)

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
