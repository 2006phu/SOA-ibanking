"""
Script tự động xuất tất cả sơ đồ kiến trúc (Mermaid Diagrams) thành file ảnh PNG độ nét cao
Dùng để chèn trực tiếp vào Báo cáo Đồ án Word / Slide PowerPoint thuyết trình.
"""
import os
import httpx

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "diagrams")
os.makedirs(OUTPUT_DIR, exist_ok=True)

DIAGRAMS = {
    "1_architecture_diagram.png": """
graph TB
    subgraph "Frontend Layer"
        UI["React.js Web Application<br/>(Port 3000)"]
    end

    subgraph "Gateway Layer"
        GW["API Gateway Service (FastAPI - Port 8000)<br/>• Centralized Authentication & JWT Verification<br/>• Reverse Proxy & Request Routing<br/>• Correlation-ID Injection (Distributed Tracing)<br/>• Structured JSON Access Logging"]
    end

    subgraph "Microservices Layer"
        AUTH["Auth Service (Port 8001)<br/>JWT Issuance & Verification"]
        USER["User Service (Port 8002)<br/>Balance Management & History<br/>Pessimistic Lock (FOR UPDATE)"]
        TUITION["Tuition Service (Port 8003)<br/>Student & Tuition Inquiries<br/>Pessimistic Lock (FOR UPDATE)"]
        PAYMENT["Payment Service (Port 8004)<br/>Saga Pattern Orchestrator<br/>Idempotency Key Enforcement"]
        OTP["OTP Service (Port 8005)<br/>OTP Generation & Validation"]
        NOTIFY["Notification Service (Port 8006)<br/>Async Email Sender Worker"]
    end

    subgraph "Database per Service Pattern"
        DB_AUTH[("PostgreSQL<br/>auth_db")]
        DB_USER[("PostgreSQL<br/>user_db")]
        DB_TUITION[("PostgreSQL<br/>tuition_db")]
        DB_PAYMENT[("PostgreSQL<br/>payment_db")]
        DB_OTP[("PostgreSQL<br/>otp_db")]
    end

    subgraph "Message Broker Layer"
        MQ["RabbitMQ Message Broker<br/>Queues: 'otp_email', 'payment_success'"]
    end

    UI -->|"HTTP REST"| GW
    GW -->|"Proxy + X-Correlation-ID"| AUTH
    GW -->|"Proxy + X-Correlation-ID"| USER
    GW -->|"Proxy + X-Correlation-ID"| TUITION
    GW -->|"Proxy + X-Correlation-ID"| PAYMENT

    AUTH --> DB_AUTH
    USER --> DB_USER
    TUITION --> DB_TUITION
    PAYMENT --> DB_PAYMENT
    OTP --> DB_OTP

    PAYMENT -->|"Deduct / Refund"| USER
    PAYMENT -->|"Verify & Pay Fee"| TUITION
    PAYMENT -->|"Request OTP"| OTP

    PAYMENT -->|"Publish: payment_success"| MQ
    OTP -->|"Publish: otp_email"| MQ
    MQ -->|"Consume events"| NOTIFY
""",

    "2_usecase_diagram.png": """
graph LR
    subgraph "Hệ thống iBanking Thanh Toán Học Phí (SOA)"
        UC1["1. Đăng nhập hệ thống"]
        UC2["2. Xem thông tin & số dư khả dụng"]
        UC3["3. Tra cứu nợ học phí theo MSSV"]
        UC4["4. Khởi tạo & Xác nhận thanh toán"]
        UC5["5. Nhận & Xác thực mã OTP"]
        UC6["6. Xem lịch sử giao dịch thanh toán"]
    end

    subgraph "Dịch vụ ngoại vi"
        EMAIL_SYS(("Hệ thống Email TDTU<br/>(Gmail SMTP)"))
        MQ_SYS(("RabbitMQ Message Broker"))
    end

    USER(("Người dùng<br/>(Sinh viên / Phụ huynh)"))

    USER --> UC1
    USER --> UC2
    USER --> UC3
    USER --> UC4
    USER --> UC5
    USER --> UC6

    UC4 -.->|include| UC3
    UC4 -.->|include| UC5

    UC5 --> MQ_SYS
    MQ_SYS --> EMAIL_SYS
""",

    "3_database_erd_diagram.png": """
erDiagram
    USERS {
        uuid id PK
        varchar username UK
        varchar password_hash
        varchar full_name
        varchar phone
        varchar email UK
        decimal balance
        timestamp created_at
    }

    USER_PROFILES {
        uuid id PK
        varchar full_name
        varchar phone
        varchar email UK
        decimal balance
        timestamp created_at
    }

    STUDENTS {
        uuid id PK
        varchar mssv UK
        varchar full_name
        varchar program
        timestamp created_at
    }

    TUITION_FEES {
        uuid id PK
        varchar mssv FK
        varchar semester
        decimal amount
        varchar status
        uuid paid_by_user_id FK
        uuid paid_by_transaction_id FK
        timestamp paid_at
    }

    TRANSACTIONS {
        uuid id PK
        uuid user_id FK
        uuid tuition_fee_id FK
        varchar mssv
        varchar student_name
        decimal amount
        varchar status
        decimal user_balance_before
        decimal user_balance_after
        varchar idempotency_key UK
        timestamp created_at
        timestamp completed_at
    }

    OTP_CODES {
        uuid id PK
        uuid transaction_id FK
        varchar code
        varchar email
        boolean is_used
        timestamp expires_at
        timestamp created_at
    }

    USER_PROFILES ||--o{ TRANSACTIONS : "thuc_hien"
    STUDENTS ||--o{ TUITION_FEES : "co_khoan_phi"
    TRANSACTIONS ||--o| TUITION_FEES : "thanh_toan"
    TRANSACTIONS ||--o| OTP_CODES : "xac_thuc"
""",

    "4_sequence_diagram.png": """
sequenceDiagram
    autonumber
    participant C as Web Client (React)
    participant GW as API Gateway (8000)
    participant P as Payment Service (8004)
    participant U as User Service (8002)
    participant T as Tuition Service (8003)
    participant O as OTP Service (8005)
    participant MQ as RabbitMQ
    participant N as Notification Service (8006)

    Note over GW: Tự động gắn X-Correlation-ID
    C->>GW: 1. POST /payments/initiate (MSSV, tuition_fee_id)
    GW->>P: Forward request + correlation-id
    P->>T: GET /tuition/fee/{id} (Check UNPAID)
    T-->>P: Fee Info
    P->>U: GET /users/{id}/balance (Check Balance)
    U-->>P: Balance Info
    P->>P: Kiểm tra (Balance >= Amount)
    P-->>C: 201 Created (Transaction PENDING)

    C->>GW: 2. POST /payments/{id}/confirm
    GW->>P: Forward confirm
    P->>O: POST /otp/generate (transaction_id, email)
    O->>MQ: Publish event vào queue 'otp_email'
    MQ->>N: Consume event
    N->>N: Gửi OTP thật về Gmail sinh viên
    O-->>P: OTP generated
    P-->>C: 200 OK (Status: OTP_SENT)

    C->>GW: 3. POST /payments/{id}/verify-otp (Nhập OTP)
    GW->>P: Forward verify
    P->>O: POST /otp/verify (Check code, TTL, used flag)
    O-->>P: Valid = True

    rect rgb(240, 248, 255)
        Note over P,T: CRITICAL SECTION - SAGA ORCHESTRATION & LOCKING
        P->>U: PUT /balance/deduct (SELECT ... FOR UPDATE)
        U-->>P: Deducted Success
        P->>T: PUT /tuition/fee/pay (SELECT ... FOR UPDATE)
        alt Học phí chưa được ai trả
            T-->>P: Mark PAID Success
            P->>P: Update Transaction status = SUCCESS
            P->>MQ: Publish 'payment_success' event
            MQ->>N: Gửi Email biên lai thanh toán thành công
            P-->>C: 200 SUCCESS (Thanh toán hoàn tất)
        else Bị tranh chấp (người khác vừa thanh toán xong)
            T-->>P: 409 Conflict (Already Paid)
            Note over P,U: SAGA COMPENSATION (ROLLBACK HOÀN TIỀN)
            P->>U: PUT /balance/refund (Hoàn tiền lại cho User)
            U-->>P: Refunded Success
            P->>P: Update Transaction status = FAILED
            P-->>C: 409 Lỗi: Học phí đã được thanh toán, tiền đã hoàn lại
        end
    end
"""
}

def export_all():
    print(f"🚀 Đang xuất các sơ đồ ra thư mục: {OUTPUT_DIR}\n")
    with httpx.Client(timeout=60.0) as client:
        for filename, mermaid_code in DIAGRAMS.items():
            print(f"🖼️ Đang tạo sơ đồ: {filename}...", end="", flush=True)
            try:
                res = client.post(
                    "https://kroki.io/mermaid/png",
                    content=mermaid_code.strip(),
                    headers={"Content-Type": "text/plain; charset=utf-8"}
                )
                if res.status_code == 200:
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(res.content)
                    print(f"  --> ✅ ĐÃ XUẤT ({len(res.content):,} bytes)")
                else:
                    print(f"  --> ❌ Lỗi {res.status_code}: {res.text}")
            except Exception as e:
                print(f"  --> ❌ Lỗi: {e}")

    print(f"\n🎉 Hoàn thành! Toàn bộ file ảnh đã được lưu tại:\n👉 {OUTPUT_DIR}")

if __name__ == "__main__":
    export_all()
