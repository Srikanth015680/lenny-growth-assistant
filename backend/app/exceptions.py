from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.logging_config import get_logger


logger = get_logger(__name__)


class AppError(Exception):
    code = "INTERNAL_ERROR"
    http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
    ):
        self.message = message

        if code:
            self.code = code

        super().__init__(message)


class SessionNotFoundError(AppError):
    code = "SESSION_NOT_FOUND"
    http_status = status.HTTP_404_NOT_FOUND


class InvalidMessageError(AppError):
    code = "INVALID_MESSAGE"
    http_status = status.HTTP_400_BAD_REQUEST


class OllamaUnavailableError(AppError):
    code = "OLLAMA_UNAVAILABLE"
    http_status = status.HTTP_503_SERVICE_UNAVAILABLE


class OllamaTimeoutError(AppError):
    code = "OLLAMA_TIMEOUT"
    http_status = status.HTTP_504_GATEWAY_TIMEOUT


class AnthropicUnavailableError(AppError):
    code = "ANTHROPIC_UNAVAILABLE"
    http_status = status.HTTP_503_SERVICE_UNAVAILABLE


class ProviderNotConfiguredError(AppError):
    code = "PROVIDER_NOT_CONFIGURED"
    http_status = status.HTTP_400_BAD_REQUEST


class EmbeddingError(AppError):
    code = "EMBEDDING_FAILED"
    http_status = status.HTTP_502_BAD_GATEWAY


class RetrievalError(AppError):
    code = "RETRIEVAL_FAILED"
    http_status = status.HTTP_502_BAD_GATEWAY


class ArtifactGenerationError(AppError):
    code = "ARTIFACT_GENERATION_FAILED"
    http_status = status.HTTP_502_BAD_GATEWAY


class InvalidArtifactError(AppError):
    code = "INVALID_ARTIFACT"
    http_status = status.HTTP_400_BAD_REQUEST


class ModeNotImplementedError(AppError):
    code = "MODE_NOT_IMPLEMENTED"
    http_status = status.HTTP_501_NOT_IMPLEMENTED


class InsufficientContextError(AppError):
    code = "INSUFFICIENT_CONTEXT"
    http_status = status.HTTP_422_UNPROCESSABLE_CONTENT


class DatabaseUnavailableError(AppError):
    code = "DATABASE_UNAVAILABLE"
    http_status = status.HTTP_503_SERVICE_UNAVAILABLE


async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    logger.warning(
        "handled_app_error",
        extra={
            "error_code": exc.code,
            "path": str(request.url.path),
        },
    )

    return JSONResponse(
        status_code=exc.http_status,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        extra={
            "path": str(request.url.path),
            "exception_type": type(exc).__name__,
        },
        exc_info=exc,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Something went wrong processing your request.",
            }
        },
    )