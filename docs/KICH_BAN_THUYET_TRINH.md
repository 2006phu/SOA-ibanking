# KỊCH BẢN THUYẾT TRÌNH & DEMO BẢO VỆ ĐỒ ÁN GIỮA KỲ

**Môn học:** Kiến Trúc Hướng Dịch Vụ (504070) – HK1/2026-2027  
**Đề tài:** Hệ thống Thanh toán Học phí Trực tuyến (iBanking) theo Kiến trúc Microservices SOA  
**Nhóm:** `SOA.26-19` — **Lê Phú (524H0121)** & **Vũ Giang Huy (524H0095)**  
**Bộ slide sử dụng:** [`docs/Slide_SOA_v2.pptx`](Slide_SOA_v2.pptx) (15 slides, tiếng Anh)  
**Tổng thời lượng:** **15 phút** (10 phút trình bày + Live Demo, 5 phút Hỏi - Đáp)

---

## 0. CHECKLIST CHUẨN BỊ TRƯỚC GIỜ BÁO CÁO (LÀM TRƯỚC 15 PHÚT)

Theo [Hướng dẫn báo cáo giữa kỳ](SOA-HuongDanBaoCaoGiuaKy.docx): bật sẵn **webcam**, chia sẻ toàn màn hình, hạn chế đọc lý thuyết dài dòng, ưu tiên chứng minh bằng sản phẩm thực tế.

1. **Khởi chạy toàn bộ Docker Compose (10 containers):**
   ```powershell
   docker compose up -d --build
   python scripts/seed_data.py
   python scripts/manage_students.py --reset
   ```
2. **Kiểm tra trạng thái các container & chạy test nhanh:**
   ```powershell
   docker compose ps
   .\.venv\Scripts\python.exe -m pytest tests/test_otp_and_saga.py -v
   ```
3. **Mở sẵn 4 cửa sổ trình duyệt / ứng dụng (Alt+Tab chuyển nhanh):**
   - **Cửa sổ 1:** [`docs/Slide_SOA_v2.pptx`](Slide_SOA_v2.pptx) đang ở chế độ Slide Show (F5).
   - **Cửa sổ 2:** Frontend React app tại `http://localhost:3000` (đã sẵn sàng ở màn hình Login).
   - **Cửa sổ 3:** Hộp thư Gmail của tài khoản `lephu` (`524h0121@student.tdtu.edu.vn`) để cho giảng viên thấy OTP thật & Biên lai điện tử gửi về ngay trong lúc demo.
   - **Cửa sổ 4:** Tab Swagger `/docs` (`http://localhost:8004/docs` hoặc RabbitMQ Management `http://localhost:15672` user `ibanking`).
   - **Cửa sổ 5:** Terminal PowerShell đặt sẵn ở thư mục `d:\University\SOA\SOA-ibanking` và cửa sổ VS Code mở sẵn 3 file cốt lõi (`services/payment-service/app/service.py`, `services/user-service/app/service.py`, `services/tuition-service/app/service.py`) phòng khi thầy yêu cầu đọc code.

---

## PHẦN 1: TỔNG QUAN HỆ THỐNG (1 PHÚT — SLIDE 1–3)

> **Người trình bày:** Vũ Giang Huy (524H0095)

### Slide 1–2: Chào hỏi & Giới thiệu Nhóm (~15 giây)
> *"Em xin kính chào thầy Dương Hữu Phúc và các bạn. Em là Vũ Giang Huy, đại diện nhóm SOA.26-19 gồm bạn Lê Phú (524H0121) và em (524H0095), xin trình bày đồ án giữa kỳ: Hệ thống Thanh toán Học phí Trực tuyến iBanking theo kiến trúc Microservices."*

