# iBanking - Thanh Toán Học Phí (Microservices SOA)

## 🚀 Khởi Chạy Nhanh (1-Click Run)

Sau khi clone repo về máy, bạn chỉ cần **1 CLICK (hoặc 1 lệnh)** để tự động kiểm tra Docker, tạo `.env`, khởi động tất cả Microservices, nạp dữ liệu mẫu và tự động bật trình duyệt:

### 🪟 Dành cho Windows:
> **Click đúp chuột (Double click) vào file:** `start.bat`

### 🍎 Dành cho macOS:
> **Click đúp chuột (Double click) vào file:** `start.command`  
> *(hoặc mở Terminal gõ: `./start.sh`)*

### 🐍 Hoặc chạy đa nền tảng bằng Python (Windows / Mac / Linux):
```bash
python run.py
```

---

## 🛠️ Khởi chạy thủ công bằng Docker Compose

```bash
# 1. Clone repo
git clone https://github.com/2006phu/SOA-ibanking.git
cd SOA-ibanking

# 2. Tạo file .env (copy từ file mẫu)
cp .env.example .env

# 3. Khởi chạy toàn bộ hệ thống
docker compose up -d --build

# 4. Nạp dữ liệu mẫu
python scripts/seed_data.py
```

## 🌐 Địa chỉ truy cập
- **Giao diện Web iBanking:** [http://localhost:3000](http://localhost:3000)
- **API Gateway (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **RabbitMQ Management:** [http://localhost:15672](http://localhost:15672) *(user: `ibanking` / pass: `rabbitmq_secret_2026`)*

## ⚡ Tài khoản đăng nhập mẫu
*(Trên giao diện Web đã có sẵn các nút bấm tự động điền nhanh tài khoản demo)*

| Username | Password | Số dư | Vai trò |
|---|---|---|---|
| `student1` | `password123` | 15.000.000 ₫ | Sinh viên |
| `parent1` | `password123` | 25.000.000 ₫ | Phụ huynh |
| `rich_user` | `password123` | 100.000.000 ₫ | Tài khoản VIP |
| `lephu` | `235780` | 80.000.000 ₫ | Quản trị / Sinh viên |

## 🎓 Mã số sinh viên (MSSV) tra cứu học phí
- `52100888`: Nguyễn Văn An — Học kỳ 1 (12.500.000 ₫)
- `52100999`: Trần Thị Bích — Học kỳ 2 (13.200.000 ₫)
- `52100777`: Lê Hoàng Nam — Học kỳ 1 (10.800.000 ₫)

## 🧪 Kịch bản kiểm thử Tương tranh (Concurrency Test)

```bash
# Chạy script giả lập người dùng bấm thanh toán cùng lúc (chứng minh Saga + Pessimistic Locking)
python scripts/test_concurrency_scenarios.py

# Xem danh sách hoặc reset trạng thái học phí để test lại
python scripts/manage_students.py --list
python scripts/manage_students.py --reset
```

## 🏗️ Kiến trúc hệ thống
Hệ thống gồm 6 Microservices backend độc lập + 1 API Gateway + React Frontend:
- **API Gateway (8000):** Điểm tiếp nhận duy nhất, xác thực JWT, định tuyến request và gắn mã vết `X-Correlation-ID`.
- **Auth Service (8001):** Cấp và xác thực JWT token.
- **User Service (8002):** Quản lý hồ sơ và số dư, dùng `SELECT FOR UPDATE` chống lỗi Race Condition / Double-spending.
- **Tuition Service (8003):** Quản lý công nợ học phí sinh viên, dùng `SELECT FOR UPDATE` ngăn thanh toán trùng.
- **Payment Service (8004):** Điều phối giao dịch phân tán (Saga Orchestration), xử lý Idempotency Key và kích hoạt Refund khi có sự cố.
- **OTP Service (8005):** Sinh và xác minh mã OTP (hiệu lực 5 phút, dùng 1 lần).
- **Notification Service (8006):** Lắng nghe RabbitMQ (`otp_email`, `payment_success`) và gửi email thông báo qua Gmail SMTP.
