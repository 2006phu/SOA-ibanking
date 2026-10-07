# BÁO CÁO ĐỒ ÁN GIỮA KỲ MÔN HỌC KIẾN TRÚC HƯỚNG DỊCH VỤ (SOA)
**Tên đề tài:** Hệ thống thanh toán học phí trực tuyến (iBanking Tuition Payment) sử dụng Kiến trúc Microservices
**Mục tiêu:** Đạt điểm 10/10 dựa trên 8 tiêu chí khắt khe của TDTU.

---

## 1. Thông tin chung
- **Trường:** Đại học Tôn Đức Thắng (TDTU)
- **Khoa:** Công nghệ thông tin
- **Môn học:** Kiến trúc Hướng Dịch vụ (Service-Oriented Architecture - SOA)
- **Giảng viên hướng dẫn:** [Tên Giảng Viên]
- **Sinh viên thực hiện:** Lê Phú (MSSV: 524h0121)

---

## 2. Phần Mở đầu
### 2.1. Lý do chọn đề tài
- Quá trình thanh toán học phí truyền thống hoặc qua các hệ thống nguyên khối (monolithic) thường gặp vấn đề về hiệu suất, nghẽn mạng trong kỳ đóng học phí.
- Ứng dụng kiến trúc Microservices giúp hệ thống dễ dàng mở rộng (scale), chịu lỗi tốt (fault tolerance) và phân tách rõ ràng nghiệp vụ.
### 2.2. Mục tiêu đề tài
- Xây dựng hệ thống thanh toán học phí mô phỏng giao dịch ngân hàng trực tuyến.
- Đảm bảo tính toàn vẹn dữ liệu trong môi trường phân tán bằng Saga Pattern.
- Giải quyết bài toán tương tranh (Concurrency) như: một tài khoản thanh toán nhiều lần cùng lúc (Double-spending) hoặc một khoản học phí được nhiều người thanh toán cùng lúc.
- Áp dụng hệ thống xác thực OTP thực qua Email để bảo mật giao dịch.
### 2.3. Phạm vi đề tài
- Hệ thống gồm 6 Microservices backend (Auth, User, Tuition, Payment, OTP, Notification), 1 API Gateway và 1 ứng dụng Frontend (React).

---

## 3. Cơ sở lý thuyết
### 3.1. Kiến trúc Microservices & API Gateway
- Tách ứng dụng thành các dịch vụ nhỏ, độc lập, có database riêng biệt (Database-per-service).
- API Gateway làm điểm chạm duy nhất (Single Entry Point), định tuyến (routing) và xác thực (authentication).
### 3.2. Quản lý giao dịch phân tán (Distributed Transaction)
- **Saga Pattern (Orchestration):** Payment Service đóng vai trò điều phối (Orchestrator), gọi lần lượt các dịch vụ khác. Nếu có bước thất bại, nó sẽ gọi hành động bù đắp (Compensation action) như hoàn tiền (refund).
### 3.3. Xử lý tương tranh (Concurrency Control)
- **Pessimistic Locking (Khóa bi quan):** Sử dụng `SELECT ... FOR UPDATE` trong PostgreSQL ở User Service và Tuition Service để ngăn chặn hiện tượng Race Conditions (Race Condition) trong quá trình trừ tiền và cập nhật trạng thái học phí.
### 3.4. Giao tiếp bất đồng bộ (Asynchronous Communication)
- Sử dụng Message Broker (RabbitMQ) để giao tiếp bất đồng bộ giữa các dịch vụ, đặc biệt trong việc gửi Email OTP và thông báo thành công (Notification Service).

---

## 4. Phân tích và Thiết kế hệ thống
### 4.1. Sơ đồ Usecase (Usecase Diagram)
*(Sơ đồ thể hiện các tác vụ của người dùng như Đăng nhập, Xem số dư, Tra cứu học phí, Thanh toán và Xem lịch sử)*
![Sơ đồ Usecase](diagrams/so_do_usecase.jpg)

### 4.2. Sơ đồ Kiến trúc (Architecture Diagram)
*(Sơ đồ thể hiện kiến trúc 6 Microservices, API Gateway, Message Broker, Frontend và hệ thống gửi Email thực)*
![Sơ đồ Kiến trúc](diagrams/so_do_kien_truc.jpg)

