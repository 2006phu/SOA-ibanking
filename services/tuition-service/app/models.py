import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    mssv: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    program: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    tuition_fees: Mapped[List["TuitionFee"]] = relationship(
        "TuitionFee",
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="TuitionFee.created_at.desc()",
    )


class TuitionFee(Base):
    __tablename__ = "tuition_fees"

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_tuition_fee_amount_positive"),
        CheckConstraint(
            "status IN ('UNPAID', 'PAID')", name="check_tuition_fee_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    mssv: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("students.mssv", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    semester: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(10), default="UNPAID", nullable=False
    )
    paid_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, nullable=True
    )
    paid_by_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, nullable=True
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    student: Mapped["Student"] = relationship(
        "Student", back_populates="tuition_fees"
    )
