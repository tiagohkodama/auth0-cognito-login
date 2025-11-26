from pydantic import BaseModel
from typing import Optional


class LoginResponse(BaseModel):
    """Response for login initiation"""
    redirect_url: str


class TokenResponse(BaseModel):
    """Response containing access token"""
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    """User information from provider"""
    sub: str
    email: str
    email_verified: bool


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
