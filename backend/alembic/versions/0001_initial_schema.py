"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-06-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    split_type = sa.Enum("equal", "unequal", "percentage", "share", name="splittype")
    expense_status = sa.Enum("imported", "warning", "rejected", name="expensestatus")
    expense_type = sa.Enum("expense", "settlement", "refund", name="expensetype")
    anomaly_severity = sa.Enum("error", "warning", "info", name="anomalyseverity")
    anomaly_category = sa.Enum(
        "DUPLICATE_EXPENSE", "MISSING_PAYER", "MISSING_CURRENCY",
        "INVALID_AMOUNT", "ZERO_AMOUNT", "AMOUNT_FORMAT_NORMALIZED",
        "AMOUNT_PRECISION_NORMALIZED", "AMBIGUOUS_DATE", "SETTLEMENT_TRANSACTION",
        "REFUND_TRANSACTION", "UNKNOWN_PARTICIPANT", "STALE_PARTICIPANT",
        "NAME_INCONSISTENCY", "CONFLICTING_SPLIT_INFO", "INVALID_PERCENTAGE_SPLIT",
        "MISSING_SPLIT_TYPE",
        name="anomalycategory",
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("normalized_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("is_guest", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("normalized_name", name="uq_users_normalized_name"),
    )
    op.create_index("ix_users_normalized_name", "users", ["normalized_name"])

    # import_reports
    op.create_table(
        "import_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("total_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("imported_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("warning_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("report_json", sa.Text, nullable=True),
    )

    # expenses
    op.create_table(
        "expenses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("import_id", UUID(as_uuid=True), sa.ForeignKey("import_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payer_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("expense_date", sa.Date, nullable=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("split_type", split_type, nullable=True),
        sa.Column("expense_type", expense_type, nullable=False, server_default="expense"),
        sa.Column("status", expense_status, nullable=False, server_default="imported"),
        sa.Column("raw_row", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_expenses_import_id", "expenses", ["import_id"])
    op.create_index("ix_expenses_payer_id", "expenses", ["payer_id"])
    op.create_index("ix_expenses_import_date", "expenses", ["import_id", "expense_date"])
    op.create_index("ix_expenses_payer_date", "expenses", ["payer_id", "expense_date"])

    # expense_participants
    op.create_table(
        "expense_participants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("expense_id", UUID(as_uuid=True), sa.ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("share_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("share_percentage", sa.Numeric(7, 4), nullable=True),
        sa.Column("share_weight", sa.Integer, nullable=True),
        sa.UniqueConstraint("expense_id", "user_id", name="uq_participant_expense_user"),
    )
    op.create_index("ix_participants_expense_id", "expense_participants", ["expense_id"])
    op.create_index("ix_participants_user_id", "expense_participants", ["user_id"])

    # anomalies
    op.create_table(
        "anomalies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("import_id", UUID(as_uuid=True), sa.ForeignKey("import_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expense_id", UUID(as_uuid=True), sa.ForeignKey("expenses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("category", anomaly_category, nullable=False),
        sa.Column("severity", anomaly_severity, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("resolution", sa.Text, nullable=True),
        sa.Column("raw_row", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_anomalies_import_id", "anomalies", ["import_id"])
    op.create_index("ix_anomalies_expense_id", "anomalies", ["expense_id"])
    op.create_index("ix_anomalies_import_severity", "anomalies", ["import_id", "severity"])
    op.create_index("ix_anomalies_import_category", "anomalies", ["import_id", "category"])


def downgrade() -> None:
    op.drop_table("anomalies")
    op.drop_table("expense_participants")
    op.drop_table("expenses")
    op.drop_table("import_reports")
    op.drop_table("users")

    for enum_name in ["splittype", "expensestatus", "expensetype", "anomalyseverity", "anomalycategory"]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
