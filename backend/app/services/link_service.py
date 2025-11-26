from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.linked_identity import LinkedIdentity
import uuid


class LinkService:
    """Service for account linking operations"""

    def can_link_identities(
        self,
        user_id: str,
        provider: str,
        identity_id: str,
        email: str,
        db: Session
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if identity can be linked
        Returns (can_link, error_message)
        """
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            return False, "User not found"

        # Email must match (case-insensitive)
        if user.email.lower() != email.lower():
            return False, "Email addresses do not match"

        # Check if this identity is already linked
        existing_link = db.query(LinkedIdentity).filter(
            LinkedIdentity.identity_provider == provider,
            LinkedIdentity.identity_id == identity_id
        ).first()

        if existing_link:
            if existing_link.user_id == uuid.UUID(user_id):
                return False, "This identity is already linked to your account"
            else:
                return False, "This identity is linked to another account"

        # Check if this is the user's primary identity
        if user.primary_identity_provider == provider and user.primary_identity_id == identity_id:
            return False, "Cannot link primary identity"

        return True, None

    def link_identity(
        self,
        user_id: str,
        provider: str,
        identity_id: str,
        email: str,
        db: Session
    ) -> Optional[LinkedIdentity]:
        """Link identity to user account"""
        can_link, error = self.can_link_identities(user_id, provider, identity_id, email, db)
        if not can_link:
            raise ValueError(error)

        linked_identity = LinkedIdentity(
            user_id=uuid.UUID(user_id),
            identity_provider=provider,
            identity_id=identity_id,
            provider_email=email.lower()
        )

        db.add(linked_identity)
        db.commit()
        db.refresh(linked_identity)
        return linked_identity

    def unlink_identity(self, user_id: str, provider: str, db: Session) -> bool:
        """Unlink identity from user account"""
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            return False

        # Cannot unlink primary identity
        if user.primary_identity_provider == provider:
            raise ValueError("Cannot unlink primary identity provider")

        # Find and delete linked identity
        linked_identity = db.query(LinkedIdentity).filter(
            LinkedIdentity.user_id == uuid.UUID(user_id),
            LinkedIdentity.identity_provider == provider
        ).first()

        if linked_identity:
            db.delete(linked_identity)
            db.commit()
            return True

        return False

    def get_linked_identities(self, user_id: str, db: Session) -> list:
        """Get all linked identities for a user"""
        return db.query(LinkedIdentity).filter(
            LinkedIdentity.user_id == uuid.UUID(user_id)
        ).all()
