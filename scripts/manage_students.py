"""
Công cụ quản lý & tra cứu dữ liệu Sinh viên / Học phí (CLI Tool)
Dùng để tra cứu danh sách, thêm sinh viên mới, hoặc reset trạng thái học phí để test lại.
"""
import sys
import argparse
import asyncio
import httpx

TUITION_SERVICE_URL = "http://localhost:8003"

async def list_students():
    import subprocess
    print("\n📋 DANH SÁCH TẤT CẢ SINH VIÊN VÀ HỌC PHÍ TRONG HỆ THỐNG:")
    print("=" * 85)
    cmd = 'docker compose exec postgres psql -U ibanking -d tuition_db -c "SELECT s.mssv, s.full_name, s.program, f.semester, f.amount, f.status FROM students s LEFT JOIN tuition_fees f ON s.mssv = f.mssv ORDER BY s.mssv;"'
    subprocess.run(cmd, shell=True)

async def add_student(mssv, name, program, semester, amount):
    print(f"\n➕ Đang thêm sinh viên: {mssv} - {name} ({amount:,.0f} VND)...")
    async with httpx.AsyncClient(base_url=TUITION_SERVICE_URL) as client:
        # 1. Tạo sinh viên
        try:
            res_student = await client.post("/api/tuition/students", json={
                "mssv": mssv,
                "full_name": name,
                "program": program
            })
            if res_student.status_code == 201:
                print(f"✅ Đã tạo hồ sơ sinh viên: {name}")
            elif res_student.status_code == 400:
                print(f"ℹ️ Sinh viên {mssv} đã tồn tại trong hệ thống, tiếp tục thêm khoản học phí.")
            else:
                print(f"❌ Lỗi tạo sinh viên: {res_student.text}")
                return
        except Exception as e:
            print(f"❌ Lỗi kết nối Tuition Service: {e}")
            return

        # 2. Tạo khoản học phí
        res_fee = await client.post("/api/tuition/fees", json={
            "mssv": mssv,
            "semester": semester,
            "amount": amount
        })
        if res_fee.status_code == 201:
            print(f"✅ Đã tạo thành công khoản nợ học phí {amount:,.0f} VND cho sinh viên {mssv} ({semester})!")
            print(f"👉 Bây giờ bạn có thể lên Web nhập MSSV '{mssv}' để tra cứu và thanh toán ngay!")
        else:
            print(f"❌ Lỗi tạo học phí: {res_fee.text}")

async def reset_all_to_unpaid():
    import subprocess
    print("\n🔄 Đang reset tất cả học phí về trạng thái UNPAID (chưa thanh toán) để test lại...")
    cmd = 'docker compose exec postgres psql -U ibanking -d tuition_db -c "UPDATE tuition_fees SET status=\'UNPAID\', paid_by_user_id=NULL, paid_by_transaction_id=NULL, paid_at=NULL;"'
    subprocess.run(cmd, shell=True)
    print("✅ Đã reset thành công! Tất cả sinh viên hiện đều đang nợ học phí để bạn thoải mái test.")

def main():
    parser = argparse.ArgumentParser(description="Quản lý sinh viên và học phí")
    parser.add_argument("--list", action="store_true", help="Xem danh sách tất cả sinh viên và tình trạng học phí")
    parser.add_argument("--reset", action="store_true", help="Reset tất cả các khoản học phí về chưa thanh toán (UNPAID)")
    parser.add_argument("--mssv", type=str, help="Mã số sinh viên (VD: 52100123)")
    parser.add_argument("--name", type=str, help="Họ và tên sinh viên (VD: 'Nguyễn Văn Minh')")
    parser.add_argument("--program", type=str, default="Công nghệ thông tin", help="Ngành học")
    parser.add_argument("--semester", type=str, default="HK1 2026-2027", help="Học kỳ")
    parser.add_argument("--amount", type=float, default=15000000.0, help="Số tiền học phí (VND)")

    args = parser.parse_args()

    if args.list:
        asyncio.run(list_students())
    elif args.reset:
        asyncio.run(reset_all_to_unpaid())
    elif args.mssv and args.name:
        asyncio.run(add_student(args.mssv, args.name, args.program, args.semester, args.amount))
    else:
        # Nếu chỉ gõ python scripts/manage_students.py thì hiện danh sách
        asyncio.run(list_students())
        print("\n💡 GỢI Ý LỆNH:")
        print("1. Xem danh sách:       python scripts/manage_students.py --list")
        print("2. Reset để test lại:   python scripts/manage_students.py --reset")
        print("3. Thêm sinh viên nợ:   python scripts/manage_students.py --mssv 52100123 --name \"Nguyễn Văn Minh\" --amount 15000000")

if __name__ == "__main__":
    main()
