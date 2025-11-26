from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.user_service import UserService
from app.schemas.user import UserProfileResponse
from typing import Dict

router = APIRouter(prefix="/user", tags=["user"])

user_service = UserService()


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile with linked identities"""
    user_profile = user_service.get_user_profile(current_user["user_id"], db)

    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")

    return user_profile