### Slide 3: System Overview & Use Case Diagram (~45 giây)
> *"Trên Slide 3 là tổng quan bài toán và Use Case Diagram của hệ thống. Giao diện React SPA cho phép Sinh viên hoặc Phụ huynh thực hiện khép kín 6 nghiệp vụ chính: (1) Đăng nhập xác thực JWT, (2) Xem số dư tài khoản theo thời gian thực, (3) Tra cứu công nợ học phí theo MSSV, (4) Khởi tạo thanh toán có Idempotency, (5) Nhận và xác thực mã OTP 6 chữ số gửi qua email thật, và (6) Xem lịch sử giao dịch kèm biên lai điện tử.*
>
> *Ở phía bên phải sơ đồ là 2 tác nhân hệ thống ngoại vi: **RabbitMQ Message Broker** và **Gmail SMTP**. Nhờ tách luồng gửi email ra bất đồng bộ, người dùng không bị chờ xử lý I/O mạng khi thanh toán."*

---

## PHẦN 2: PHÂN TÍCH & THIẾT KẾ HỆ THỐNG (2 PHÚT — SLIDE 4–7)

> **Người trình bày:** Vũ Giang Huy (Slide 4–6) → chuyển mic Lê Phú (Slide 7)

### Slide 4: Microservices Architecture & API Gateway (~35 giây)
> *"Về mặt kiến trúc tổng thể (Slide 4), mọi request từ React Client đều đi qua duy nhất một cổng **API Gateway** ở port 8000. API Gateway đảm nhiệm xác thực HS256 JWT, gán `X-User-ID`, và sinh/chuyển tiếp header `X-Correlation-ID` để truy vết toàn luồng.*
>
> *Bên dưới Gateway là **6 Microservices FastAPI** giao tiếp nội bộ qua HTTP REST và bất đồng bộ qua RabbitMQ. Nhóm chọn kiến trúc Microservices vì ba lý do: (1) dễ scale độc lập các dịch vụ chịu tải cao như Payment và OTP, (2) tách bạch ranh giới sở hữu dữ liệu, và (3) cô lập lỗi — chẳng hạn nếu dịch vụ Gmail SMTP chậm thì luồng trừ tiền và gạch nợ học phí vẫn phản hồi nhanh."*

### Slide 5: Service Decomposition & Data Ownership (~25 giây)
> *"Slide 5 tóm tắt trách nhiệm và quyền sở hữu dữ liệu của từng thành phần:*
> - **`auth-service` (`auth_db`):** Quản lý định danh, băm mật khẩu `bcrypt`, cấp phát JWT.*
> - **`user-service` (`user_db`):** Sở hữu số dư ví người nộp tiền và lịch sử ví.*
> - **`tuition-service` (`tuition_db`):** Quản lý hồ sơ sinh viên và công nợ học phí theo kỳ.*
> - **`payment-service` (`payment_db`):** Đóng vai trò **Saga Orchestrator** điều phối toàn giao dịch.*
> - **`otp-service` (`otp_db`):** Sinh, khóa dòng và xác thực OTP gắn 1–1 với giao dịch.*
> - **`notification-service` (Worker):** Không có DB, tiêu thụ message từ RabbitMQ để gửi email qua Gmail SMTP."*

### Slide 6: Database-per-Service Physical ERD (~30 giây)
> *"Slide 6 thể hiện Sơ đồ ERD phân tán chuẩn SOA — tách 5 PostgreSQL database hoàn toàn độc lập (`auth_db`, `user_db`, `tuition_db`, `payment_db`, `otp_db`).*
> - ***Đường nét liền*** *là khóa ngoại vật lý hợp lệ bên trong cùng một DB (như `transaction_histories.user_id` trong `user_db`, hay `tuition_fees.mssv` trong `tuition_db`).*
> - ***Đường nét đứt*** *giữa `payment_db` / `otp_db` với các service khác chỉ là tham chiếu logic qua UUID/MSSV, tuyệt đối không có Foreign Key hay JOIN xuyên database.*
> - *Về ràng buộc toàn vẹn: toàn bộ cột tiền tệ dùng `Numeric(15, 2)` để tránh sai số dấu phẩy động; có ràng buộc `UNIQUE` trên `username`, `email`, `mssv`, `idempotency_key`, `otp_codes.transaction_id`, và `CHECK (amount > 0)`."*

