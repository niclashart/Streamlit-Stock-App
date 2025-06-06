"""
Module initialization for API routers
"""
from fastapi import APIRouter

from backend.api import auth, portfolio, stocks, trading, chat

# Create router
api_router = APIRouter()

# Include available API routers
api_router.include_router(auth.router)
api_router.include_router(portfolio.router)
api_router.include_router(stocks.router)
api_router.include_router(trading.router)
api_router.include_router(chat.router)
