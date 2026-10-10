---
marp: true
theme: default
paginate: true
---

# MIDTERM PRESENTATION
## Course: Service-Oriented Architecture (SOA)
**Project:** Online Tuition Payment System (iBanking) using Microservices Architecture

**Instructor:** [Instructor's Name]
**Student:** Lê Phú (Student ID: 524h0121)

---

# Team Members & Contribution Rates

| Student ID | Full Name | Academic Email | Assigned Responsibilities | Completion |
| --- | --- | --- | --- | --- |
| 524H0121 | Lê Phú | 524h0121@student.tdtu.edu.vn | Full Project (Analysis, Design, Microservices Implementation, React Frontend, Docker) | 100% |

---

# System Overview & Usecase (Frontend GUI)

- **React.js Interface:** Professional iBanking simulation.
- **Key Features:**
  - Login & JWT Authentication.
  - Tuition fee inquiry by Student ID.
  - Real-time account balance display.
  - Email OTP confirmation and Transaction History tracking.

![bg right:40% 90%](diagrams/so_do_usecase.jpg)

---

# Microservices Architecture & API Gateway

- **Service Decomposition:** 6 independent Microservices (Auth, User, Tuition, Payment, OTP, Notification).
- **Database-per-service:** 5 separate PostgreSQL databases, no cross-database foreign keys.
- **API Gateway:**
  - Single Entry Point.
  - JWT Authentication and Request Routing.
  - Request tracking using `X-Correlation-ID` header.

![bg right:45% 90%](diagrams/so_do_kien_truc.jpg)

---

# Core Operation Flow (Payment Workflow)

**Step-by-step execution of a tuition payment:**
1. **Initiation:** User selects a tuition fee. Frontend sends an initiation request to Payment Service.
2. **Validation:** Payment Service cross-checks tuition status (Tuition Service) and user balance (User Service).
3. **OTP Generation:** If valid, OTP Service generates a code and sends it via Email (asynchronously via RabbitMQ).
4. **Confirmation:** User enters the OTP.
5. **Execution:** Payment Service deducts the balance and updates the tuition status to `PAID`.
6. **Notification:** On success, an e-receipt is sent via Email.

---

# Distributed Transaction (Saga Pattern)

**Problem:** Ensuring data consistency across multiple DBs during the Execution phase.
- **Orchestration Mechanism:** Payment Service acts as the central orchestrator.
- **Rollback (Compensation):** 
  - If money deduction succeeds but tuition update fails (e.g., already paid by someone else), Payment Service calls User Service to process a **Refund**.
  - Ensures ACID properties in a distributed environment.

![bg right:40% 80%](diagrams/so_do_sequence.jpg)

---

# Concurrency Control (Pessimistic Locking)

**Problem:** 
1. *Double-spending:* A single user sends multiple payment requests simultaneously.
2. *Race Condition:* Multiple users attempting to pay the same tuition fee at the exact same time.

**Solution:** Applying **Pessimistic Locking** at the Database level.
- Using `SELECT ... FOR UPDATE` when reading balances and tuition statuses.
- Subsequent transactions must wait until the first transaction finishes and releases the lock.

```python
# Code Snippet in User Service (Row-level Locking)
result = await db.execute(
    select(UserProfile)
    .where(UserProfile.id == user_id)
    .with_for_update()
)
```

---

# Asynchronous Communication

**Performance Optimization with RabbitMQ:**
- Tasks not requiring immediate response (like Email) are pushed to the Message Queue.
- **Notification Service** acts as an independent Worker:
  - Listens to `otp_email` queue: Sends OTP codes (valid for 5 mins).
  - Listens to `payment_success` queue: Sends e-receipts via email.
- Integrated with `aiosmtplib` to send real emails via Gmail's SMTP server.

---

# Database Design (ERD)

- Logical Data Decentralization.
- **Payment Service** stores complete transaction records for auditing.
- **Idempotency Key:** Prevents duplicate requests from the Frontend, ensuring a transaction is only created once regardless of repeated clicks.

![bg right:50% 90%](diagrams/so_do_erd.jpg)

---

# Evaluation: Advantages & Limitations

**Advantages:**
- **Data Integrity:** Completely resolves concurrent payment issues and distributed consistency (Saga).
- **Scalability:** Easy to independently scale up high-load services (e.g., Payment).
- **Security:** Real email OTP flow and secure JWT.

**Limitations & Trade-offs:**
- **Network Latency:** Multiple internal API calls increase latency $\rightarrow$ *Could replace HTTP REST with gRPC in the future.*
- **Debugging Complexity:** Tracing errors across multiple services is difficult $\rightarrow$ *Implemented `X-Correlation-ID` for comprehensive logging and tracking.*

---

# Project Deliverables & Task Completion

| Requirement / Criteria | Description & Deliverables | Status / Completion |
| --- | --- | --- |
| **Req 1: Microservices** | Multi-service architecture + API Gateway (FastAPI) | 100% (Pass) |
| **Req 2: Database** | Independent DBs (PostgreSQL), no cross-service FKs | 100% (Pass) |
| **Req 3: Distributed Sys** | Implemented Saga Pattern (Orchestration) | 100% (Pass) |
| **Req 4: Concurrency** | Implemented Pessimistic Locking (FOR UPDATE) | 100% (Pass) |
| **Req 5: Async Comm** | Message Broker (RabbitMQ) & Real Email sending | 100% (Pass) |
| **Req 6: Frontend GUI** | Professional React UI, routed via Gateway | 100% (Pass) |
| **Req 7: Deployment** | Packaged and runs smoothly with Docker Compose | 100% (Pass) |

---

# Thank You for Your Attention

**Q&A Session**
*(Live Application Demo and Automated Concurrency Test Script execution)*
