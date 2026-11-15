"""
E2E concurrency test (chạy qua API Gateway, hệ thống phải đang chạy bằng Docker Compose).

Hai kịch bản đúng theo rubric:
  1. CÙNG MỘT TÀI KHOẢN gửi 2 giao dịch đồng thời cho 2 khoản học phí KHÁC NHAU,
     tổng tiền > số dư  -> chỉ 1 giao dịch thành công, số dư không bao giờ âm.
  2. HAI TÀI KHOẢN KHÁC NHAU cùng thanh toán MỘT khoản học phí cùng lúc
     -> chỉ 1 thành công, người còn lại nhận 409 và được hoàn tiền (Saga compensation).

Script tự tạo sinh viên/khoản học phí mới cho mỗi lần chạy nên có thể chạy lặp lại
mà không cần reset dữ liệu. Thoát với exit code 1 nếu có kịch bản không đạt.

OTP: lấy từ response nếu OTP_DEBUG_EXPOSE=true, ngược lại đọc trực tiếp từ otp_db
bằng `docker compose exec postgres psql` (OTP không bao giờ lộ ra API ở chế độ demo).

Chạy:  python scripts/test_concurrency_scenarios.py
"""
import asyncio
import subprocess
import sys
import time
import uuid
from decimal import Decimal

import httpx

API_URL = "http://localhost:8000/api"
TUITION_SERVICE_URL = "http://localhost:8003"  # internal API, chỉ dùng để tạo dữ liệu test
PG_USER = "ibanking"

SCENARIO_1_USER = ("levanc", "password123")
SCENARIO_2_USERS = [("lephu", "235780"), ("nguyenvana", "password123")]


# ----------------------------------------------------------------- helpers
async def login(client: httpx.AsyncClient, username: str, password: str) -> str:
    res = await client.post(f"{API_URL}/auth/login", json={"username": username, "password": password})
    res.raise_for_status()
    return res.json()["access_token"]


async def get_balance(client: httpx.AsyncClient, token: str) -> Decimal:
    res = await client.get(f"{API_URL}/users/me/balance", headers={"Authorization": f"Bearer {token}"})
    res.raise_for_status()
    return Decimal(str(res.json()["balance"]))


async def create_test_fees(client: httpx.AsyncClient, amounts: list[Decimal]) -> tuple[str, list[str]]:
    """Tạo 1 sinh viên test mới + các khoản học phí UNPAID, trả về (mssv, [fee_id])."""
    mssv = "T" + uuid.uuid4().hex[:9].upper()
    res = await client.post(
        f"{TUITION_SERVICE_URL}/api/tuition/students",
        json={"mssv": mssv, "full_name": f"Concurrency Test {mssv}", "program": "QA"},
    )
    res.raise_for_status()
    for i, amount in enumerate(amounts, 1):
        res = await client.post(
            f"{TUITION_SERVICE_URL}/api/tuition/fees",
            json={"mssv": mssv, "semester": f"TEST-{i}", "amount": float(amount)},
        )
        res.raise_for_status()
    res = await client.get(f"{API_URL}/tuition/{mssv}")
    res.raise_for_status()
    fee_ids = [f["id"] for f in sorted(res.json()["tuition_fees"], key=lambda f: f["semester"])]
    return mssv, fee_ids


def read_otp_from_db(txn_id: str) -> str | None:
    cmd = [
        "docker", "compose", "exec", "-T", "postgres", "psql", "-U", PG_USER, "-d", "otp_db",
        "-tAc", f"SELECT code FROM otp_codes WHERE transaction_id = '{txn_id}'",
    ]
    out = subprocess.run(cmd, capture_output=True, text=True)
    return out.stdout.strip() or None


async def full_payment(token: str, mssv: str, fee_id: str, label: str) -> tuple[bool, int, str]:
    """initiate -> confirm (OTP gửi email) -> verify-otp. Trả về (success, http_status, detail)."""
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid.uuid4())}
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        res = await client.post(f"{API_URL}/payments/initiate", json={"mssv": mssv, "tuition_fee_id": fee_id})
        if res.status_code != 201:
            print(f"  [{label}] initiate bị từ chối ({res.status_code}): {res.text}")
            return False, res.status_code, res.text
        txn_id = res.json()["transaction_id"]

        res = await client.post(f"{API_URL}/payments/{txn_id}/confirm")
        if res.status_code != 200:
            print(f"  [{label}] confirm bị từ chối ({res.status_code}): {res.text}")
            return False, res.status_code, res.text

        otp = res.json().get("otp_code") or await asyncio.to_thread(read_otp_from_db, txn_id)
        if not otp:
            print(f"  [{label}] không lấy được OTP cho {txn_id}")
            return False, 0, "OTP unavailable"

        res = await client.post(f"{API_URL}/payments/{txn_id}/verify-otp", json={"otp_code": otp})
        ok = res.status_code == 200
        print(f"  [{label}] {'THÀNH CÔNG' if ok else 'BỊ TỪ CHỐI'} ({res.status_code}): {res.text[:140]}")
        return ok, res.status_code, res.text