### Slide 7: REST API Design & Validation Contract (~30 giây)
> *(Lê Phú nhận lời)* *"Slide 7 là thiết kế bộ REST API qua Gateway `:8000` gồm đầy đủ các nhóm endpoint Auth, User Balance, Tuition Inquiry, và chuỗi 3 bước Payment: `POST /api/payments/initiate` (kèm header `Idempotency-Key` chống bấm đúp, trả `201 Created` hoặc `400`/`409`), `POST /api/payments/{id}/confirm` kích hoạt OTP, và `POST /api/payments/{id}/verify-otp` trả `200`, `401` (sai OTP), `409` (học phí đã thanh toán kèm hoàn tiền) hoặc `429` (nhập sai quá 5 lần). Dữ liệu vào được kiểm tra bằng Pydantic v2 (tự trả `422`), định dạng lỗi thống nhất `{"detail": "..."}` và có sẵn OpenAPI `/docs` trên từng service."*

---

## PHẦN 3: GIẢI PHÁP KỸ THUẬT TRỌNG TÂM (2 PHÚT — SLIDE 8–12)

> **Người trình bày:** Lê Phú (524H0121)

### Slide 8–9: Workflow 5 Giai đoạn & Bảo mật OTP (~35 giây)
> *"Slide 8 là sơ đồ Workflow toàn dự án từ đăng nhập đến hoàn tất thanh toán. Điểm nhấn ở Slide 9 là cơ chế bảo mật OTP được xây dựng chặt chẽ đúng yêu cầu tài chính:*
> - *Mã OTP 6 số được sinh bằng bộ sinh ngẫu nhiên mật mã học CSPRNG (`secrets.choice`), ràng buộc 1–1 với `transaction_id` (`UNIQUE`), thời hạn 5 phút và dùng đúng một lần (`is_used = True`).*
> - *Hệ thống dùng so sánh hằng thời gian (`secrets.compare_digest`), đếm số lần nhập sai `failed_attempts` và tự động khóa `HTTP 429 Too Many Requests` nếu sai quá 5 lần. Đặc biệt ở chế độ demo thật (`OTP_DEBUG_EXPOSE=false`), mã OTP không bao giờ bị lộ trong API response hay file log mà chỉ được gửi qua RabbitMQ tới Gmail của chủ tài khoản."*

### Slide 10: Distributed Transaction — Saga Orchestration (~35 giây)
> *"Ở Slide 10, vì dữ liệu tiền nằm ở `user_db` còn trạng thái công nợ nằm ở `tuition_db`, nếu dùng khóa phân tán Two-Phase Commit (2PC) sẽ gây treo tài nguyên xuyên database. Nhóm chọn **Saga Pattern theo mô hình Orchestration**, do `PaymentService` làm điều phối trung tâm: đảm bảo **ACID cục bộ** trong mỗi PostgreSQL DB và **Eventual Consistency** trên toàn hệ thống.*
>
> *Luồng thực thi qua máy trạng thái `PENDING -> OTP_SENT -> SUCCESS | FAILED | REFUNDED`. Nếu Bước A trừ tiền ở `user-service` thành công nhưng Bước B gạch nợ ở `tuition-service` thất bại (chẳng hạn trả `409 Conflict` vì tài khoản khác vừa đóng xong), `PaymentService` lập tức gọi giao dịch bù trừ **Refund** ở Bước C để hoàn lại tiền cho người dùng và cập nhật giao dịch sang `REFUNDED`."*

