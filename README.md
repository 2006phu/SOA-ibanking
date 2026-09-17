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

## Kiến trúc
7 Microservices: Auth, User, Tuition, OTP, Payment (Saga Orchestrator), Notification (RabbitMQ), API Gateway.

Mỗi service có database riêng (Database-per-Service pattern). Sử dụng Pessimistic Locking (`SELECT FOR UPDATE`) để chống Race Condition.
