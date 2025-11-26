from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.cognito_service import CognitoService
from app.services.auth0_service import Auth0Service
from app.services.jwt_service import JWTService
from app.services.user_service import UserService
from app.schemas.auth import LoginResponse, TokenResponse, ErrorResponse
from app.utils.security import generate_state_parameter, hash_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

cognito_service = CognitoService()
auth0_service = Auth0Service()
jwt_service = JWTService()
user_service = UserService()

# In-memory state storage (use Redis in production)
state_storage = {}


@router.post("/login/cognito", response_model=LoginResponse)
async def login_cognito():
    """Initiate Cognito OAuth2 flow"""
    state = generate_state_parameter()
    state_storage[hash_token(state)] = {"provider": "cognito"}

    authorization_url = cognito_service.get_authorization_url(state)

    return LoginResponse(redirect_url=authorization_url)


@router.post("/login/auth0", response_model=LoginResponse)
async def login_auth0():
    """Initiate Auth0 OAuth2 flow"""
    state = generate_state_parameter()
    state_storage[hash_token(state)] = {"provider": "auth0"}

    authorization_url = auth0_service.get_authorization_url(state)

    return LoginResponse(redirect_url=authorization_url)


@router.get("/callback/cognito")
async def callback_cognito(
    code: str,
    state: str,
    response: Response,
    db: Session = Depends(get_db)
):
    """Handle Cognito OAuth2 callback"""
    # Verify state
    state_hash = hash_token(state)
    if state_hash not in state_storage:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    del state_storage[state_hash]

    # Exchange code for tokens
    tokens = await cognito_service.exchange_code_for_tokens(code)
    if not tokens:
        raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

    # Verify ID token
    id_token_claims = await cognito_service.verify_id_token(tokens["id_token"])
    if not id_token_claims:
        raise HTTPException(status_code=400, detail="Invalid ID token")

    # Get user info
    email = id_token_claims.get("email")
    identity_id = id_token_claims.get("sub")
    email_verified = id_token_claims.get("email_verified", False)

    # Get or create user
    user = user_service.get_user_by_identity("cognito", identity_id, db)

    if not user:
        user = user_service.create_user(
            email=email,
            provider="cognito",
            identity_id=identity_id,
            email_verified=email_verified,
            db=db
        )
    else:
        user_service.update_last_login(str(user.id), db)

    # Create application tokens
    access_token = jwt_service.create_access_token(str(user.id), user.email)
    refresh_token = jwt_service.create_refresh_token(str(user.id), db)

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="strict",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    # Redirect to frontend with access token
    frontend_url = f"{settings.FRONTEND_URL}?access_token={access_token}"
    return JSONResponse(
        content={"redirect_url": frontend_url},
        headers={"Location": frontend_url}
    )


@router.get("/callback/auth0")
async def callback_auth0(
    code: str,
    state: str,
    response: Response,
    db: Session = Depends(get_db)
):
    """Handle Auth0 OAuth2 callback"""
    # Verify state
    state_hash = hash_token(state)
    if state_hash not in state_storage:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    del state_storage[state_hash]

    # Exchange code for tokens
    tokens = await auth0_service.exchange_code_for_tokens(code)
    if not tokens:
        raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

    # Verify ID token
    id_token_claims = await auth0_service.verify_id_token(tokens["id_token"])
    if not id_token_claims:
        raise HTTPException(status_code=400, detail="Invalid ID token")

    # Get user info
    email = id_token_claims.get("email")
    identity_id = id_token_claims.get("sub")
    email_verified = id_token_claims.get("email_verified", False)

    # Get or create user
    user = user_service.get_user_by_identity("auth0", identity_id, db)

    if not user:
        user = user_service.create_user(
            email=email,
            provider="auth0",
            identity_id=identity_id,
            email_verified=email_verified,
            db=db
        )
    else:
        user_service.update_last_login(str(user.id), db)

    # Create application tokens
    access_token = jwt_service.create_access_token(str(user.id), user.email)
    refresh_token = jwt_service.create_refresh_token(str(user.id), db)

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="strict",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    # Redirect to frontend with access token
    frontend_url = f"{settings.FRONTEND_URL}?access_token={access_token}"
    return JSONResponse(
        content={"redirect_url": frontend_url},
        headers={"Location": frontend_url}
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token from cookie"""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )

    # Verify refresh token
    payload = jwt_service.verify_refresh_token(refresh_token, db)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = payload["sub"]
    user = user_service.get_user_by_id(user_id, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Create new access token
    new_access_token = jwt_service.create_access_token(str(user.id), user.email)

    # Optionally rotate refresh token
    new_refresh_token = jwt_service.rotate_refresh_token(refresh_token, str(user.id), db)
    if new_refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=settings.APP_ENV == "production",
            samesite="strict",
            max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

    return TokenResponse(access_token=new_access_token)


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Logout user and revoke tokens"""
    if refresh_token:
        # Revoke refresh token
        jwt_service.revoke_refresh_token(refresh_token, db)

    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token")

    return {"message": "Logged out successfully"}
