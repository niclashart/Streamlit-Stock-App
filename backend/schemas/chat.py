"""
Chat schemas
"""
from typing import List, Dict, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Chat message schema"""
    content: str
    role: str = "user"


class ChatRequest(BaseModel):
    """Chat request schema"""
    message: str
    ticker: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    """Chat response schema"""
    response: str
    timestamp: str
