"""
Automated unit & integration tests for OTP Security and Payment Saga Orchestration.

Uses an in-memory SQLite async database (via aiosqlite) and mocked inter-service
HTTP / RabbitMQ clients so the entire test suite runs standalone in milliseconds
without requiring Docker containers.
"""

from __future__ import annotations

import importlib
import sys
import types
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_service_modules(service_dir_name: str, extra_submodules: list[str]):
    """Import a microservice's app package cleanly with a lightweight DB Base."""
    service_root = ROOT_DIR / "services" / service_dir_name / "app"

    # Clear any previous `app` modules so two services do not collide
    for mod_name in list(sys.modules.keys()):
        if mod_name == "app" or mod_name.startswith("app."):
            del sys.modules[mod_name]

    pkg = types.ModuleType("app")
    pkg.__path__ = [str(service_root)]
    sys.modules["app"] = pkg

    # Provide stub app.database to avoid initializing PostgreSQL/asyncpg engine on import
    db_mod = types.ModuleType("app.database")

    class Base(DeclarativeBase):
        pass

    db_mod.Base = Base
    db_mod.AsyncSession = AsyncSession
    sys.modules["app.database"] = db_mod

    loaded = {"Base": Base}
    for sub in extra_submodules:
        loaded[sub] = importlib.import_module(f"app.{sub}")

    # Clean up sys.modules after grabbing module references
    for mod_name in list(sys.modules.keys()):
        if mod_name == "app" or mod_name.startswith("app."):
            del sys.modules[mod_name]

    return loaded


_otp_mods = _load_service_modules("otp-service", ["config", "models", "schemas", "service"])
OTPBase = _otp_mods["Base"]
OTPCode = _otp_mods["models"].OTPCode
OTPGenerateRequest = _otp_mods["schemas"].OTPGenerateRequest
OTPVerifyRequest = _otp_mods["schemas"].OTPVerifyRequest
otp_service_mod = _otp_mods["service"]
otp_settings = _otp_mods["config"].settings
OTPService = otp_service_mod.OTPService

_pay_mods = _load_service_modules(
    "payment-service", ["config", "logger", "models", "rabbitmq", "schemas", "service"]
)
PayBase = _pay_mods["Base"]
Transaction = _pay_mods["models"].Transaction
payment_service_mod = _pay_mods["service"]
PaymentService = payment_service_mod.PaymentService


