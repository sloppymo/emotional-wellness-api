"""Global error handling middleware for consistent error responses."""

import time
import traceback
from typing import Callable, Dict, Any
from uuid import uuid4

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from ..exceptions import BaseAPIException
from ..structured_logging import get_logger

logger = get_logger(__name__)


async def error_handling_middleware(request: Request, call_next: Callable) -> Response:
    """
    Global error handling middleware that catches all exceptions and returns
    consistent error responses.
    """
    request_id = str(uuid4())
    start_time = time.time()
    
    # Add request ID to request state for tracking
    request.state.request_id = request_id
    
    try:
        response = await call_next(request)
        
        # Log successful requests
        process_time = time.time() - start_time
        logger.info(
            f"Request completed successfully",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except BaseAPIException as e:
        # Handle our custom exceptions
        process_time = time.time() - start_time
        
        logger.warning(
            f"API Exception: {e.error_code} - {e.message}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error_code": e.error_code,
                "status_code": e.status_code,
                "details": e.details,
                "process_time": process_time
            }
        )
        
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": e.error_code,
                "message": e.message,
                "details": e.details,
                "request_id": request_id,
                "timestamp": time.time()
            },
            headers={"X-Request-ID": request_id}
        )
        
    except RequestValidationError as e:
        # Handle Pydantic validation errors
        process_time = time.time() - start_time
        
        logger.warning(
            f"Validation Error",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "errors": e.errors(),
                "process_time": process_time
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "errors": format_validation_errors(e.errors())
                },
                "request_id": request_id,
                "timestamp": time.time()
            },
            headers={"X-Request-ID": request_id}
        )
        
    except StarletteHTTPException as e:
        # Handle Starlette HTTP exceptions
        process_time = time.time() - start_time
        
        logger.info(
            f"HTTP Exception: {e.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": e.status_code,
                "detail": e.detail,
                "process_time": process_time
            }
        )
        
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": get_error_code_from_status(e.status_code),
                "message": str(e.detail),
                "request_id": request_id,
                "timestamp": time.time()
            },
            headers={"X-Request-ID": request_id}
        )
        
    except Exception as e:
        # Handle unexpected exceptions
        process_time = time.time() - start_time
        error_trace = traceback.format_exc()
        
        logger.error(
            f"Unhandled Exception: {str(e)}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": error_trace,
                "process_time": process_time
            }
        )
        
        # In production, don't expose internal error details
        if request.app.debug:
            error_details = {
                "type": type(e).__name__,
                "traceback": error_trace.split('\n')
            }
        else:
            error_details = {}
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": error_details,
                "request_id": request_id,
                "timestamp": time.time()
            },
            headers={"X-Request-ID": request_id}
        )


def format_validation_errors(errors: list) -> list:
    """Format Pydantic validation errors for API response."""
    formatted_errors = []
    
    for error in errors:
        formatted_error = {
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", ""),
            "type": error.get("type", "")
        }
        
        # Add input value if available (be careful with sensitive data)
        if "input" in error:
            formatted_error["input"] = error["input"]
            
        formatted_errors.append(formatted_error)
    
    return formatted_errors


def get_error_code_from_status(status_code: int) -> str:
    """Map HTTP status codes to error codes."""
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        410: "GONE",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    return error_code_map.get(status_code, "UNKNOWN_ERROR")


class ErrorResponseModel:
    """Model for consistent error responses."""
    
    def __init__(
        self,
        error: str,
        message: str,
        details: Dict[str, Any] = None,
        request_id: str = None,
        timestamp: float = None
    ):
        self.error = error
        self.message = message
        self.details = details or {}
        self.request_id = request_id or str(uuid4())
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "error": self.error,
            "message": self.message,
            "details": self.details,
            "request_id": self.request_id,
            "timestamp": self.timestamp
        }
    
    def to_json_response(self, status_code: int) -> JSONResponse:
        """Create JSONResponse from error model."""
        return JSONResponse(
            status_code=status_code,
            content=self.to_dict(),
            headers={"X-Request-ID": self.request_id}
        ) 