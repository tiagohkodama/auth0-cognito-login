from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class LinkedIdentitySchema(BaseModel):
    """Linked identity information"""
    provider: str
    email: str
    linked_at: Optional[str] = None


class UserProfileResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    email_verified: bool
    primary_provider: str
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None
    linked_identities: List[LinkedIdentitySchema] = []