@pytest_asyncio.fixture
async def otp_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(OTPBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def payment_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(PayBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


def _make_http_status_error(status_code: int, body: dict, method: str = "PUT", url: str = "http://internal") -> httpx.HTTPStatusError:
    req = httpx.Request(method, url)
    resp = httpx.Response(status_code, json=body, request=req)
    return httpx.HTTPStatusError(f"HTTP {status_code}", request=req, response=resp)


# =========================================================================
# OTP Service Security & Lifecycle Tests
# =========================================================================


@pytest.mark.asyncio
async def test_otp_generation_hides_code_by_default(otp_db: AsyncSession):
    txn_id = uuid.uuid4()
    req = OTPGenerateRequest(transaction_id=txn_id, email="student@tdtu.edu.vn")

    with patch.object(otp_settings, "OTP_DEBUG_EXPOSE", False), patch.object(
        otp_service_mod.rabbitmq_client, "publish_otp", new=AsyncMock()
    ) as mock_pub:
        res = await OTPService.generate_otp(otp_db, req)

    assert res["transaction_id"] == txn_id
    assert res["otp_code"] is None, "OTP must not be leaked in API response when OTP_DEBUG_EXPOSE=False"

    row = (await otp_db.execute(select(OTPCode).where(OTPCode.transaction_id == txn_id))).scalar_one()
    assert len(row.code) == otp_settings.OTP_LENGTH
    assert row.code.isdigit()
    assert row.is_used is False
    assert row.failed_attempts == 0

    mock_pub.assert_awaited_once()
    assert mock_pub.call_args.kwargs["code"] == row.code
    assert mock_pub.call_args.kwargs["email"] == "student@tdtu.edu.vn"


@pytest.mark.asyncio
async def test_otp_verify_success_and_single_use(otp_db: AsyncSession):
    txn_id = uuid.uuid4()
    with patch.object(otp_service_mod.rabbitmq_client, "publish_otp", new=AsyncMock()):
        await OTPService.generate_otp(
            otp_db, OTPGenerateRequest(transaction_id=txn_id, email="user@tdtu.edu.vn")
        )

    row = (await otp_db.execute(select(OTPCode).where(OTPCode.transaction_id == txn_id))).scalar_one()
    code = row.code

    verify_res = await OTPService.verify_otp(otp_db, OTPVerifyRequest(transaction_id=txn_id, otp_code=code))
    assert verify_res == {"valid": True, "transaction_id": txn_id}

    await otp_db.refresh(row)
    assert row.is_used is True

    with pytest.raises(HTTPException) as exc_info:
        await OTPService.verify_otp(otp_db, OTPVerifyRequest(transaction_id=txn_id, otp_code=code))
    assert exc_info.value.status_code == 400
    assert "already used" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_otp_expired_rejected(otp_db: AsyncSession):
    txn_id = uuid.uuid4()
    expired_row = OTPCode(
        id=uuid.uuid4(),
        transaction_id=txn_id,
        code="123456",
        email="user@tdtu.edu.vn",
        is_used=False,
        failed_attempts=0,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        created_at=datetime.now(timezone.utc) - timedelta(minutes=6),
    )
    otp_db.add(expired_row)
    await otp_db.commit()

    with pytest.raises(HTTPException) as exc_info:
        await OTPService.verify_otp(otp_db, OTPVerifyRequest(transaction_id=txn_id, otp_code="123456"))
    assert exc_info.value.status_code == 400
    assert "expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_otp_brute_force_lockout_after_5_attempts(otp_db: AsyncSession):
    txn_id = uuid.uuid4()
    with patch.object(otp_service_mod.rabbitmq_client, "publish_otp", new=AsyncMock()):
        await OTPService.generate_otp(
            otp_db, OTPGenerateRequest(transaction_id=txn_id, email="victim@tdtu.edu.vn")
        )

    row = (await otp_db.execute(select(OTPCode).where(OTPCode.transaction_id == txn_id))).scalar_one()
    real_code = row.code
    wrong_code = "000000" if real_code != "000000" else "999999"

    for attempt in range(1, 6):
        with pytest.raises(HTTPException) as exc_info:
            await OTPService.verify_otp(otp_db, OTPVerifyRequest(transaction_id=txn_id, otp_code=wrong_code))
        assert exc_info.value.status_code == 401
        await otp_db.refresh(row)
        assert row.failed_attempts == attempt

    # 6th attempt even with the REAL code must be locked out with HTTP 429
    with pytest.raises(HTTPException) as lock_exc:
        await OTPService.verify_otp(otp_db, OTPVerifyRequest(transaction_id=txn_id, otp_code=real_code))
    assert lock_exc.value.status_code == 429
    assert "too many" in lock_exc.value.detail.lower()


# =========================================================================
# Payment Service Idempotency & Saga Compensation Tests
# =========================================================================


@pytest.mark.asyncio
async def test_payment_idempotency_key(payment_db: AsyncSession):
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    fee_id = uuid.uuid4()
    idem_key = f"idem-{uuid.uuid4()}"

    async def fake_call_service(method: str, url: str, **kwargs):
        if "/api/tuition/fee/" in url:
            return {
                "id": str(fee_id),
                "mssv": "52100001",
                "student_name": "Nguyen Van A",
                "amount": 15000000.0,
                "status": "UNPAID",
            }
        if "/balance" in url:
            return {"balance": 50000000.0}
        raise AssertionError(f"Unexpected call: {method} {url}")

    with patch.object(payment_service_mod, "call_service", side_effect=fake_call_service):
        tx1 = await PaymentService.initiate_payment(
            payment_db, user_id=user_a, mssv="52100001", tuition_fee_id=fee_id, idempotency_key=idem_key
        )
        tx2 = await PaymentService.initiate_payment(
            payment_db, user_id=user_a, mssv="52100001", tuition_fee_id=fee_id, idempotency_key=idem_key
        )

        assert tx1.id == tx2.id
        count = (await payment_db.execute(select(func.count()).select_from(Transaction))).scalar_one()
        assert count == 1

        with pytest.raises(HTTPException) as exc_info:
            await PaymentService.initiate_payment(
                payment_db, user_id=user_b, mssv="52100001", tuition_fee_id=fee_id, idempotency_key=idem_key
            )
        assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_payment_saga_happy_path(payment_db: AsyncSession):
    user_id = uuid.uuid4()
    fee_id = uuid.uuid4()
    calls: list[tuple[str, str, dict]] = []

    async def fake_call_service(method: str, url: str, **kwargs):
        calls.append((method, url, kwargs))
        if method == "GET" and f"/api/tuition/fee/{fee_id}" in url:
            return {
                "id": str(fee_id),
                "mssv": "52100002",
                "student_name": "Tran Thi B",
                "amount": 14500000.0,
                "status": "UNPAID",
            }
        if method == "GET" and url.endswith("/balance"):
            return {"balance": 80000000.0}
        if method == "POST" and "/api/otp/generate" in url:
            return {"otp_id": str(uuid.uuid4()), "otp_code": None}
        if method == "POST" and "/api/otp/verify" in url:
            return {"valid": True, "transaction_id": kwargs["json"]["transaction_id"]}
        if method == "PUT" and url.endswith("/balance"):
            return {"old_balance": 80000000.0, "new_balance": 65500000.0}
        if method == "PUT" and url.endswith("/pay"):
            return {"id": str(fee_id), "status": "PAID"}
        if method == "POST" and url.endswith("/transactions"):
            return {"id": str(uuid.uuid4())}
        if method == "GET" and url.endswith(f"/api/users/{user_id}"):
            return {"id": str(user_id), "email": "lephu@tdtu.edu.vn"}
        raise AssertionError(f"Unexpected call: {method} {url}")

    with patch.object(payment_service_mod, "call_service", side_effect=fake_call_service), patch.object(
        payment_service_mod.rabbitmq_client, "publish_payment_success", new=AsyncMock()
    ) as mock_mq:
        tx = await PaymentService.initiate_payment(
            payment_db, user_id=user_id, mssv="52100002", tuition_fee_id=fee_id
        )
        assert tx.status == "PENDING"

        tx, _ = await PaymentService.confirm_payment(
            payment_db, transaction_id=tx.id, user_id=user_id, email="lephu@tdtu.edu.vn"
        )
        assert tx.status == "OTP_SENT"

        tx = await PaymentService.verify_otp_and_pay(
            payment_db, transaction_id=tx.id, user_id=user_id, otp_code="654321"
        )

    assert tx.status == "SUCCESS"
    assert tx.user_balance_before == Decimal("80000000.00")
    assert tx.user_balance_after == Decimal("65500000.00")
    assert tx.completed_at is not None
    assert any(c[0] == "POST" and c[1].endswith("/transactions") for c in calls)
    mock_mq.assert_awaited_once()
    assert mock_mq.call_args.args[0]["email"] == "lephu@tdtu.edu.vn"


@pytest.mark.asyncio
async def test_payment_step_a_insufficient_balance_marks_failed_no_unbound_error(payment_db: AsyncSession):
    """Simulates Concurrency Scenario 1: concurrent deduction fails with 400 (must NOT crash with UnboundLocalError)."""
    user_id = uuid.uuid4()
    fee_id = uuid.uuid4()
    tx = Transaction(
        id=uuid.uuid4(),
        user_id=user_id,
        tuition_fee_id=fee_id,
        mssv="52100777",
        student_name="Nguyen Van C",
        amount=Decimal("6000000.00"),
        status="OTP_SENT",
        user_balance_before=Decimal("10000000.00"),
        created_at=datetime.now(timezone.utc),
    )
    payment_db.add(tx)
    await payment_db.commit()

    async def fake_call_service(method: str, url: str, **kwargs):
        if "/api/otp/verify" in url:
            return {"valid": True, "transaction_id": str(tx.id)}
        if method == "PUT" and url.endswith("/balance"):
            raise _make_http_status_error(
                400, {"detail": "Insufficient balance. Available: 4000000.00, Requested: 6000000.00"}
            )
        raise AssertionError(f"Unexpected call: {method} {url}")

    with patch.object(payment_service_mod, "call_service", side_effect=fake_call_service):
        with pytest.raises(HTTPException) as exc_info:
            await PaymentService.verify_otp_and_pay(
                payment_db, transaction_id=tx.id, user_id=user_id, otp_code="111222"
            )

    assert exc_info.value.status_code == 400
    assert "insufficient balance" in exc_info.value.detail.lower()

    await payment_db.refresh(tx)
    assert tx.status == "FAILED"
    assert tx.user_balance_after == tx.user_balance_before
    assert tx.completed_at is not None


@pytest.mark.asyncio
async def test_payment_step_b_tuition_conflict_triggers_saga_refund(payment_db: AsyncSession):
    """Simulates Concurrency Scenario 2: deduction succeeds then tuition pay hits 409 -> triggers Saga Refund."""
    user_id = uuid.uuid4()
    fee_id = uuid.uuid4()
    tx = Transaction(
        id=uuid.uuid4(),
        user_id=user_id,
        tuition_fee_id=fee_id,
        mssv="52100999",
        student_name="Tran Thi D",
        amount=Decimal("1000000.00"),
        status="OTP_SENT",
        user_balance_before=Decimal("50000000.00"),
        created_at=datetime.now(timezone.utc),
    )
    payment_db.add(tx)
    await payment_db.commit()

    balance_ops: list[dict] = []

    async def fake_call_service(method: str, url: str, **kwargs):
        if "/api/otp/verify" in url:
            return {"valid": True, "transaction_id": str(tx.id)}
        if method == "PUT" and url.endswith("/balance"):
            payload = kwargs.get("json", {})
            balance_ops.append(payload)
            if payload.get("operation") == "deduct":
                return {"old_balance": 50000000.0, "new_balance": 49000000.0}
            return {"old_balance": 49000000.0, "new_balance": 50000000.0}
        if method == "PUT" and url.endswith("/pay"):
            raise _make_http_status_error(409, {"detail": "Tuition fee already paid"})
        raise AssertionError(f"Unexpected call: {method} {url}")

    with patch.object(payment_service_mod, "call_service", side_effect=fake_call_service):
        with pytest.raises(HTTPException) as exc_info:
            await PaymentService.verify_otp_and_pay(
                payment_db, transaction_id=tx.id, user_id=user_id, otp_code="111222"
            )

    assert exc_info.value.status_code == 409
    assert "balance has been refunded" in exc_info.value.detail.lower()
    assert [op.get("operation") for op in balance_ops] == ["deduct", "refund"]
    assert balance_ops[1]["amount"] == 1000000.0

    await payment_db.refresh(tx)
    assert tx.status == "REFUNDED"
    assert tx.user_balance_after == tx.user_balance_before
    assert tx.completed_at is not None
