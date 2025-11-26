from typing import Dict, Optional
from urllib.parse import urlencode
import httpx
from jose import jwt
from app.config import settings
from app.utils.security import generate_state_parameter


class Auth0Service:
    """Service for Auth0 OAuth2 authentication (Research Catalog)"""

    def __init__(self):
        self.domain = settings.AUTH0_RESEARCH_DOMAIN
        self.client_id = settings.AUTH0_RESEARCH_CLIENT_ID
        self.client_secret = settings.AUTH0_RESEARCH_CLIENT_SECRET
        self.callback_url = settings.AUTH0_RESEARCH_CALLBACK_URL

        # Auth0 URLs
        self.authorize_url = f"https://{self.domain}/authorize"
        self.token_url = f"https://{self.domain}/oauth/token"
        self.userinfo_url = f"https://{self.domain}/userinfo"
        self.jwks_url = f"https://{self.domain}/.well-known/jwks.json"

    def get_authorization_url(self, state: str) -> str:
        """Generate Auth0 OAuth2 authorization URL"""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": self.callback_url,
            "state": state,
            "audience": f"https://{self.domain}/api/v2/"
        }

        return f"{self.authorize_url}?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for tokens"""
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
                    self.token_url,
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error exchanging code for tokens: {e}")
                return None

    async def verify_id_token(self, id_token: str) -> Optional[Dict]:
        """Verify Auth0 ID token JWT"""
        try:
            # In production, you would download and cache the JWKS
            # For now, we'll decode without verification for demo purposes
            # TODO: Implement proper JWKS verification
            unverified_claims = jwt.get_unverified_claims(id_token)

            # Basic validation
            if unverified_claims.get("aud") != self.client_id:
                return None

            if unverified_claims.get("iss") != f"https://{self.domain}/":
                return None

            return unverified_claims
        except Exception as e:
            print(f"Error verifying ID token: {e}")
            return None

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user info from Auth0 UserInfo endpoint"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error getting user info: {e}")
                return None

    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke refresh token on Auth0 side"""
        revoke_url = f"https://{self.domain}/oauth/revoke"

        data = {
            "token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    revoke_url,
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                print(f"Error revoking token: {e}")
                return False
