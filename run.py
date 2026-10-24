#!/usr/bin/env python3
"""
iBanking TDTU — Universal 1-Click System Launcher (Cross-Platform)
Works on Windows, macOS, and Linux without any third-party dependencies.
"""
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

def print_banner():
    print("=" * 76)
    print("       🏛️  iBANKING TDTU - HỆ THỐNG THANH TOÁN HỌC PHÍ MICROSERVICES")
    print("=" * 76 + "\n")

def check_env():
    print("[1/5] Kiểm tra cấu hình môi trường (.env)...")
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("    -- Đã tự động tạo file .env từ .env.example!")
        else:
            print("    ⚠️ Cảnh báo: Không tìm thấy .env.example!")
    else:
        print("    -- File .env đã sẵn sàng.")
    print()

def check_docker():
    print("[2/5] Kiểm tra Docker Daemon...")
    try:
        res = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0:
            raise RuntimeError()
        print("    -- Docker đang hoạt động tốt.\n")
    except Exception:
        print("\n❌ [LỖI] Docker chưa được khởi động hoặc chưa cài đặt!")
        print("   Vui lòng mở ứng dụng Docker Desktop rồi chạy lại lệnh này.\n")
        input("Nhấn Enter để thoát...")
        sys.exit(1)

def start_docker():
    print("[3/5] Đang build và khởi động tất cả Microservices, Gateway, DB và RabbitMQ...")
    print("    (Quá trình này có thể mất 1-2 phút trong lần chạy đầu tiên)\n")
    
    cmd = ["docker", "compose", "up", "--build", "-d"]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        # Fallback to docker-compose
        try:
            subprocess.run(["docker-compose", "up", "--build", "-d"], check=True)
        except Exception as e:
            print(f"\n❌ [LỖI] Không thể khởi động Docker Compose: {e}")
            input("Nhấn Enter để thoát...")
            sys.exit(1)
    print()

def wait_for_gateway():
    print("[4/5] Chờ hệ thống khởi động hoàn tất (Health Check)...")
    url = "http://localhost:8000/health"
    max_retries = 30
    for i in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    print("\n    -- API Gateway và các Microservices đã sẵn sàng!")
                    return
        except Exception:
            pass
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(2)
    print("\n    -- Đã hết thời gian chờ, tiếp tục nạp dữ liệu...")

def seed_data():
    print("\n[5/5] Tự động nạp dữ liệu mẫu sinh viên và học phí (Seed Data)...")
    try:
        # Copy seed_data.py to container
        subprocess.run(
            ["docker", "compose", "cp", "scripts/seed_data.py", "payment-service:/app/seed_data.py"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        # Execute inside container
        subprocess.run(
            ["docker", "compose", "exec", "-T", "-e", "GATEWAY_URL=http://gateway:8000/api", "payment-service", "python", "/app/seed_data.py"],
            check=True
        )
        print("    -- Dữ liệu mẫu đã được nạp thành công!\n")
    except Exception as e:
        print(f"    ⚠️ Gặp sự cố khi nạp dữ liệu tự động: {e}. Bạn có thể chạy thủ công 'python scripts/seed_data.py'.\n")

def open_browser():
    print("=" * 76)
    print("🎉 HỆ THỐNG ĐÃ SẴN SÀNG! ĐANG MỞ TRÌNH DUYỆT...")
    print("=" * 76)
    print(" 🌐 Giao diện Web:      http://localhost:3000")
    print(" 📖 Swagger API Docs:   http://localhost:8000/docs")
    print(" 🐰 RabbitMQ Panel:     http://localhost:15672 (ibanking / rabbitmq_secret_2026)")
    print()
    print(" ⚡ Tài khoản dùng thử (Đã có sẵn nút bấm tự điền trên giao diện):")
    print("    1. student1  / password123 (Số dư: 15.000.000 ₫)")
    print("    2. parent1   / password123 (Số dư: 25.000.000 ₫)")
    print("    3. rich_user / password123 (Số dư: 100.000.000 ₫)")
    print("=" * 76 + "\n")
    
    try:
        webbrowser.open("http://localhost:3000")
        webbrowser.open("http://localhost:8000/docs")
    except Exception:
        pass

if __name__ == "__main__":
    print_banner()
    check_env()
    check_docker()
    start_docker()
    wait_for_gateway()
    seed_data()
    open_browser()
    print("Để dừng hệ thống khi không dùng nữa, chạy lệnh: docker compose down\n")