def check(cond: bool, msg: str, failures: list[str]) -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {msg}")
    if not cond:
        failures.append(msg)


# --------------------------------------------------------------- scenarios
async def scenario_1_same_account(failures: list[str]) -> None:
    print("\n" + "=" * 72)
    print("KỊCH BẢN 1: 1 tài khoản, 2 giao dịch đồng thời, tổng tiền > số dư")
    print("=" * 72)
    async with httpx.AsyncClient(timeout=30.0) as client:
        token = await login(client, *SCENARIO_1_USER)
        before = await get_balance(client, token)
        if before < Decimal("2000"):
            failures.append("Scenario 1: số dư levanc quá thấp, hãy chạy lại seed_data.py")
            print("  Số dư quá thấp để test, bỏ qua.")
            return
        fee_amount = (before * Decimal("0.6")).quantize(Decimal("1"))  # 2 x 60% = 120% số dư
        mssv, fee_ids = await create_test_fees(client, [fee_amount, fee_amount])
        print(f"  Số dư ban đầu: {before:,.0f} VND | 2 khoản học phí, mỗi khoản {fee_amount:,.0f} VND")

        results = await asyncio.gather(
            full_payment(token, mssv, fee_ids[0], "Luồng 1"),
            full_payment(token, mssv, fee_ids[1], "Luồng 2"),
        )
        after = await get_balance(client, token)

    successes = sum(1 for ok, _, _ in results if ok)
    print(f"  Số dư sau: {after:,.0f} VND")
    check(successes == 1, f"đúng 1 giao dịch thành công (thực tế {successes})", failures)
    check(after >= 0, "số dư không âm", failures)
    check(after == before - fee_amount, "số dư chỉ bị trừ đúng 1 lần", failures)
    check(all(code in (200, 400) for _, code, _ in results), "giao dịch bị từ chối trả 400 (không phải 500)", failures)


async def scenario_2_same_fee(failures: list[str]) -> None:
    print("\n" + "=" * 72)
    print("KỊCH BẢN 2: 2 tài khoản cùng thanh toán 1 khoản học phí cùng lúc")
    print("=" * 72)
    async with httpx.AsyncClient(timeout=30.0) as client:
        tokens = [await login(client, u, p) for u, p in SCENARIO_2_USERS]
        before = [await get_balance(client, t) for t in tokens]
        amount = Decimal("1000000")
        mssv, (fee_id,) = await create_test_fees(client, [amount])
        print(f"  Khoản học phí {amount:,.0f} VND (MSSV {mssv})")

        results = await asyncio.gather(*[
            full_payment(t, mssv, fee_id, u) for t, (u, _) in zip(tokens, SCENARIO_2_USERS)
        ])
        after = [await get_balance(client, t) for t in tokens]
        fee = (await client.get(f"{TUITION_SERVICE_URL}/api/tuition/fee/{fee_id}")).json()

    successes = sum(1 for ok, _, _ in results if ok)
    spent = sum(b - a for b, a in zip(before, after))
    check(successes == 1, f"đúng 1 tài khoản thanh toán thành công (thực tế {successes})", failures)
    check(fee.get("status") == "PAID", "khoản học phí ở trạng thái PAID", failures)
    check(spent == amount, f"tổng tiền bị trừ = 1 lần học phí (thực tế {spent:,.0f})", failures)
    check(all(code in (200, 409) for _, code, _ in results), "người đến sau nhận 409 Conflict", failures)


async def main() -> int:
    failures: list[str] = []
    start = time.perf_counter()
    await scenario_1_same_account(failures)
    await scenario_2_same_fee(failures)
    print("\n" + "=" * 72)
    if failures:
        print(f"KẾT QUẢ: {len(failures)} kiểm tra KHÔNG ĐẠT")
        for f in failures:
            print(f"   - {f}")
    else:
        print(f"KẾT QUẢ: TẤT CẢ KIỂM TRA ĐỀU ĐẠT ({time.perf_counter() - start:.1f}s)")
    return 1 if failures else 0


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(asyncio.run(main()))
