"""Add classifier detail columns to ai_systems."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_classifier_fields"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add D3 classifier columns to ai_systems."""

    op.add_column(
        "ai_systems",
        sa.Column("secondary_articles", postgresql.ARRAY(sa.Text()), nullable=True),
    )
    op.add_column(
        "ai_systems",
        sa.Column("deadline_iso", sa.Date(), nullable=True),
    )
    op.add_column(
        "ai_systems",
        sa.Column("triggers_article_50", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    """Remove D3 classifier columns from ai_systems."""

    op.drop_column("ai_systems", "triggers_article_50")
    op.drop_column("ai_systems", "deadline_iso")
    op.drop_column("ai_systems", "secondary_articles")
