"""init tables

Revision ID: 20251004_000001
Revises: 
Create Date: 2025-10-04 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251004_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "tickers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("sector", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "headlines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "mentions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("headline_id", sa.Integer(), nullable=False),
        sa.Column("ticker_id", sa.Integer(), nullable=False),
        sa.Column("context", sa.String(length=512), nullable=True),
        sa.Column("relevance", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["headline_id"], ["headlines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticker_id"], ["tickers.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_mentions_headline_id", "mentions", ["headline_id"], unique=False)
    op.create_index("ix_mentions_ticker_id", "mentions", ["ticker_id"], unique=False)

    op.create_table(
        "risk_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker_id", sa.Integer(), nullable=False),
        sa.Column("headline_id", sa.Integer(), nullable=True),
        sa.Column("model", sa.String(length=64), nullable=False, server_default=sa.text("'finbert'")),
        sa.Column("sentiment", sa.Float(), nullable=True),
        sa.Column("urgency", sa.Float(), nullable=True),
        sa.Column("volatility", sa.Float(), nullable=True),
        sa.Column("composite", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ticker_id"], ["tickers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["headline_id"], ["headlines.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_risk_scores_ticker_id", "risk_scores", ["ticker_id"], unique=False)
    op.create_index("ix_risk_scores_headline_id", "risk_scores", ["headline_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_risk_scores_headline_id", table_name="risk_scores")
    op.drop_index("ix_risk_scores_ticker_id", table_name="risk_scores")
    op.drop_table("risk_scores")

    op.drop_index("ix_mentions_ticker_id", table_name="mentions")
    op.drop_index("ix_mentions_headline_id", table_name="mentions")
    op.drop_table("mentions")

    op.drop_table("headlines")

    op.drop_table("tickers")

    op.drop_table("users")


