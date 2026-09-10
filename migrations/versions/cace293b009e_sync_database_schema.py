"""sync database schema

Revision ID: cace293b009e
Revises: 17653df4dd0a
Create Date: 2026-09-10 22:05:42.154765

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cace293b009e"
down_revision = "17653df4dd0a"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create the users table required by the current User model.
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )

    # 2. Add owner_id and its foreign key to events.
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("owner_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_events_owner_id_users",
            "users",
            ["owner_id"],
            ["id"],
        )

    # 3. Add requester_id and rejection_reason to resource_requests.
    with op.batch_alter_table("resource_requests", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("requester_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("rejection_reason", sa.Text(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_resource_requests_requester_id_users",
            "users",
            ["requester_id"],
            ["id"],
        )

    # 4. Add request_id and its foreign key to allocations.
    with op.batch_alter_table("allocations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("request_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_allocations_request_id_resource_requests",
            "resource_requests",
            ["request_id"],
            ["id"],
        )


def downgrade():
    # Reverse allocations changes.
    with op.batch_alter_table("allocations", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_allocations_request_id_resource_requests",
            type_="foreignkey",
        )
        batch_op.drop_column("request_id")

    # Reverse resource_requests changes.
    with op.batch_alter_table("resource_requests", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_resource_requests_requester_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("rejection_reason")
        batch_op.drop_column("requester_id")

    # Reverse events changes.
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_events_owner_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("owner_id")

    # Remove users table last.
    op.drop_table("users")