import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SplitType(str, enum.Enum):
    EQUAL = "equal"
    UNEQUAL = "unequal"
    PERCENTAGE = "percentage"
    SHARE = "share"


class ExpenseStatus(str, enum.Enum):
    IMPORTED = "imported"
    WARNING = "warning"
    REJECTED = "rejected"


class ExpenseType(str, enum.Enum):
    EXPENSE = "expense"
    SETTLEMENT = "settlement"
    REFUND = "refund"


class AnomalySeverity(str, enum.Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AnomalyCategory(str, enum.Enum):
    DUPLICATE_EXPENSE = "DUPLICATE_EXPENSE"
    MISSING_PAYER = "MISSING_PAYER"
    MISSING_CURRENCY = "MISSING_CURRENCY"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    ZERO_AMOUNT = "ZERO_AMOUNT"
    AMOUNT_FORMAT_NORMALIZED = "AMOUNT_FORMAT_NORMALIZED"
    AMOUNT_PRECISION_NORMALIZED = "AMOUNT_PRECISION_NORMALIZED"
    AMBIGUOUS_DATE = "AMBIGUOUS_DATE"
    SETTLEMENT_TRANSACTION = "SETTLEMENT_TRANSACTION"
    REFUND_TRANSACTION = "REFUND_TRANSACTION"
    UNKNOWN_PARTICIPANT = "UNKNOWN_PARTICIPANT"
    STALE_PARTICIPANT = "STALE_PARTICIPANT"
    NAME_INCONSISTENCY = "NAME_INCONSISTENCY"
    CONFLICTING_SPLIT_INFO = "CONFLICTING_SPLIT_INFO"
    INVALID_PERCENTAGE_SPLIT = "INVALID_PERCENTAGE_SPLIT"
    MISSING_SPLIT_TYPE = "MISSING_SPLIT_TYPE"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Lowercased, stripped name used for deduplication lookups
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    expenses_paid: Mapped[list["Expense"]] = relationship(
        "Expense", back_populates="payer", foreign_keys="Expense.payer_id"
    )
    participations: Mapped[list["ExpenseParticipant"]] = relationship(
        "ExpenseParticipant", back_populates="user"
    )

    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_users_normalized_name"),
    )


# ---------------------------------------------------------------------------
# ImportReport
# ---------------------------------------------------------------------------

class ImportReport(Base):
    __tablename__ = "import_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # JSON blob storing the full machine-readable report
    report_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    expenses: Mapped[list["Expense"]] = relationship(
        "Expense", back_populates="import_report"
    )
    anomalies: Mapped[list["Anomaly"]] = relationship(
        "Anomaly", back_populates="import_report"
    )


# ---------------------------------------------------------------------------
# Expense
# ---------------------------------------------------------------------------

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    import_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Nullable: missing payer anomaly
    payer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Row number in the original CSV (1-indexed, excluding header)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    expense_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    split_type: Mapped[SplitType | None] = mapped_column(
        Enum(SplitType), nullable=True
    )
    expense_type: Mapped[ExpenseType] = mapped_column(
        Enum(ExpenseType), nullable=False, default=ExpenseType.EXPENSE
    )
    status: Mapped[ExpenseStatus] = mapped_column(
        Enum(ExpenseStatus), nullable=False, default=ExpenseStatus.IMPORTED
    )
    # Raw unparsed CSV row stored for audit purposes
    raw_row: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    import_report: Mapped["ImportReport"] = relationship(
        "ImportReport", back_populates="expenses"
    )
    payer: Mapped["User | None"] = relationship(
        "User", back_populates="expenses_paid", foreign_keys=[payer_id]
    )
    participants: Mapped[list["ExpenseParticipant"]] = relationship(
        "ExpenseParticipant", back_populates="expense", cascade="all, delete-orphan"
    )
    anomalies: Mapped[list["Anomaly"]] = relationship(
        "Anomaly", back_populates="expense"
    )

    __table_args__ = (
        Index("ix_expenses_import_date", "import_id", "expense_date"),
        Index("ix_expenses_payer_date", "payer_id", "expense_date"),
    )


# ---------------------------------------------------------------------------
# ExpenseParticipant
# ---------------------------------------------------------------------------

class ExpenseParticipant(Base):
    __tablename__ = "expense_participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Computed share amount (may be null for rejected expenses)
    share_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    share_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 4), nullable=True
    )
    share_weight: Mapped[int | None] = mapped_column(Integer, nullable=True)

    expense: Mapped["Expense"] = relationship("Expense", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="participations")

    __table_args__ = (
        UniqueConstraint("expense_id", "user_id", name="uq_participant_expense_user"),
    )


# ---------------------------------------------------------------------------
# Anomaly
# ---------------------------------------------------------------------------

class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    import_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Nullable: anomalies may be detected before an Expense record is created
    expense_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[AnomalyCategory] = mapped_column(
        Enum(AnomalyCategory), nullable=False, index=True
    )
    severity: Mapped[AnomalySeverity] = mapped_column(
        Enum(AnomalySeverity), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Raw CSV row JSON for full auditability
    raw_row: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    import_report: Mapped["ImportReport"] = relationship(
        "ImportReport", back_populates="anomalies"
    )
    expense: Mapped["Expense | None"] = relationship(
        "Expense", back_populates="anomalies"
    )

    __table_args__ = (
        Index("ix_anomalies_import_severity", "import_id", "severity"),
        Index("ix_anomalies_import_category", "import_id", "category"),
    )
