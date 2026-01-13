"""add DELETED to user 

Revision ID: 64ac096e193a
Revises: 93a16b0f4d5c
Create Date: 2026-01-13 20:52:02.988175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64ac096e193a'
down_revision: Union[str, Sequence[str], None] = '93a16b0f4d5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("users", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_is_deleted", "users", ["is_deleted"])

    # server_default 제거(선택) - DB에 기본값 남겨도 되는데 깔끔하게 하려면 제거 가능
    op.alter_column("users", "is_deleted", server_default=None)

def downgrade():
    op.drop_index("ix_users_is_deleted", table_name="users")
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "is_deleted")