### Slide 11: Concurrency Control — Pessimistic Locking (~30 giây)
> *"Slide 11 giải quyết trực tiếp hai tình huống tương tranh của đề bài bằng **Pessimistic Locking (`SELECT ... FOR UPDATE`)**:*
> 1. ***Kịch bản 1 (Double-Spending trên cùng 1 tài khoản):*** *`user-service` khóa dòng `user_profiles` bằng `.with_for_update()`. Giao dịch đến trước trừ tiền; giao dịch đến sau phải chờ nhả khóa, đọc số dư mới, thấy không đủ tiền nên bị từ chối sạch với `400 Bad Request` (`FAILED`) — số dư không bao giờ âm.*
> 2. ***Kịch bản 2 (Nhiều tài khoản đóng cùng 1 khoản học phí):*** *`tuition-service` khóa dòng `tuition_fees` bằng `.with_for_update()`. Người đầu tiên đánh dấu `PAID` (`200 OK`); người thứ hai đọc thấy đã `PAID`, nhận `409 Conflict`, và Saga lập tức hoàn tiền về ví."*

### Slide 12: Async Messaging (RabbitMQ) & Tracing (~20 giây)
> *"Cuối phần giải pháp kỹ thuật (Slide 12), việc gửi email OTP và biên lai được đẩy sang RabbitMQ qua 2 hàng đợi `otp_email` và `payment_success`. `notification-service` dùng cơ chế Exponential Backoff retry 3 lần (`1s → 2s → 4s`) nếu SMTP lỗi tạm thời, và toàn bộ HTTP lẫn AMQP message đều mang theo `X-Correlation-ID` giúp nhóm truy vết log xuyên suốt 6 service."*

---

## PHẦN 4: KỊCH BẢN LIVE DEMO (5 PHÚT — SLIDE 13–14)

> **Người thực hiện:** Lê Phú thao tác chính; Vũ Giang Huy thuyết minh song song trên màn hình.

### Chuẩn bị Slide 13 (15 giây)
> *"Xin mời thầy theo dõi Slide 13 là kế hoạch kiểm thử tự động (`pytest` 8 test case + kịch bản E2E concurrency) và đóng gói Docker Compose. Em xin phép chuyển sang màn hình ứng dụng thực tế để demo 2 phần: (A) Luồng thanh toán iBanking kết hợp Email OTP thật, và (B) Kiểm thử tương tranh đồng thời."*

### Phần A: Demo UI Luồng Thanh toán & OTP Email Thật (~2 phút 45 giây)

| Bước | Thao tác trên màn hình | Lời thuyết minh ngắn gọn |
|---|---|---|
| **1. Đăng nhập** | Tại `http://localhost:3000`, nhập `lephu` / `235780` → nhấn **Đăng nhập**. | *"Em đăng nhập tài khoản `lephu`. Hệ thống gọi qua Gateway `:8000` xuống Auth Service xác thực và trả JWT."* |
| **2. Dashboard & Tra cứu** | Chỉ vào số dư **80,000,000 VND**. Nhập MSSV **`52100002`** (*Ngô Thị Mai Anh*) → nhấn **Tra cứu**. | *"Số dư thực tế đang là 80 triệu. Em tra cứu MSSV `52100002`, hệ thống chỉ hiển thị khoản nợ `UNPAID` kỳ HK2 2025-2026 là 14,500,000 VND."* |
| **3. Khởi tạo & Xác nhận** | Chọn khoản học phí `14,500,000 VND` → nhấn **Thanh toán** → nhấn **Xác nhận gửi OTP**. | *"Gateway tạo giao dịch `PENDING` kèm `Idempotency-Key`, sau đó chuyển `OTP_SENT` và đẩy sự kiện vào RabbitMQ để gửi email."* |
| **4. Nhận OTP Email thật** | Chuyển sang **tab Gmail** (`524h0121@student.tdtu.edu.vn`), mở email mới nhất có mã OTP 6 số, copy mã. | *"Đây là hộp thư thật nhận từ Gmail SMTP chỉ sau 1–2 giây. Mã OTP 6 số gắn với đúng mã giao dịch này và có hiệu lực 5 phút."* |
| **5. Nhập OTP & Kiểm tra kết quả** | Quay lại UI, nhập mã OTP → nhấn **Xác nhận thanh toán**. | *"Thanh toán thành công! Số dư tự động giảm từ 80 triệu còn 65.5 triệu. Tra cứu lại MSSV `52100002` thì khoản học phí vừa rồi đã chuyển `PAID` và không thể thanh toán lại."* |
| **6. Lịch sử & Biên lai** | Mở tab **Lịch sử giao dịch** và quay lại **tab Gmail** mở email biên lai `payment_success`. | *"Lịch sử giao dịch trên UI ghi nhận đầy đủ trạng thái `SUCCESS`, đồng thời Notification Worker đã gửi biên lai điện tử qua email."* |

