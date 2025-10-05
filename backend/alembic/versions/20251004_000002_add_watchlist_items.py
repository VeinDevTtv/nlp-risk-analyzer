"""add watchlist items

Revision ID: 20251004_000002
Revises: 20251004_000001
Create Date: 2025-10-04 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251004_000002"
down_revision = "20251004_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_watchlist_items_user_id", "watchlist_items", ["user_id"], unique=False)
    op.create_index("ix_watchlist_items_symbol", "watchlist_items", ["symbol"], unique=False)
    op.create_unique_constraint("uq_watchlist_user_symbol", "watchlist_items", ["user_id", "symbol"])


def downgrade() -> None:
    op.drop_constraint("uq_watchlist_user_symbol", "watchlist_items", type_="unique")
    op.drop_index("ix_watchlist_items_symbol", table_name="watchlist_items")
    op.drop_index("ix_watchlist_items_user_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")


