"""
Error handling utilities for API endpoints
"""
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class APIError(Exception):
    """Base error class for API exceptions"""
    def __init__(
        self, 
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.headers = headers
        super().__init__(detail)


class NotFoundError(APIError):
    """Error raised when a resource is not found"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, error_code="not_found")


class BadRequestError(APIError):
    """Error raised when the request is invalid"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, error_code="bad_request")


class UnauthorizedError(APIError):
    """Error raised when the user is not authenticated"""
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="unauthorized",
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenError(APIError):
    """Error raised when the user doesn't have sufficient permissions"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, error_code="forbidden")


class ValidationError(APIError):
    """Error raised when validation fails"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail, error_code="validation_error")


class DatabaseError(APIError):
    """Error raised when there's a database-related issue"""
    def __init__(self, detail: str = "Database error occurred"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail, error_code="database_error")


class ExternalServiceError(APIError):
    """Error raised when an external service (e.g., stock data provider) fails"""
    def __init__(self, detail: str = "External service error"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail, error_code="external_service_error")


def get_error_response(error: APIError) -> JSONResponse:
    """Convert an APIError to a JSONResponse"""
    content = {
        "error": {
            "code": error.error_code,
            "message": error.detail
        }
    }
    
    return JSONResponse(
        status_code=error.status_code,
        content=content,
        headers=error.headers
    )
