"""add users, sessions, and portfolio ownership

Introduces identity (US-13, ADR 0014) and scopes portfolios to a user.

Pre-release data note: portfolios created before this migration have no owner and cannot be
reached once every query is user-scoped. They are removed here rather than left orphaned
behind a nullable foreign key, which keeps the schema honest. There is no production data.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("token_hash", name="uq_user_sessions_token_hash"),
    )
    op.create_index("ix_user_sessions_token_hash", "user_sessions", ["token_hash"])
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])

    # Holdings cascade from portfolios, so removing unowned portfolios clears their rows too.
    op.execute("DELETE FROM holdings")
    op.execute("DELETE FROM portfolios")

    op.add_column("portfolios", sa.Column("user_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "fk_portfolios_user_id", "portfolios", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_portfolios_user_id", "portfolios", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_portfolios_user_id", table_name="portfolios")
    op.drop_constraint("fk_portfolios_user_id", "portfolios", type_="foreignkey")
    op.drop_column("portfolios", "user_id")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_index("ix_user_sessions_token_hash", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
