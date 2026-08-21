"""Create service requests table.

Revision ID: 20260821_01
Revises: 20260820_02
Create Date: 2026-08-21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260821_01"
down_revision: str | None = "20260820_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                "in_progress",
                "resolved",
                "closed",
                name="service_request_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="open",
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum(
                "low",
                "medium",
                "high",
                name="service_request_priority",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="medium",
            nullable=False,
        ),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("assigned_agent_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assigned_agent_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_requests_assigned_agent_id"),
        "service_requests",
        ["assigned_agent_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_service_requests_customer_id"),
        "service_requests",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_service_requests_priority"),
        "service_requests",
        ["priority"],
        unique=False,
    )
    op.create_index(
        op.f("ix_service_requests_status"),
        "service_requests",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_service_requests_status"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_priority"), table_name="service_requests")
    op.drop_index(
        op.f("ix_service_requests_customer_id"), table_name="service_requests"
    )
    op.drop_index(
        op.f("ix_service_requests_assigned_agent_id"),
        table_name="service_requests",
    )
    op.drop_table("service_requests")
