"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-11-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('email_verified', sa.Boolean(), default=False),
        sa.Column('primary_identity_provider', sa.String(), nullable=False),
        sa.Column('primary_identity_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create linked_identities table
    op.create_table(
        'linked_identities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('identity_provider', sa.String(), nullable=False),
        sa.Column('identity_id', sa.String(), nullable=False),
        sa.Column('provider_email', sa.String(), nullable=False),
        sa.Column('linked_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        'uq_provider_identity',
        'linked_identities',
        ['identity_provider', 'identity_id']
    )

    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint('uq_token_hash', 'refresh_tokens', ['token_hash'])


def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_table('linked_identities')
    op.drop_table('users')
