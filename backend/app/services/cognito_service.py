from typing import Dict, Optional
from urllib.parse import urlencode
import httpx
from jose import jwt
from app.config import settings
from app.utils.security import generate_state_parameter


class CognitoService:
    """Service for AWS Cognito OAuth2 authentication (with Auth0 federation)"""

    def __init__(self):
        self.user_pool_id = settings.COGNITO_USER_POOL_ID
        self.client_id = settings.COGNITO_CLIENT_ID
        self.client_secret = settings.COGNITO_CLIENT_SECRET
        self.domain = settings.COGNITO_DOMAIN
        self.callback_url = settings.COGNITO_CALLBACK_URL
        self.region = settings.AWS_REGION

        # JWKS URL for token verification
        self.jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"

    def get_authorization_url(self, state: str) -> str:
        """Generate Cognito OAuth2 authorization URL"""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": self.callback_url,
            "state": state
        }

        return f"{self.domain}/oauth2/authorize?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for tokens"""
        token_url = f"{self.domain}/oauth2/token"

        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.callback_url
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error exchanging code for tokens: {e}")
                return None

    async def verify_id_token(self, id_token: str) -> Optional[Dict]:
        """Verify Cognito ID token JWT"""
        try:
            # In production, you would download and cache the JWKS
            # For now, we'll decode without verification for demo purposes
            # TODO: Implement proper JWKS verification
            unverified_claims = jwt.get_unverified_claims(id_token)

            # Basic validation
            if unverified_claims.get("aud") != self.client_id:
                return None

            if unverified_claims.get("iss") != f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}":
                return None

            return unverified_claims
        except Exception as e:
            print(f"Error verifying ID token: {e}")
            return None

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user info from Cognito UserInfo endpoint"""
        userinfo_url = f"{self.domain}/oauth2/userInfo"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error getting user info: {e}")
                return None

    async def revoke_token(self, token: str) -> bool:
        """Revoke token on Cognito side"""
        revoke_url = f"{self.domain}/oauth2/revoke"

        data = {
            "token": token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    revoke_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                print(f"Error revoking token: {e}")
                return False
