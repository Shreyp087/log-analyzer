"""add public auth fields to users

Revision ID: a1f4c8d2e6b7
Revises: 0539ac7c9ad1
Create Date: 2026-03-06 21:45:00.000000

"""

from uuid import uuid4
from typing import Optional, Set

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1f4c8d2e6b7"
down_revision = "0539ac7c9ad1"
branch_labels = None
depends_on = None


def _derive_username(email: Optional[str], user_id: int, used: Set[str]) -> str:
    local = (email or "").split("@")[0].strip().lower()
    local = local or f"user{user_id}"
    candidate = local
    suffix = 1
    while candidate in used:
        candidate = f"{local}_{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("public_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("username", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("full_name", sa.String(length=255), nullable=True))

    bind = op.get_bind()
    metadata = sa.MetaData()
    users = sa.Table(
        "users",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(length=255)),
        sa.Column("public_id", sa.String(length=36)),
        sa.Column("username", sa.String(length=100)),
        sa.Column("full_name", sa.String(length=255)),
    )

    existing_rows = bind.execute(sa.select(users.c.id, users.c.email)).fetchall()
    used_usernames: Set[str] = set()
    for row in existing_rows:
        username = _derive_username(row.email, int(row.id), used_usernames)
        bind.execute(
            users.update()
            .where(users.c.id == row.id)
            .values(
                public_id=str(uuid4()),
                username=username,
                full_name=username.replace(".", " ").replace("_", " ").title(),
            )
        )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("public_id", existing_type=sa.String(length=36), nullable=False)
        batch_op.alter_column("username", existing_type=sa.String(length=100), nullable=False)
        batch_op.alter_column("full_name", existing_type=sa.String(length=255), nullable=False)
        batch_op.create_index(batch_op.f("ix_users_public_id"), ["public_id"], unique=True)
        batch_op.create_index(batch_op.f("ix_users_username"), ["username"], unique=True)


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_username"))
        batch_op.drop_index(batch_op.f("ix_users_public_id"))
        batch_op.drop_column("full_name")
        batch_op.drop_column("username")
        batch_op.drop_column("public_id")
