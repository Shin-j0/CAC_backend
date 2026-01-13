"""partial unique email for active users

Revision ID: 5fcd1010f071
Revises: 94fa9872b891
Create Date: 2026-01-13 22:38:02.168503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fcd1010f071'
down_revision: Union[str, Sequence[str], None] = '94fa9872b891'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) 기존 UNIQUE(email) constraint가 있으면 제거 (보통 users_email_key)
    #    환경마다 이름이 다를 수 있어서, 안전하게 존재할 때만 제거하도록 DO 블록 사용
    op.execute("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname = 'users'
          AND c.contype = 'u'
          AND c.conname = 'users_email_key'
      ) THEN
        ALTER TABLE users DROP CONSTRAINT users_email_key;
      END IF;
    END $$;
    """)

    # 2) 혹시 과거에 unique index로 만들어진 케이스도 대비해 드롭 (없으면 무시)
    op.execute("DROP INDEX IF EXISTS ix_users_email;")
    op.execute("DROP INDEX IF EXISTS uq_users_email;")
    op.execute("DROP INDEX IF EXISTS users_email_key;")  # 인덱스 이름인 경우 대비

    # 3) 활성 사용자만(email, is_deleted=false) unique 되도록 partial unique index 생성
    op.create_index(
        "uq_users_email_active",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )
    

def downgrade():
    # downgrade에서 partial index 제거
    op.drop_index("uq_users_email_active", table_name="users")
    
    # 기존과 동일하게 모든 사용자에 대해 email unique 제약 복원
    op.create_unique_constraint("users_email_key", "users", ["email"])