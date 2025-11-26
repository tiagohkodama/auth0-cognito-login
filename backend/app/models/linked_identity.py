from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class LinkedIdentity(Base):
    __tablename__ = "linked_identities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    identity_provider = Column(String, nullable=False)  # 'cognito' or 'auth0'
    identity_id = Column(String, nullable=False)  # sub claim from provider
    provider_email = Column(String, nullable=False)
    linked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="linked_identities")

    # Ensure each identity can only be linked once
    __table_args__ = (
        UniqueConstraint('identity_provider', 'identity_id', name='uq_provider_identity'),
    )
