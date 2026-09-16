# iBanking - Hệ Thống Thanh Toán Học Phí (Microservices)

Dự án mô phỏng hệ thống thanh toán học phí của iBanking áp dụng kiến trúc **Microservices (SOA)**.

## 🌟 Tính năng nổi bật (Theo Tiêu chí 10 điểm)
- Kiến trúc **7 Microservices** độc lập với **Database-per-service**.
- Sử dụng **API Gateway** làm điểm vào duy nhất, xử lý JWT Auth và Routing.
- Xử lý **Concurrency (Tính nhất quán dữ liệu)** bằng Pessimistic Locking (`SELECT FOR UPDATE`).
- Giao dịch phân tán (Distributed Transaction) với **Saga Pattern & Compensation**.
- Chống lặp giao dịch với **Idempotency Key**.
- Giao tiếp bất đồng bộ qua **RabbitMQ** (gửi email OTP và hóa đơn).
- **Structured Logging & Tracing** (Correlation ID) xuyên suốt các service.

## 🛠 Công nghệ sử dụng
- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0 (Async), Uvicorn.
- **Frontend:** React.js 18, React Router v6, Axios, Nginx.
- **Database:** PostgreSQL 16.
- **Message Broker:** RabbitMQ 3.13.
- **Infrastructure:** Docker & Docker Compose.

---

## 🚀 Hướng dẫn cài đặt và khởi chạy

### 1. Chuẩn bị môi trường
- Đảm bảo máy tính đã cài đặt **Docker** và **Docker Compose**.
- Cài đặt Python 3.11+ (nếu muốn chạy các script test/seed bên ngoài Docker).

### 2. Cấu hình
Mở file `.env` ở thư mục gốc và cập nhật thông tin email của bạn để hệ thống có thể gửi email OTP thật:
```env
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```
*(Lưu ý: Đối với Gmail, bạn cần bật 2FA và tạo App Password).*

### 3. Khởi chạy hệ thống
Mở terminal tại thư mục gốc của dự án và chạy lệnh:
```bash
docker compose up -d --build
```
Hệ thống sẽ tải image, build các service và khởi chạy. Quá trình này mất khoảng 2-3 phút cho lần đầu tiên.

Kiểm tra trạng thái các container:
```bash
docker compose ps
```
Chờ đến khi tất cả các service hiển thị trạng thái `healthy` hoặc `running`.

### 4. Khởi tạo dữ liệu mẫu (Seed Data)
Sau khi các service đã chạy ổn định, tạo dữ liệu mẫu bằng lệnh:
```bash
docker compose exec payment-service python /app/scripts/seed_data.py
```
Dữ liệu mẫu bao gồm:
- **Tài khoản đăng nhập:** 
  - `nguyenvana` / `password123` (Số dư: 50.000.000 VNĐ)
  - `levanc` / `password123` (Số dư: 10.000.000 VNĐ - dùng để test thanh toán không đủ tiền)
- **MSSV để tra cứu:** `52100001`, `52100002`, `52100005`, v.v.

### 5. Truy cập ứng dụng
- **Giao diện Web (Frontend):** [http://localhost:3000](http://localhost:3000)
- **API Gateway (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **RabbitMQ Management UI:** [http://localhost:15672](http://localhost:15672) (user/pass: `ibanking` / `rabbitmq_secret_2026`)

---

## 🧪 Hướng dẫn Demo cho Giảng viên

Để chứng minh hệ thống xử lý tốt Concurrency (Tiêu chí 6 - 1.5 điểm), bạn có thể chạy script demo tự động:

### Kịch bản 1: Race Condition trên cùng 1 tài khoản
*User A có 10 triệu, bấm thanh toán 2 khoản 6 triệu cùng 1 lúc (2 requests đồng thời).*
*Kỳ vọng: 1 giao dịch thành công, 1 giao dịch bị từ chối do không đủ số dư.*

Chạy lệnh:
```bash
docker compose exec payment-service python /app/scripts/demo_concurrency.py
```
Script sẽ tự động gọi API đồng thời và in ra kết quả chặn race condition.

---

## 📁 Cấu trúc thư mục

- `/gateway`: API Gateway service.
- `/services/auth-service`: Quản lý xác thực và JWT.
- `/services/user-service`: Quản lý thông tin và số dư người dùng.
- `/services/tuition-service`: Quản lý thông tin học phí sinh viên.
- `/services/otp-service`: Quản lý vòng đời mã OTP.
- `/services/payment-service`: Orchestrator điều phối quá trình thanh toán (Saga).
- `/services/notification-service`: RabbitMQ Worker gửi email.
- `/frontend`: React Web Application.
- `/scripts`: Các script tiện ích (seed, demo).
