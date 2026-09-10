"""add description to events

Revision ID: d71a8f921b3e
Revises: cace293b009e
Create Date: 2026-09-10 23:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d71a8f921b3e"
down_revision = "cace293b009e"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if "events" in tables:
        columns = [c["name"] for c in inspector.get_columns("events")]
        if "description" not in columns:
            with op.batch_alter_table("events", schema=None) as batch_op:
                batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if "events" in tables:
        columns = [c["name"] for c in inspector.get_columns("events")]
        if "description" in columns:
            with op.batch_alter_table("events", schema=None) as batch_op:
                batch_op.drop_column("description")
