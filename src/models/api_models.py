from typing import Dict, List

from pydantic import BaseModel


class AuthResponse(BaseModel):
    """Response model for authentication endpoint."""
    AccessToken: str


class BulkRequest(BaseModel):
    """Request model for bulk banner show endpoint."""
    Data: List[Dict[str, str | int]]

