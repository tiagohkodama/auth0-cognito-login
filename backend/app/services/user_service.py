from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.linked_identity import LinkedIdentity
import uuid


class UserService:
    """Service for user operations"""

    def get_user_by_id(self, user_id: str, db: Session) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == uuid.UUID(user_id)).first()

    def get_user_by_email(self, email: str, db: Session) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email.lower()).first()

    def get_user_by_identity(self, provider: str, identity_id: str, db: Session) -> Optional[User]:
        """Get user by identity provider and identity ID"""
        # Check primary identity
        user = db.query(User).filter(
            User.primary_identity_provider == provider,
            User.primary_identity_id == identity_id
        ).first()

        if user:
            return user

        # Check linked identities
        linked_identity = db.query(LinkedIdentity).filter(
            LinkedIdentity.identity_provider == provider,
            LinkedIdentity.identity_id == identity_id
        ).first()

        if linked_identity:
            return linked_identity.user

        return None

    def create_user(
        self,
        email: str,
        provider: str,
        identity_id: str,
        email_verified: bool,
        db: Session
    ) -> User:
        """Create new user"""
        user = User(
            email=email.lower(),
            email_verified=email_verified,
            primary_identity_provider=provider,
            primary_identity_id=identity_id,
            last_login_at=datetime.utcnow()
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update_last_login(self, user_id: str, db: Session) -> None:
        """Update user's last login timestamp"""
        user = self.get_user_by_id(user_id, db)
        if user:
            user.last_login_at = datetime.utcnow()
            db.commit()

    def get_user_profile(self, user_id: str, db: Session) -> Optional[dict]:
        """Get user profile with linked identities"""
        user = self.get_user_by_id(user_id, db)
        if not user:
            return None

        linked_identities = db.query(LinkedIdentity).filter(
            LinkedIdentity.user_id == uuid.UUID(user_id)
        ).all()

        return {
            "id": str(user.id),
            "email": user.email,
            "email_verified": user.email_verified,
            "primary_provider": user.primary_identity_provider,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "linked_identities": [
                {
                    "provider": li.identity_provider,
                    "email": li.provider_email,
                    "linked_at": li.linked_at.isoformat() if li.linked_at else None
                }
                for li in linked_identities
            ]
        }
