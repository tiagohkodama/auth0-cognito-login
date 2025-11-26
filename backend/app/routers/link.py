from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Dict
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.cognito_service import CognitoService
from app.services.auth0_service import Auth0Service
from app.services.link_service import LinkService
from app.schemas.auth import LoginResponse
from app.utils.security import generate_state_parameter, hash_token

router = APIRouter(prefix="/link", tags=["account-linking"])

cognito_service = CognitoService()
auth0_service = Auth0Service()
link_service = LinkService()

# In-memory state storage (use Redis in production)
link_state_storage = {}


@router.post("/start/{provider}", response_model=LoginResponse)
async def start_linking(
    provider: str,
    current_user: Dict = Depends(get_current_user)
):
    """Initiate account linking flow"""
    if provider not in ["cognito", "auth0"]:
        raise HTTPException(status_code=400, detail="Invalid provider")

    state = generate_state_parameter()
    link_state_storage[hash_token(state)] = {
        "provider": provider,
        "user_id": current_user["user_id"]
    }

    if provider == "cognito":
        authorization_url = cognito_service.get_authorization_url(state)
    else:
        authorization_url = auth0_service.get_authorization_url(state)

    return LoginResponse(redirect_url=authorization_url)


@router.get("/callback/{provider}")
async def link_callback(
    provider: str,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle account linking callback"""
    # Verify state
    state_hash = hash_token(state)
    if state_hash not in link_state_storage:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    state_data = link_state_storage[state_hash]
    del link_state_storage[state_hash]

    user_id = state_data["user_id"]

    # Exchange code for tokens
    if provider == "cognito":
        tokens = await cognito_service.exchange_code_for_tokens(code)
        if not tokens:
            raise HTTPException(status_code=400, detail="Failed to exchange code")

        id_token_claims = await cognito_service.verify_id_token(tokens["id_token"])
    else:
        tokens = await auth0_service.exchange_code_for_tokens(code)
        if not tokens:
            raise HTTPException(status_code=400, detail="Failed to exchange code")

        id_token_claims = await auth0_service.verify_id_token(tokens["id_token"])

    if not id_token_claims:
        raise HTTPException(status_code=400, detail="Invalid ID token")

    # Get identity information
    email = id_token_claims.get("email")
    identity_id = id_token_claims.get("sub")

    # Link identity
    try:
        link_service.link_identity(user_id, provider, identity_id, email, db)
        return {"message": f"Successfully linked {provider} account", "success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{provider}")
async def unlink_identity(
    provider: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlink identity provider from account"""
    if provider not in ["cognito", "auth0"]:
        raise HTTPException(status_code=400, detail="Invalid provider")

    try:
        success = link_service.unlink_identity(current_user["user_id"], provider, db)
        if success:
            return {"message": f"Successfully unlinked {provider} account"}
        else:
            raise HTTPException(status_code=404, detail="Linked identity not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
