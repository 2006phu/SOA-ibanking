# iBanking - Thanh Toán Học Phí (Microservices SOA)

## Yêu cầu
- Docker & Docker Compose

## Cách chạy

```bash
# 1. Clone repo
git clone https://github.com/2006phu/SOA-ibanking.git
cd SOA-ibanking

# 2. Tạo file .env (copy từ file mẫu)
cp .env.example .env

# 3. Khởi chạy toàn bộ hệ thống
docker compose up -d --build

# 4. Đợi ~30 giây cho các service khởi động xong, sau đó mở trình duyệt
```

## Truy cập
- **Web iBanking:** http://localhost:3000
- **API Gateway (Swagger):** http://localhost:8000/docs
- **RabbitMQ Management:** http://localhost:15672 (user: `ibanking` / pass: `rabbitmq_secret_2026`)

## Tài khoản đăng nhập

| Username | Password | Số dư |
|----------|----------|-------|
| lephu | 235780 | 80.000.000 VNĐ |
| nguyenvana | password123 | 50.000.000 VNĐ |
| levanc | password123 | 10.000.000 VNĐ |

## MSSV để tra cứu học phí

| MSSV | Sinh viên | Học phí chưa thanh toán |
|------|-----------|------------------------|
| 52100888 | Nguyễn Văn An | 12.500.000 VNĐ |
| 52100999 | Trần Thị Bình | 13.200.000 VNĐ |
| 52100777 | Lê Hoàng Cường | 10.800.000 VNĐ |

## Lệnh Demo & Test (Dành cho Giảng viên / Đánh giá điểm 10)

```bash
# 1. Test Concurrency tự động (Chống Race Condition & Double-spending)
python scripts/test_concurrency_scenarios.py

# 2. Xem danh sách hoặc reset trạng thái học phí để test lại
python scripts/manage_students.py --list
python scripts/manage_students.py --reset
```

## Kiến trúc
Hệ thống gồm 6 Microservices backend + API Gateway + React Frontend:
- **Auth Service (8001):** Cấp và xác thực JWT token.
- **User Service (8002):** Quản lý số dư, dùng `SELECT FOR UPDATE` chống Race Condition.
- **Tuition Service (8003):** Quản lý học phí sinh viên, dùng `SELECT FOR UPDATE` chống thanh toán trùng.
- **OTP Service (8005):** Sinh và kiểm tra mã OTP (hạn 5 phút, dùng 1 lần).
- **Payment Service (8004):** Điều phối giao dịch phân tán (Saga Orchestration) và Idempotency Key.
- **Notification Service (8006):** Lắng nghe RabbitMQ, gửi email thật qua SMTP.
- **API Gateway (8000):** Xác thực JWT, gắn X-Correlation-ID và reverse proxy.
- **Database-per-Service:** 5 database PostgreSQL độc lập cho từng service.
