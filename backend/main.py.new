"""
Main backend application entry point
"""
import uvicorn
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.database import init_db, get_db
from backend.api import api_router
from backend.services.trading_service import trading_service
from backend.utils.error_handling import APIError, get_error_response

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return get_error_response(exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Invalid request parameters",
                "details": exc.errors()
            }
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "http_error",
                "message": exc.detail
            }
        },
        headers=exc.headers
    )

# Include API router
app.include_router(api_router)

# Custom OpenAPI docs endpoints
@app.get(f"{settings.API_PREFIX}/docs", include_in_schema=False)
async def get_swagger_documentation():
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        title=f"{settings.APP_NAME} - Swagger UI"
    )

@app.get(f"{settings.API_PREFIX}/redoc", include_in_schema=False)
async def get_redoc_documentation():
    return get_redoc_html(
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        title=f"{settings.APP_NAME} - ReDoc"
    )

# Health check endpoint
@app.get(f"{settings.API_PREFIX}/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Schedule background task to check orders
@app.on_event("startup")
async def schedule_order_check():
    async def periodic_order_check():
        while True:
            try:
                db = next(get_db())
                await trading_service.check_pending_orders(db)
            except Exception as e:
                print(f"Error checking orders: {e}")
            finally:
                await asyncio.sleep(60)  # Check every minute
    
    asyncio.create_task(periodic_order_check())

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
