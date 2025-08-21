"""API request and response models for ShowAds service."""

from typing import Dict, List

from pydantic import BaseModel

class BaseRequestBody:
    pass

class AuthResponse(BaseModel, BaseRequestBody):
    """Response model for authentication endpoint."""
    AccessToken: str

class AuthRequest(BaseModel, BaseRequestBody):
    """Response model for authentication endpoint."""
    ProjectKey: str

class BulkRequest(BaseModel, BaseRequestBody):
    """Request model for bulk banner show endpoint."""
    Data: List[Dict[str, str | int]]

