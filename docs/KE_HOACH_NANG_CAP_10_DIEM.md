# BÁO CÁO RÀ SOÁT CHẤT LƯỢNG & KẾ HOẠCH NÂNG CẤP ĐẠT ĐIỂM 10/10

**Tài liệu đối chiếu:**
- Phiếu chấm điểm giữa kỳ: [`docs/rubric-midterm.pdf`](rubric-midterm.pdf) (8 Tiêu chí + Thang 10.0)
- Hướng dẫn báo cáo giữa kỳ: [`docs/SOA-HuongDanBaoCaoGiuaKy.docx`](SOA-HuongDanBaoCaoGiuaKy.docx)
- Bộ slide báo cáo nâng cấp: [`docs/Slide_SOA_v2.pptx`](Slide_SOA_v2.pptx) & Kịch bản [`docs/KICH_BAN_THUYET_TRINH.md`](KICH_BAN_THUYET_TRINH.md)

---

## 1. BẢNG ĐỐI CHIẾU RUBRIC 10.0 / 10.0 SAU KHI NÂNG CẤP

| Tiêu chí Rubric | Trọng số | Bằng chứng hiện có trong dự án (Code, Docs, Slide, Demo) | Trạng thái |
|---|---:|---|---|
| **1. Phân tích nghiệp vụ & UML** | **1.0** | Use Case Diagram chuyên nghiệp ([`hinh_3_1_use_case.png`](images/hinh_3_1_use_case.png)), ERD khái niệm + **ERD Vật lý phân tán Database-per-Service** ([`hinh_3_3b_soa_erd.png`](images/hinh_3_3b_soa_erd.png)), Workflow toàn dự án bằng `/archify` ([`hinh_3_4_workflow_archify.png`](images/hinh_3_4_workflow_archify.png)). | ✅ **1.0 / 1.0** |
| **2. Kiến trúc Microservices** | **1.5** | API Gateway (`:8000`) + 6 Microservices độc lập (`auth`, `user`, `tuition`, `payment`, `otp`, `notification`) + 5 DB PostgreSQL tách biệt + RabbitMQ & Gmail SMTP; có giải thích Service Ownership & Architecture Trade-offs tại Slide 4–5, 14. | ✅ **1.5 / 1.5** |
| **3. Thiết kế REST API** | **1.0** | Đầy đủ endpoint Auth, User, Tuition, Payment (`initiate`/`confirm`/`verify-otp`), Pydantic v2 schema trả `422`, unified JSON `{"detail": "..."}`, chuẩn hóa HTTP status `200`/`201`/`400`/`401`/`403`/`404`/`409`/`429`, có Swagger `/docs` trên từng service và bảng tổng hợp ở Slide 7. | ✅ **1.0 / 1.0** |
| **4. Database & Data Persistence** | **1.0** | 5 DB khởi tạo tự động qua [`scripts/init-databases.sql`](../scripts/init-databases.sql), kiểu tiền tệ `Numeric(15,2)`, ràng buộc `UNIQUE` (`username`, `email`, `mssv`, `idempotency_key`, `otp_codes.transaction_id`), `CheckConstraint("amount > 0")`, dữ liệu mẫu phong phú trong [`scripts/seed_data.py`](../scripts/seed_data.py). | ✅ **1.0 / 1.0** |
| **5. Hiện thực chức năng & Payment Workflow** | **2.0** | Luồng khép kín: Login JWT → xem số dư → tra cứu MSSV → Initiate (`Idempotency-Key`) → Confirm sinh OTP CSPRNG 6 số (`secrets.choice`, 5m TTL, dùng 1 lần, giới hạn 5 lần sai → `429`, gửi qua RabbitMQ → Gmail SMTP thật) → trừ tiền + gạch nợ `PAID` + lưu lịch sử + gửi biên lai. | ✅ **2.0 / 2.0** |
| **6. Transaction & Concurrency** | **1.5** | Saga Orchestration trong `PaymentService` (`PENDING -> OTP_SENT -> SUCCESS | FAILED | REFUNDED`) kèm bù trừ Refund khi `tuition-service` trả `409`; khóa bi quan `SELECT ... FOR UPDATE` trên `user_profiles`, `tuition_fees`, `transactions`, `otp_codes`; kiểm chứng cả 2 kịch bản tương tranh trong [`scripts/test_concurrency_scenarios.py`](../scripts/test_concurrency_scenarios.py). | ✅ **1.5 / 1.5** |
| **7. User Interface & Integration** | **0.5** | React 18 + Tailwind CSS SPA tích hợp đầy đủ qua API Gateway `:8000` hỗ trợ toàn bộ luồng từ Login → Dashboard → Tra cứu → Thanh toán → Nhập OTP Email → Lịch sử & Biên lai. | ✅ **0.5 / 0.5** |
| **8. Documentation, Deployment & Demonstration** | **1.5** | [`README.md`](../README.md) đầy đủ hướng dẫn + 1-click [`run.py`](../run.py)/[`start.bat`](../start.bat); Docker Compose 10 containers có `healthcheck` & `depends_on: service_healthy`; bộ slide 15 trang & kịch bản Demo 5 phút. | ✅ **1.5 / 1.5** |
| **Giải pháp Nâng cao (Mức 10.0)** | **Bonus / Đạt chuẩn 10** | Có bộ **Unit/Integration Test tự động (`pytest` 8/8 PASS)** tại [`tests/test_otp_and_saga.py`](../tests/test_otp_and_saga.py), **E2E Concurrency Assertions**, **`Idempotency-Key`**, **API Gateway**, **`X-Correlation-ID` Tracing** xuyên HTTP & RabbitMQ. | ✅ **Đạt mức 10.0** |

