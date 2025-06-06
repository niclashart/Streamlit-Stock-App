"""
Chat API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.config import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}/chat", tags=["chat"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}
