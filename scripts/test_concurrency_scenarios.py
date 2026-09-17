"""
Script kiểm thử Concurrency (Tranh chấp tài nguyên & Chống Race Condition)
Theo tiêu chí chấm điểm 10 SOA.

Bao gồm 2 kịch bản chính:
1. KỊCH BẢN 1: Nhiều giao dịch đồng thời trên CÙNG MỘT TÀI KHOẢN (Chống trừ tiền âm - Double Spending)
2. KỊCH BẢN 2: NHIỀU TÀI KHOẢN cùng thanh toán 1 KHOẢN HỌC PHÍ tại cùng một thời điểm (Chống thanh toán trùng)
"""
import asyncio
import httpx
import time

API_URL = "http://localhost:8000/api"

async def login(username, password):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{API_URL}/auth/login", json={"username": username, "password": password})
        res.raise_for_status()
        return res.json()["access_token"]

async def get_student_fee(mssv):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_URL}/tuition/{mssv}")
        res.raise_for_status()
        data = res.json()
        unpaid = [f for f in data.get("tuition_fees", []) if f["status"] == "UNPAID"]
        if not unpaid:
            return None, None
        return data["student_name"], unpaid[0]

async def execute_full_payment(token, mssv, fee_id, label="Tx"):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        # Bước 1: Initiate
        init_res = await client.post(f"{API_URL}/payments/initiate", json={
            "mssv": mssv,
            "tuition_fee_id": fee_id
        })
        if init_res.status_code != 201:
            print(f"[{label}] ❌ Khởi tạo thất bại ({init_res.status_code}): {init_res.text}")
            return False, init_res.text
        
        txn_id = init_res.json()["transaction_id"]
        
        # Bước 2: Confirm
        confirm_res = await client.post(f"{API_URL}/payments/{txn_id}/confirm")
        if confirm_res.status_code != 200:
            print(f"[{label}] ❌ Confirm thất bại ({confirm_res.status_code}): {confirm_res.text}")
            return False, confirm_res.text
        
        otp_code = confirm_res.json().get("otp_code")
        
        # Bước 3: Verify OTP & Pay
        verify_res = await client.post(f"{API_URL}/payments/{txn_id}/verify-otp", json={
            "otp_code": otp_code
        })
        if verify_res.status_code == 200:
            print(f"[{label}] ✅ Thanh toán THÀNH CÔNG!")
            return True, "SUCCESS"
        else:
            print(f"[{label}] ❌ Thanh toán BỊ TỪ CHỐI ({verify_res.status_code}): {verify_res.text}")
            return False, verify_res.text

async def scenario_1_same_account():
    print("\n" + "="*70)
    print("🚦 KỊCH BẢN 1: 1 TÀI KHOẢN GỬI 2 GIAO DỊCH ĐỒNG THỜI (TEST DOUBLE-SPENDING)")
    print("="*70)
    print("User 'levanc' có 10.000.000 VND.")
    print("Thực hiện 2 request thanh toán cùng lúc, mỗi khoản vượt quá số dư nếu cộng gộp.")
    
    token = await login("levanc", "password123")
    student_name, fee = await get_student_fee("52100777")
    
    if not fee:
        print("Khoản phí của sinh viên 52100777 đã được thanh toán hoặc không tìm thấy.")
        return

    print(f"-> Học phí mục tiêu: {fee['amount']:,.0f} VND (MSSV 52100777 - {student_name})")
    
    # Bắn 2 luồng đồng thời
    print("\n⚡ Đang gửi 2 giao dịch đồng thời tại cùng một tích tắc...")
    t1 = asyncio.create_task(execute_full_payment(token, "52100777", fee["id"], label="Luồng 1"))
    t2 = asyncio.create_task(execute_full_payment(token, "52100777", fee["id"], label="Luồng 2"))
    
    r1, r2 = await asyncio.gather(t1, t2)
    
    success_count = sum([1 for r in (r1, r2) if r[0]])
    print(f"\n=> Kết quả: {success_count}/2 giao dịch thành công.")
    if success_count == 1:
        print("🎯 ĐẠT TIÊU CHÍ: Hệ thống khóa dòng tiền (SELECT FOR UPDATE) chuẩn xác, ngăn chặn trừ tiền 2 lần!")
    else:
        print("⚠️ Cần kiểm tra lại kết quả.")

async def scenario_2_multiple_users_same_fee():
    print("\n" + "="*70)
    print("🚦 KỊCH BẢN 2: 2 TÀI KHOẢN KHÁC NHAU CÙNG THANH TOÁN 1 KHOẢN HỌC PHÍ CÙNG LÚC")
    print("="*70)
    print("User 1 ('lephu') và User 2 ('nguyenvana') cùng thanh toán cho 1 sinh viên tại cùng 1 thời điểm.")
    
    token_lephu = await login("lephu", "235780")
    token_nguyen = await login("nguyenvana", "password123")
    
    student_name, fee = await get_student_fee("52100999")
    if not fee:
        print("Khoản phí của sinh viên 52100999 đã được thanh toán hoặc không tìm thấy.")
        return

    print(f"-> Học phí mục tiêu: {fee['amount']:,.0f} VND (MSSV 52100999 - {student_name})")
    
    print("\n⚡ Đang gửi 2 request từ 2 user khác nhau cùng lúc...")
    t1 = asyncio.create_task(execute_full_payment(token_lephu, "52100999", fee["id"], label="User Lê Phú"))
    t2 = asyncio.create_task(execute_full_payment(token_nguyen, "52100999", fee["id"], label="User Nguyễn Văn A"))
    
    r1, r2 = await asyncio.gather(t1, t2)
    
    success_count = sum([1 for r in (r1, r2) if r[0]])
    print(f"\n=> Kết quả: {success_count}/2 user thanh toán thành công.")
    if success_count == 1:
        print("🎯 ĐẠT TIÊU CHÍ: Khóa học phí (Pessimistic Lock) thành công! Chỉ 1 người được thanh toán, người kia bị từ chối và tiền được bảo toàn!")
    else:
        print("⚠️ Cần kiểm tra lại kết quả.")

async def main():
    await scenario_1_same_account()
    await scenario_2_multiple_users_same_fee()

if __name__ == "__main__":
    asyncio.run(main())