---

## 2. CÁC LỖI & ĐIỂM YẾU ĐÃ PHÁT HIỆN VÀ ĐÃ XỬ LÝ XONG (P0 & P1)

Trong quá trình rà soát sâu trước bảo vệ, đã phát hiện và sửa triệt để **5 vấn đề nghiêm trọng** sau:

### ✅ [P0 - Bug chí mạng] `UnboundLocalError: refund_success` trong `PaymentService`
- **Vị trí cũ:** [`services/payment-service/app/service.py`](../services/payment-service/app/service.py#L306-L329) (Step a: trừ số dư ở `user-service`).
- **Nguyên nhân:** Khi 2 giao dịch cùng tài khoản chạy song song (**Kịch bản Concurrency 1**), giao dịch thứ 2 bị `user-service` trả `400 Insufficient balance`. Khối `except httpx.HTTPStatusError` và `except httpx.RequestError` lại tham chiếu biến `refund_success` vốn chỉ được gán ở Bước c phía dưới → làm ứng dụng văng `UnboundLocalError` (HTTP `500 Internal Server Error`) và treo giao dịch ở trạng thái `OTP_SENT`.
- **Đã sửa:** Vì Bước a chưa trừ tiền nên không cần bù trừ, đặt trực tiếp `tx.status = "FAILED"`, giữ nguyên `tx.user_balance_after = tx.user_balance_before`, commit và ném lại đúng `HTTPException(400 / 503)`. Đã xác minh qua unit test `test_payment_step_a_insufficient_balance_marks_failed_no_unbound_error`.

### ✅ [P0 - Bảo mật OTP] Rò rỉ OTP qua API & Log, PRNG yếu, thiếu chống Brute-force
- **Vị trí đã sửa:** [`services/otp-service/app/models.py`](../services/otp-service/app/models.py), [`config.py`](../services/otp-service/app/config.py), [`database.py`](../services/otp-service/app/database.py), [`service.py`](../services/otp-service/app/service.py), [`services/payment-service/app/service.py`](../services/payment-service/app/service.py#L229), [`docker-compose.yml`](../docker-compose.yml), [`.env.example`](../.env.example).
- **Đã nâng cấp 5 điểm chuẩn tài chính:**
  1. Thay `random.choices` bằng CSPRNG **`secrets.choice("0123456789")`**.
  2. Thêm cờ cấu hình **`OTP_DEBUG_EXPOSE: bool = False`** (mặc định `False` để không bao giờ lộ `otp_code` trong JSON response khi demo/production).
  3. Xóa mã OTP dạng plaintext khỏi dòng log ở cả `otp-service` và `payment-service`.
  4. Dùng **`secrets.compare_digest`** để so sánh OTP ở hằng thời gian.
  5. Thêm cột `failed_attempts` (kèm tự động `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` trong `init_db()` để tương thích DB cũ) và ngưỡng `OTP_MAX_ATTEMPTS = 5` → tự động khóa bằng **`HTTP 429 Too Many Requests`** nếu nhập sai quá 5 lần.

### ✅ [P1 - Testing] Bổ sung Bộ Test Tự động & E2E Concurrency Assertions
- **Unit & Integration Test tự động ([`tests/test_otp_and_saga.py`](../tests/test_otp_and_saga.py)):** Viết 8 test case bằng `pytest` + `pytest-asyncio` + `sqlite+aiosqlite` (chạy độc lập không cần Docker), kiểm chứng: ẩn OTP mặc định, verify 1 lần (`is_used`), hết hạn (`400`), khóa `429` sau 5 lần sai, `Idempotency-Key` (`201` trùng trả cũ / khác user trả `409`), Saga Happy Path (`SUCCESS`), lỗi Step a (`FAILED` không `500`), và xung đột Step b `409` → tự động Saga Refund (`REFUNDED`). **Kết quả chạy: `8 passed in 1.40s`.**
- **E2E Concurrency Script ([`scripts/test_concurrency_scenarios.py`](../scripts/test_concurrency_scenarios.py)):** Viết lại hoàn chỉnh để tự động sinh MSSV test mới qua `tuition-service` (chạy lặp lại vô hạn không cần reset thủ công), đọc OTP từ `otp_db` khi `OTP_DEBUG_EXPOSE=false`, và **kiểm tra assertion thực tế** (đúng `1/2` thành công, số dư không âm, đúng `400` / `409` và exit code `1` nếu có lỗi).

### ✅ [P1 - Slide & Kịch bản] Nâng cấp `presentation_backup.pptx` (11 slides) → [`Slide_SOA_v2.pptx`](Slide_SOA_v2.pptx) (15 slides)
- Khắc phục triệt để 7 lỗi của slide cũ: xóa chữ `"Preview unavailable"` (Slide 3), thay thế bằng các sơ đồ mới nhất ([`hinh_3_1_use_case.png`](images/hinh_3_1_use_case.png), [`hinh_3_3b_soa_erd.png`](images/hinh_3_3b_soa_erd.png), [`hinh_3_4_workflow_archify.png`](images/hinh_3_4_workflow_archify.png)), sửa sai sót học thuật *"100% ACID across Microservices"* thành *Local ACID + Eventual Consistency*, sửa sai tên file `gui.py` ở Slide code thành `services/user-service/app/service.py & services/tuition-service/app/service.py`.
- Bổ sung 4 slide mới trọng tâm chấm điểm: **Service Ownership**, **REST API Design**, **OTP Security**, **Testing / Deployment / Live Demo Plan**, **Rubric 10/10 Coverage**.
- Đã xuất PNG cả 15 slide và kiểm tra bằng mắt không bị tràn chữ hay đè hình.

---

## 3. KẾ HOẠCH CẢI TIẾN MỞ RỘNG (P2 — OPTIONAL / HƯỚNG PHÁT TRIỂN)

Những hạng mục dưới đây **không cản trở demo hay điểm 10 giữa kỳ**, nhưng nhóm cần nắm rõ để trả lời khi Giảng viên hỏi về hướng đưa hệ thống lên Production (cũng là nội dung ở Slide 14):

| # | Hạng mục P2 | Hiện trạng trong code | Giải pháp nâng cấp khi lên Production |
|---|---|---|---|
| **1** | **Transactional Outbox Pattern** | [`payment-service/app/service.py`](../services/payment-service/app/service.py#L361-L447) gọi HTTP `refund` và publish RabbitMQ trực tiếp sau `commit()`. Nếu mạng rớt đúng tích tắc đó, chỉ log `CRITICAL`/`ERROR`. | Thêm bảng `outbox_events` trong `payment_db` (commit cùng transaction với `tx.status`), chạy Outbox Relay Worker gửi RabbitMQ hoặc thực thi Refund theo cơ chế **At-Least-Once + Idempotent Consumer**. |
| **2** | **Siết CORS & Quản lý Secrets** | [`gateway/app/main.py`](../gateway/app/main.py#L33-L40) dùng `allow_origin_regex=r"^https?://.*"`; các service con để `allow_origins=["*"]`; `config.py` có default `JWT_SECRET_KEY`. | Đọc danh sách domain cho phép qua biến `ALLOWED_ORIGINS` (ví dụ `http://localhost:3000`); bỏ giá trị secret mặc định trong `config.py`, bắt buộc inject từ Vault / Docker Secrets. |
| **3** | **Rate Limiting tại API Gateway** | Gateway có `AuthMiddleware`, `CorrelationIdMiddleware`, `LoggingMiddleware` nhưng chưa giới hạn số request/IP. | Bổ sung Redis + Sliding Window Rate Limiter ở [`gateway/app/middleware/`](../gateway/app/middleware/) (ví dụ giới hạn `/api/auth/login` và `/api/payments/*/verify-otp`). |
| **4** | **Internal Port Isolation & OpenTelemetry** | `docker-compose.yml` mở cả port `8001–8006` ra host để thuận tiện debug Swagger `/docs`. | Trên Production chỉ expose port `8000` (Gateway) và `3000` (Frontend); tích hợp OpenTelemetry SDK xuất trace sang Jaeger dựa trên `X-Correlation-ID`. |
| **5** | **UI Feedback cho `429` & Đếm ngược OTP** | Frontend hỗ trợ nhập OTP và gửi lại; khi bị khóa `429` cần nhắc người dùng nhấn *Gửi lại OTP*. | Có thể thêm bộ đếm ngược 5 phút trực tiếp trên Modal OTP và hiển thị nút "Gửi lại OTP mới" nổi bật khi API trả `429`. |

---

## 4. HƯỚNG DẪN CHẠY KIỂM THỬ TRƯỚC KHI BẢO VỆ

### A. Chạy bộ Unit/Integration Test (không cần Docker)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_otp_and_saga.py -v
```
*Kỳ vọng:* `8 passed` trong ~1.5 giây.

### B. Khởi chạy Full Stack Docker & Kiểm thử Tương tranh E2E
```powershell
# 1. Dựng toàn bộ 10 containers (build lại otp-service & payment-service với các bản vá mới)
docker compose up -d --build

# 2. Nạp dữ liệu mẫu & reset học phí về UNPAID
python scripts/seed_data.py
python scripts/manage_students.py --reset

# 3. Chạy kiểm thử E2E cả 2 kịch bản tương tranh
python scripts/test_concurrency_scenarios.py
```
*Kỳ vọng:* Cả Kịch bản 1 (`1/2` thành công, `400`, số dư không âm) và Kịch bản 2 (`1/2` thành công, `409` + Saga Refund, tổng tiền trừ bằng 1 lần học phí) đều in `PASS` và kết thúc với mã thoát `0`.