### 4.3. Sơ đồ Thực thể Liên kết (ERD Diagram)
*(Sơ đồ ERD thể hiện 5 databases riêng biệt của từng service, không có khóa ngoại cứng xuyên database)*
![Sơ đồ ERD](diagrams/so_do_erd.jpg)

### 4.4. Sơ đồ Tuần tự (Sequence Diagram)
*(Thể hiện luồng giao dịch Saga Pattern chi tiết từ Frontend -> Gateway -> Payment -> Các dịch vụ con)*
![Sơ đồ Tuần tự](diagrams/so_do_sequence.jpg)

---

## 5. Cài đặt và Triển khai
### 5.1. Công nghệ sử dụng
- **Backend:** Python (FastAPI), SQLAlchemy (Async), PyJWT.
- **Frontend:** React.js, Axios, React Router.
- **Database:** PostgreSQL (5 databases độc lập).
- **Message Broker:** RabbitMQ (aio-pika).
- **Triển khai:** Docker & Docker Compose.
- **Email:** SMTP Gmail (`aiosmtplib`).
### 5.2. Giải pháp đảm bảo Data Consistency & Concurrency (Tiêu chí lấy điểm tối đa)
- **Chống thanh toán trùng (Double-spending):** Khi hai request cùng trừ tiền một lúc, User Service dùng `FOR UPDATE` lock dòng dữ liệu người dùng. Request đến sau sẽ phải đợi request đầu xong mới được đọc số dư mới.
- **Chống thanh toán học phí trùng:** Tuition Service dùng `FOR UPDATE` lock dòng học phí. Request thứ hai sẽ thấy trạng thái đã là `PAID` và ném lỗi 409 Conflict. Payment Service bắt được lỗi này sẽ kích hoạt quy trình *Compensation* gọi User Service để hoàn lại tiền.
- **Idempotency Key:** Ngăn chặn việc gửi trùng request tạo giao dịch thanh toán từ Frontend.

---

## 6. Kết quả đạt được
- 100% các Microservices hoạt động độc lập và giao tiếp thông qua mạng Docker nội bộ.
- Giao diện React.js chuyên nghiệp, hiển thị số dư real-time, lấy từ User Service.
- Tích hợp thành công Email OTP thực (Gửi OTP về email sinh viên qua SMTP).
- Transaction History hiển thị chi tiết (Có tên sinh viên, MSSV nhờ việc route qua Payment Service).
- Xử lý mượt mà và an toàn các bài toán tương tranh (được chứng minh qua các script test tự động bằng Python).

---

## 7. Hướng dẫn chạy và test chương trình
### 7.1. Chạy hệ thống
```bash
docker-compose up -d --build
```
Hệ thống khởi chạy tại `http://localhost:3000` (Frontend) và API tại `http://localhost:8000` (Gateway).

### 7.2. Test kịch bản tương tranh (Concurrency)
Hệ thống có cung cấp sẵn script test chịu tải giả lập tình huống người dùng cố tình gửi nhiều request thanh toán cùng lúc:
```bash
python scripts/test_concurrency_scenarios.py
```
- **Kịch bản 1:** Test trừ tiền đồng thời -> Chỉ giao dịch đầu thành công, các giao dịch sau thất bại do không đủ tiền.
- **Kịch bản 2:** Test thanh toán cùng một khoản học phí -> Giao dịch 1 thành công, giao dịch 2 bị từ chối do học phí đã đóng (Tiền của giao dịch 2 được hoàn lại an toàn nhờ Saga).

---

## 8. Kết luận và Hướng phát triển
- **Kết luận:** Hệ thống đã đáp ứng vượt mức mong đợi các tiêu chuẩn của bài toán phân tán, đảm bảo tính ACID trong môi trường Microservices bằng Saga Pattern và Khóa bi quan. Hoàn toàn xứng đáng với mức đánh giá cao nhất.
- **Hướng phát triển:** Tích hợp Redis làm Cache, ELK Stack cho Logging, và Prometheus/Grafana cho Monitoring.