*(Mẹo dự phòng nếu Gmail SMTP chậm do mạng Google Meet: có thể nhấn nút "Gửi lại / Tra nhanh `otp_codes` bằng câu lệnh psql dự phòng", giải thích thẳng cho thầy là chứng minh không rò OTP trên API!)*

### Phần B: Demo Tương tranh & Test Tự động (~2 phút)

1. **Chạy bộ Unit/Integration Test (`pytest`) — ~20 giây:**
   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/test_otp_and_saga.py -v
   ```
   > *"Trước khi chạy concurrency thật, em cho chạy bộ 8 test case `pytest` kiểm tra bảo mật OTP (ẩn OTP khỏi API, dùng 1 lần, hết hạn, khóa `429` sau 5 lần sai), `Idempotency-Key` và bù trừ Saga Refund — 8/8 PASSED."*

2. **Chạy kịch bản E2E Concurrency thật qua API Gateway — ~1 phút 20 giây:**
   ```powershell
   python scripts/test_concurrency_scenarios.py
   ```
   - **Chỉ lên màn hình Terminal kết quả Kịch bản 1:**
     > *"Ở Kịch bản 1: tài khoản `levanc` có 10 triệu VND, script bắn đồng thời 2 giao dịch mỗi khoản 6 triệu (tổng 12 triệu > 10 triệu). Kết quả: đúng 1 luồng thành công (`200 OK`), luồng còn lại bị `user-service` giữ khóa `FOR UPDATE` bắt phải chờ và trả `400 Insufficient balance`, số dư cuối còn đúng 4 triệu — tuyệt đối không âm."*
   - **Chỉ lên màn hình Terminal kết quả Kịch bản 2:**
     > *"Ở Kịch bản 2: cả 2 tài khoản `lephu` và `nguyenvana` cùng nhấn thanh toán đúng 1 khoản học phí 1 triệu VND tại cùng tích tắc qua `asyncio.gather`. Cả hai cùng qua bước trừ tiền ban đầu, nhưng tại `tuition-service`, chỉ 1 tài khoản khóa thành công để đánh dấu `PAID`; người đến sau nhận `409 Conflict` và được `PaymentService` kích hoạt Saga Refund hoàn nguyên tiền về tài khoản. Tất cả các assertion đều PASS."*

3. **Slide 14–15: Kết luận & Bảng đối chiếu Rubric (20 giây):**
   > *"Quay lại Slide 14 là bảng đối chiếu toàn bộ 8 tiêu chí Rubric 10/10 cùng hướng phát triển như Outbox Pattern và gRPC. Phần trình bày và demo của nhóm SOA.26-19 đến đây xin kết thúc, em xin mời thầy đặt câu hỏi kiểm tra ạ!"*

---

## PHẦN 5: CẨM NANG HỎI - ĐÁP (5 PHÚT Q&A — 18 CÂU HỎI TRỌNG TÂM)

| # | Câu hỏi Giảng viên hay hỏi | Trả lời ngắn gọn, trúng trọng tâm & File mở chứng minh |
|---|---|---|
| **1** | **Vì sao không dùng Monolith hay Shared Database cho nhanh mà phải tách 6 service và 5 PostgreSQL DB?** | Theo nguyên tắc Database-per-Service của SOA/Microservices: mỗi service sở hữu schema riêng (`scripts/init-databases.sql`), không ai được `JOIN` hay sửa chéo bảng của service khác, tránh tight coupling và cho phép scale riêng Payment/OTP. |
| **2** | **Tại sao `notification-service` không có database riêng?** | Notification Service đóng vai trò Stateless Worker chuyên tiêu thụ message từ RabbitMQ (`services/notification-service/app/consumer.py`) và gửi SMTP; mọi trạng thái giao dịch/OTP đã được lưu ở `payment_db` và `otp_db`. |
| **3** | **API Gateway làm những gì? Nếu client gọi thẳng port 8004 của Payment Service thì sao?** | Gateway (`gateway/app/middleware/auth.py` dòng 29, `correlation.py` dòng 14, `proxy.py` dòng 7) là Single Entry Point xác thực JWT, kiểm tra header `X-User-ID` và cấp `X-Correlation-ID`. Trong Docker network sản phẩm thật chỉ expose port Gateway `8000` (các port 8001–8006 có thể đóng ở production). |
| **4** | **Tại sao dùng Saga Orchestration mà không dùng Two-Phase Commit (2PC)?** | 2PC bắt mọi DB phải giữ lock phân tán trong suốt pha Prepare/Commit, giảm thông lượng nghiêm trọng và không phù hợp khi mỗi service độc lập (thậm chí khi có RabbitMQ). Saga chia thành các local ACID transactions tuần tự, khi lỗi thì chạy **Compensating Transaction** (hoàn tiền). |
| **5** | **Saga có đảm bảo 100% ACID như database đơn không?** | **Không.** Mỗi service chỉ có ACID cục bộ trên DB riêng của nó; trên phạm vi toàn hệ thống chỉ đạt **Eventual Consistency** (tính nhất quán cuối cùng) thông qua giao dịch bù trừ `refund`. (Nhóm đã sửa Slide 6/10 cũ để trả lời trung thực điểm này). |
| **6** | **Nếu ở Bước C (Saga Refund) gọi sang `user-service` lại bị rớt mạng hoặc timeout thì sao?** | Mở `services/payment-service/app/service.py` dòng 376–385: hệ thống log mức `CRITICAL` với đầy đủ `user_id` và `transaction_id`, đặt trạng thái `FAILED` (thay vì `REFUNDED`) để bộ phận vận hành/reconciliation đối soát. Hướng mở rộng chuẩn production là áp dụng **Transactional Outbox Pattern** để tự động retry bước hoàn tiền. |
| **7** | **Chỉ cho tôi chỗ nào trong code xử lý khóa tương tranh Kịch bản 1 (cùng tài khoản)?** | Mở `services/user-service/app/service.py` dòng **51**: `select(UserProfile).where(UserProfile.id == user_id).with_for_update()`. Giao dịch 2 buộc phải chờ giao dịch 1 `commit()` rồi mới đọc lại `user.balance` mới nhất trước khi kiểm tra `< data.amount`. |
| **8** | **Chỉ cho tôi chỗ nào xử lý tương tranh Kịch bản 2 (2 người cùng đóng 1 học phí)?** | Mở `services/tuition-service/app/service.py` dòng **115**: `select(TuitionFee).where(TuitionFee.id == tuition_id).with_for_update()`. Người đến sau thấy `fee.status == "PAID"` (dòng 126) nên trả `409 Conflict`, kích hoạt Saga hoàn tiền ở `payment-service/app/service.py` dòng 361–393. |
| **9** | **Tại sao chọn Pessimistic Locking (`FOR UPDATE`) thay vì Optimistic Locking (`version`)?** | Vì tranh chấp trên cùng 1 số dư ví hoặc cùng 1 khoản học phí khi xảy ra đụng độ sẽ khiến Optimistic phải hủy/retry liên tục ở tầng ứng dụng. Pessimistic Locking ở mức row DB (`FOR UPDATE`) đảm bảo tuần tự hóa an toàn tuyệt đối cho giao dịch tài chính chỉ với 1 câu truy vấn. |
| **10** | **Có nguy cơ Deadlock khi dùng `FOR UPDATE` không?** | Rất thấp vì `user-service` và `tuition-service` nằm trên 2 DB khác nhau, mỗi transaction chỉ lock **đúng 1 dòng đơn lẻ** (1 `user_id` hoặc 1 `tuition_fee_id`), không bao giờ lock chéo nhiều bảng theo thứ tự ngược nhau. Trong `payment-service` (dòng 165, 240) cũng khóa dòng `Transaction` trước khi gọi sang dịch vụ ngoài. |
| **11** | **Nếu bước trừ tiền (`deduct`) ở Kịch bản 1 lỗi `400 Insufficient balance`, Payment Service xử lý ra sao?** | Mở `services/payment-service/app/service.py` dòng **306–329**: vì chưa trừ được tiền nên **không** gọi refund, cập nhật thẳng `tx.status = "FAILED"`, giữ nguyên `user_balance_after = user_balance_before`, và trả nguyên mã `400` về client. |
| **12** | **Idempotency Key hoạt động thế nào khi người dùng bấm nút Thanh toán liên tiếp?** | Frontend gửi UUID trong header `Idempotency-Key`. Mở `services/payment-service/app/service.py` dòng **53–65** và `models.py` dòng **22** (`unique=True`): nếu trùng key cùng `user_id`, API trả lại chính transaction cũ thay vì tạo giao dịch trùng; nếu khác `user_id` trả `409 Conflict`. |
| **13** | **Mã OTP đảm bảo bảo mật và chống dò mã (Brute-force) như thế nào?** | Mở `services/otp-service/app/service.py`: (1) sinh mã bằng `secrets.choice` (CSPRNG, dòng 94–95), (2) mỗi `transaction_id` chỉ có 1 OTP duy nhất (`unique=True` trong `models.py:16`), (3) hết hạn sau 5 phút (dòng 188), (4) dùng 1 lần (`is_used=True`, dòng 218), (5) so sánh hằng thời gian `secrets.compare_digest` (dòng 204), (6) khóa `HTTP 429` sau 5 lần nhập sai (`failed_attempts >= 5`, dòng 196–201), và không trả OTP ra API (`OTP_DEBUG_EXPOSE=false`, dòng 152). |
| **14** | **Trong quá trình phát triển, nếu bạn bấm gửi lại OTP thì OTP cũ thế nào?** | Mở `services/otp-service/app/service.py` dòng **100–114**: `generate_otp` dùng `with_for_update()` khóa dòng `transaction_id`, xóa OTP cũ và cấp bản ghi mới với `failed_attempts = 0` và TTL 5 phút mới. |
| **15** | **Làm sao chống sai số thập phân khi cộng trừ tiền tệ?** | Toàn bộ cột tiền và số dư dùng `Decimal` trong Python và kiểu `Numeric(15, 2)` trong SQLAlchemy/PostgreSQL (`models.py`), cộng thêm `CheckConstraint("amount > 0")` trong `tuition-service/app/models.py:43`. |
| **16** | **RabbitMQ mất kết nối hoặc Gmail SMTP lỗi tạm thời thì email OTP có mất không?** | Mở `services/notification-service/app/consumer.py` dòng **162–206**: consumer xử lý với `max_retries = 3` theo Exponential Backoff (`1s, 2s, 4s`) trước khi reject, kết hợp queue bền vững trên RabbitMQ. |
| **17** | **Làm sao tìm log của đúng 1 giao dịch chạy qua 6 container?** | Tìm theo `X-Correlation-ID` do API Gateway gắn ở `gateway/app/middleware/correlation.py:14-21` — ID này tự động chuyển tiếp qua header HTTP (`payment-service/app/service.py:29-30`) và vào body message RabbitMQ (`consumer.py:142`). |
| **18** | **Kiểm tra trạng thái `http://localhost:8004/docs` hoặc Swagger ở đâu?** | Mỗi service đều bật FastAPI Swagger UI tại `/docs` (ví dụ `:8001/docs` Auth, `:8002/docs` User, `:8003/docs` Tuition, `:8004/docs` Payment, `:8005/docs` OTP) với đầy đủ Pydantic Request/Response schema. |
