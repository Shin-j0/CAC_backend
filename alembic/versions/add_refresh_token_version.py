"""add refresh_token_version to users

Revision ID: 516fa229371c
Revises: 74ade677d08c
Create Date: 2026-01-14 00:46:22.368867

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '516fa229371c'
down_revision: Union[str, Sequence[str], None] = '74ade677d08c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
