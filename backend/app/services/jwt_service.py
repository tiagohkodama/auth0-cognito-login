from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.config import settings
from app.models.refresh_token import RefreshToken
from app.utils.security import generate_secure_token, hash_token
import uuid


class JWTService:
    """Service for JWT token operations"""

    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(self, user_id: str, email: str) -> str:
        """Create short-lived access token (15 minutes)"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": str(user_id),
            "email": email,
            "iat": datetime.utcnow(),
            "exp": expire,
            "iss": "auth-system",
            "aud": "auth-system-api",
            "type": "access"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str, db: Session) -> str:
        """Create long-lived refresh token (7 days) and store hash in database"""
        # Generate random token
        token = generate_secure_token(64)
        token_hash = hash_token(token)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        # Store hash in database
        refresh_token_record = RefreshToken(
            user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False
        )

        db.add(refresh_token_record)
        db.commit()

        return token

    def verify_access_token(self, token: str) -> Optional[Dict]:
        """Validate and decode access token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience="auth-system-api",
                issuer="auth-system"
            )

            # Verify token type
            if payload.get("type") != "access":
                return None

            return payload
        except JWTError:
            return None

    def verify_refresh_token(self, token: str, db: Session) -> Optional[Dict]:
        """Validate refresh token against database"""
        token_hash = hash_token(token)

        # Find token in database
        refresh_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False
        ).first()

        if not refresh_token:
            return None

        # Check if token is expired
        if datetime.utcnow() > refresh_token.expires_at:
            return None

        return {
            "sub": str(refresh_token.user_id),
            "token_id": str(refresh_token.id)
        }

    def revoke_refresh_token(self, token: str, db: Session) -> bool:
        """Revoke refresh token"""
        token_hash = hash_token(token)

        refresh_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        if refresh_token:
            refresh_token.revoked = True
            db.commit()
            return True

        return False

    def revoke_all_user_tokens(self, user_id: str, db: Session) -> None:
        """Revoke all refresh tokens for a user"""
        db.query(RefreshToken).filter(
            RefreshToken.user_id == uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        ).update({"revoked": True})
        db.commit()

    def rotate_refresh_token(self, old_token: str, user_id: str, db: Session) -> Optional[str]:
        """Revoke old refresh token and create new one"""
        # Revoke old token
        if not self.revoke_refresh_token(old_token, db):
            return None

        # Create new token
        return self.create_refresh_token(user_id, db)
