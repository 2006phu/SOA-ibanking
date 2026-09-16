"""
Seed data script for iBanking Tuition Payment System.
Run this after all services are up to populate initial data.

Usage:
    python scripts/seed_data.py
    
    Or via Docker:
    docker compose exec payment-service python /app/scripts/seed_data.py
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api"

# ============================================================
# Seed Users (will be created in Auth Service -> synced to User Service)
# ============================================================
SEED_USERS = [
    {
        "id": "55555555-5555-5555-5555-555555555555",
        "username": "lephu",
        "password": "235780",
        "full_name": "Lê Phú",
        "phone": "0987654321",
        "email": "lephu@tdtu.edu.vn",
        "balance": 80000000.00  # 80 triệu
    },
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "username": "nguyenvana",
        "password": "password123",
        "full_name": "Nguyễn Văn A",
        "phone": "0901234567",
        "email": "nguyenvana@gmail.com",
        "balance": 50000000.00  # 50 triệu
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "username": "tranthib",
        "password": "password123",
        "full_name": "Trần Thị B",
        "phone": "0912345678",
        "email": "tranthib@gmail.com",
        "balance": 30000000.00  # 30 triệu
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "username": "levanc",
        "password": "password123",
        "full_name": "Lê Văn C",
        "phone": "0923456789",
        "email": "levanc@gmail.com",
        "balance": 10000000.00  # 10 triệu (ít tiền - để test insufficient balance)
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "username": "phamthid",
        "password": "password123",
        "full_name": "Phạm Thị D",
        "phone": "0934567890",
        "email": "phamthid@gmail.com",
        "balance": 100000000.00  # 100 triệu
    },
]

# ============================================================
# Seed Students & Tuition Fees
# ============================================================
SEED_STUDENTS = [
    {
        "mssv": "52100001",
        "full_name": "Hoàng Minh Tuấn",
        "program": "Công nghệ thông tin",
        "tuition_fees": [
            {"semester": "HK1 2025-2026", "amount": 15000000.00, "status": "PAID"},
            {"semester": "HK2 2025-2026", "amount": 15500000.00, "status": "UNPAID"},
            {"semester": "HK1 2026-2027", "amount": 16000000.00, "status": "UNPAID"},
        ]
    },
    {
        "mssv": "52100002",
        "full_name": "Ngô Thị Mai Anh",
        "program": "Kỹ thuật phần mềm",
        "tuition_fees": [
            {"semester": "HK1 2025-2026", "amount": 14000000.00, "status": "PAID"},
            {"semester": "HK2 2025-2026", "amount": 14500000.00, "status": "UNPAID"},
        ]
    },
    {
        "mssv": "52100003",
        "full_name": "Đặng Văn Hùng",
        "program": "Khoa học máy tính",
        "tuition_fees": [
            {"semester": "HK2 2025-2026", "amount": 13000000.00, "status": "UNPAID"},
            {"semester": "HK1 2026-2027", "amount": 13500000.00, "status": "UNPAID"},
        ]
    },
    {
        "mssv": "52100004",
        "full_name": "Vũ Thị Hồng Nhung",
        "program": "Hệ thống thông tin",
        "tuition_fees": [
            {"semester": "HK2 2025-2026", "amount": 12000000.00, "status": "UNPAID"},
        ]
    },
    {
        "mssv": "52100005",
        "full_name": "Bùi Quang Vinh",
        "program": "Mạng máy tính",
        "tuition_fees": [
            {"semester": "HK1 2025-2026", "amount": 11000000.00, "status": "PAID"},
            {"semester": "HK2 2025-2026", "amount": 11500000.00, "status": "UNPAID"},
            {"semester": "HK1 2026-2027", "amount": 12000000.00, "status": "UNPAID"},
        ]
    },
    {
        "mssv": "52100006",
        "full_name": "Trương Thị Thanh Hà",
        "program": "Trí tuệ nhân tạo",
        "tuition_fees": [
            {"semester": "HK2 2025-2026", "amount": 18000000.00, "status": "UNPAID"},
        ]
    },
    {
        "mssv": "52100007",
        "full_name": "Lý Hoàng Long",
        "program": "Công nghệ thông tin",
        "tuition_fees": [
            {"semester": "HK2 2025-2026", "amount": 6000000.00, "status": "UNPAID"},
            {"semester": "HK1 2026-2027", "amount": 6500000.00, "status": "UNPAID"},
        ]
    },
    {
        "mssv": "52100008",
        "full_name": "Đinh Thị Kim Oanh",
        "program": "Kỹ thuật phần mềm",
        "tuition_fees": [
            {"semester": "HK2 2025-2026", "amount": 9000000.00, "status": "UNPAID"},
        ]
    },
    {
        "mssv": "52100009",
        "full_name": "Cao Đức Anh",
        "program": "An toàn thông tin",
        "tuition_fees": [
            {"semester": "HK1 2025-2026", "amount": 14000000.00, "status": "PAID"},
            {"semester": "HK2 2025-2026", "amount": 14500000.00, "status": "UNPAID"},
            {"semester": "HK1 2026-2027", "amount": 15000000.00, "status": "UNPAID"},
        ]
    },
    {
        "mssv": "52100010",
        "full_name": "Phan Văn Đức",
        "program": "Khoa học dữ liệu",
        "tuition_fees": [
            {"semester": "HK2 2025-2026", "amount": 16000000.00, "status": "UNPAID"},
        ]
    },
]


async def seed_auth_and_users():
    """Seed users into Auth Service (which will also sync to User Service)."""
    print("\n" + "="*60)
    print("🔐 Seeding Users (Auth Service + User Service)")
    print("="*60)
    
    async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=10.0) as client:
        for user in SEED_USERS:
            try:
                response = await client.post("/api/auth/seed-user", json=user)
                if response.status_code in (200, 201):
                    print(f"  ✅ Created user: {user['username']} (balance: {user['balance']:,.0f} VND)")
                elif response.status_code == 409:
                    print(f"  ⏭️  User already exists: {user['username']}")
                else:
                    print(f"  ❌ Failed to create {user['username']}: {response.status_code} {response.text}")
            except Exception as e:
                print(f"  ❌ Error creating {user['username']}: {e}")
    
    # Also seed into User Service
    async with httpx.AsyncClient(base_url="http://localhost:8002", timeout=10.0) as client:
        for user in SEED_USERS:
            try:
                user_data = {
                    "id": user["id"],
                    "full_name": user["full_name"],
                    "phone": user["phone"],
                    "email": user["email"],
                    "balance": user["balance"],
                }
                response = await client.post("/api/users/", json=user_data)
                if response.status_code in (200, 201):
                    print(f"  ✅ Synced to User Service: {user['full_name']}")
                elif response.status_code == 409:
                    print(f"  ⏭️  Already in User Service: {user['full_name']}")
                else:
                    print(f"  ❌ User Service sync failed: {response.status_code}")
            except Exception as e:
                print(f"  ❌ User Service sync error: {e}")


async def seed_students_and_tuition():
    """Seed students and tuition fees into Tuition Service."""
    print("\n" + "="*60)
    print("🎓 Seeding Students & Tuition Fees")
    print("="*60)
    
    async with httpx.AsyncClient(base_url="http://localhost:8003", timeout=10.0) as client:
        for student in SEED_STUDENTS:
            try:
                response = await client.post("/api/tuition/seed", json=student)
                if response.status_code in (200, 201):
                    unpaid = sum(1 for f in student["tuition_fees"] if f["status"] == "UNPAID")
                    total = sum(f["amount"] for f in student["tuition_fees"] if f["status"] == "UNPAID")
                    print(f"  ✅ {student['mssv']} - {student['full_name']}")
                    print(f"     {student['program']} | {unpaid} khoản UNPAID | Tổng: {total:,.0f} VND")
                elif response.status_code == 409:
                    print(f"  ⏭️  Already exists: {student['mssv']} - {student['full_name']}")
                else:
                    print(f"  ❌ Failed: {response.status_code} {response.text}")
            except Exception as e:
                print(f"  ❌ Error: {e}")


async def verify_seed():
    """Verify seed data by querying services."""
    print("\n" + "="*60)
    print("🔍 Verifying Seed Data")
    print("="*60)
    
    # Check auth
    async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=10.0) as client:
        try:
            response = await client.post("/api/auth/login", json={
                "username": "nguyenvana",
                "password": "password123"
            })
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Auth: Login works for 'nguyenvana'")
                print(f"     Token: {data['access_token'][:30]}...")
            else:
                print(f"  ❌ Auth: Login failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Auth check error: {e}")
    
    # Check tuition
    async with httpx.AsyncClient(base_url="http://localhost:8003", timeout=10.0) as client:
        try:
            response = await client.get("/api/tuition/52100001")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Tuition: Found student {data.get('student_name', 'N/A')} ({data.get('mssv', 'N/A')})")
            else:
                print(f"  ❌ Tuition: Lookup failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Tuition check error: {e}")
    
    print("\n" + "="*60)
    print("🎉 Seed complete!")
    print("="*60)
    print("\nTest accounts:")
    print("-" * 50)
    for user in SEED_USERS:
        print(f"  Username: {user['username']}")
        print(f"  Password: {user['password']}")
        print(f"  Balance:  {user['balance']:>15,.0f} VND")
        print()


async def main():
    print("🏦 iBanking Tuition Payment - Seed Data")
    print("=" * 60)
    
    await seed_auth_and_users()
    await seed_students_and_tuition()
    await verify_seed()


if __name__ == "__main__":
    asyncio.run(main())
