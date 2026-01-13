"""add partial unique student_id for active users

Revision ID: 74ade677d08c
Revises: 5fcd1010f071
Create Date: 2026-01-13 23:25:20.300369

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74ade677d08c'
down_revision: Union[str, Sequence[str], None] = '5fcd1010f071'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) 기존 UNIQUE(student_id) constraint가 있으면 제거
    op.execute("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname = 'users'
          AND c.contype = 'u'
          AND c.conname = 'users_student_id_key'
      ) THEN
        ALTER TABLE users DROP CONSTRAINT users_student_id_key;
      END IF;
    END $$;
    """)

    op.execute("DROP INDEX IF EXISTS ix_users_student_id;")
    op.execute("DROP INDEX IF EXISTS uq_users_student_id;")
    op.execute("DROP INDEX IF EXISTS users_student_id_key;")

    # 2) 활성 사용자만 student_id unique
    op.create_index(
        "uq_users_student_id_active",
        "users",
        ["student_id"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )


def downgrade():
    op.drop_index("uq_users_student_id_active", table_name="users")

    op.create_unique_constraint("users_student_id_key", "users", ["student_id"])
