# TODO List - سیستم ایزوله درخواست/پاسخ

> آخرین به‌روزرسانی: 2025-10-25  
> وضعیت: در حال بازطراحی معماری

---

## 📋 فهرست کارها به تفکیک فاز

### فاز 1: زیرساخت پایه ✅
- [x] راه‌اندازی محیط توسعه
  - [x] نصب Docker و Docker Compose
  - [x] نصب Python 3.11+ و pip
  - [x] نصب Node.js 20.x و npm
  - [x] نصب PostgreSQL tools
  - [x] تنظیم Git و مخزن
- [x] پیکربندی Docker
- [x] ساختار اولیه پروژه
- [x] تنظیم پایگاه داده
- [x] احراز هویت پایه

---

### فاز 2: شبکه درخواست 🔄
- [x] مدل‌های پایه
  - [x] User
  - [x] Request
- [x] API Endpoints
  - [x] مدیریت کاربران
  - [x] مدیریت درخواست‌ها
- [ ] پنل ادمین
  - [ ] داشبورد اصلی
  - [ ] مدیریت درخواست‌ها
  - [ ] مانیتورینگ سیستم
- [ ] Rate Limiting
- [ ] سیستم لاگینگ

### فاز 3: شبکه پاسخ 📝
- [x] مدل‌های پایه
- [x] API Endpoints
- [ ] پنل مدیریت
  - [ ] نمایش درخواست‌ها
  - [ ] مدیریت پردازش
  - [ ] مانیتورینگ
- [ ] سیستم لاگینگ

### فاز 4: انتقال داده ✅
- [x] فرمت فایل انتقال
- [x] Export Script
- [x] Import Script
- [x] Validation

### فاز 5: امنیت و تست 🛡️
- [ ] تست‌های واحد
  - [ ] Request API
  - [ ] Response API
  - [ ] File Transfer
- [ ] تست‌های یکپارچگی
- [ ] Security Hardening
  - [ ] Input Validation
  - [ ] Access Control
  - [ ] File Security

### فاز 6: مستندسازی و تحویل 📚
- [ ] مستندات API
- [ ] مستندات پیکربندی
- [ ] راهنمای کاربری
- [ ] مستندات فنی

## نکات و یادآوری‌ها 📝

### اولویت‌های فعلی
1. تکمیل پنل ادمین شبکه درخواست
2. پیاده‌سازی مانیتورینگ
3. تست و رفع باگ‌های احتمالی

### تغییرات معماری
- [x] ساده‌سازی مدل درخواست
- [x] حذف تفکیک کوئری/بچ/فایل
- [x] یکپارچه‌سازی مانیتورینگ
- [ ] بهبود سیستم لاگینگ

### مسائل باز
- تصمیم‌گیری درباره فرمت دقیق فایل‌های انتقال
- نحوه مدیریت خطاها در فرآیند انتقال
- استراتژی نگهداری لاگ‌ها
**تخمین زمان:** 2 ساعت  
**اولویت:** 🔴 بالا

---

### 1.3 Docker Compose Setup (Development)

- [ ] ایجاد `docker-compose.yml` اصلی
- [ ] تعریف service PostgreSQL (Request Network)
  - Port: 5432
  - Volume: `./data/postgres-request`
  - Environment variables
  - Health check
- [ ] تعریف service PostgreSQL (Response Network)
  - Port: 5433
  - Volume: `./data/postgres-response`
- [ ] تعریف service Redis (Request Network)
  - Port: 6379
  - Volume: `./data/redis-request`
  - Persistence: AOF + RDB
- [ ] تعریف service Redis (Response Network)
  - Port: 6380
  - Volume: `./data/redis-response`
- [ ] تعریف service Elasticsearch
  - Port: 9200
  - Volume: `./data/elasticsearch`
  - Memory limit: 2GB (dev)
  - Single node cluster
- [ ] ایجاد shared volumes برای /export و /import directories
- [ ] ایجاد shared network برای services
- [ ] تست راه‌اندازی تمام services

**وابستگی‌ها:** 1.2  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🔴 بالا

---

## PHASE 2: Database و Models (هفته 2-3)

### 2.1 Database Schema - Request Network

- [x] ایجاد Alembic configuration برای migrations
  - [x] `alembic init alembic`
  - [x] تنظیم `alembic.ini`
  - [x] تنظیم `env.py`
- [x] ایجاد initial migration
- [x] پیاده‌سازی `users` table (read-only replica)
  - UUID primary key (synced)
  - Fields for rate limiting, index access control, and user info
- [x] پیاده‌سازی `requests` table (Done)
  - UUID primary key
  - Foreign key به users
  - JSONB fields
  - Status field با enum
  - Indexes برای performance
- [x] پیاده‌سازی `responses` table (Done)
  - [x] One-to-one relation با requests
  - [x] JSONB result data
  - [x] Cache fields
- [x] پیاده‌سازی `export_batches` table (Done)
- [x] پیاده‌سازی `import_batches` table (Done)
- [x] پیاده‌سازی `audit_logs` table (Done)
- [x] پیاده‌سازی `api_keys` table (Done)
- [x] اجرای migrations و تست (Done)
- [ ] ایجاد seed data برای development
  - Admin user
  - Test users با profiles مختلف
  - Sample requests

**وابستگی‌ها:** 1.3  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🔴 بالا

---

### 2.2 Database Schema - Response Network

- [x] ایجاد Alembic configuration جداگانه
- [x] ایجاد initial migration
- [x] پیاده‌سازی `users` table (source of truth)
  - UUID primary key
  - Authentication fields (password hashing)
  - Basic user fields (without rate limiting)
  - Indexes & Constraints
- [x] پیاده‌سازی `incoming_requests` table
  - Mirror از requests table
  - بدون foreign key به users (isolated)
- [x] پیاده‌سازی `query_results` table
  - [x] Foreign key to `incoming_requests` (Done)
  - Elasticsearch execution metadata
- [x] پیاده‌سازی `query_cache` table (Done)
- [x] پیاده‌سازی `export_batches` table (مجدداً بررسی و تایید شد)
- [x] پیاده‌سازی `import_batches` table (مجدداً بررسی و تایید شد)
- [x] پیاده‌سازی `system_logs` table
- [x] اجرای migrations و تست
- [x] ایجاد seed data برای development

**وابستگی‌ها:** 2.1  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 2.3 SQLAlchemy Models

- [x] ایجاد base model با common fields
  - `id` (در هر مدل)
  - [x] Mixins برای `created_at`, `updated_at`
- [x] پیاده‌سازی `User` model (Response Network)
  - [x] Relationships (Implicitly handled by SQLAlchemy base)
  - [x] Password hashing methods
- [x] پیاده‌سازی `User` model (Request Network - read-only)
- [x] پیاده‌سازی `Request` model (Request Network)
  - [ ] Status transitions (will be implemented in workers)
  - [ ] Query builder methods (will be implemented in workers)
- [x] پیاده‌سازی `Response` model (Request Network)
- [x] پیاده‌سازی `ExportBatch` model (Both Networks)
- [x] پیاده‌سازی `ImportBatch` model (Both Networks)
- [x] پیاده‌سازی `AuditLog` model (Request Network)
- [x] پیاده‌سازی `APIKey` model (Request Network)
- [x] پیاده‌سازی models برای Response Network
  - [x] `IncomingRequest`
  - [x] `QueryResult`
  - [x] `SystemLog`
- [ ] نوشتن unit tests برای models
  - CRUD operations
  - Relationships
  - Custom methods

**وابستگی‌ها:** 2.1, 2.2  
**تخمین زمان:** 10 ساعت  
**اولویت:** 🔴 بالا

---

## PHASE 3: Shared Components (هفته 3-4)

### 3.1 File Format Handler

- [x] پیاده‌سازی `file_format_handler.py` در shared/
- [x] کلاس `JSONLHandler`:
  - [x] `write_jsonl()` - نوشتن به فرمت JSONL
  - [x] `read_jsonl()` - خواندن و parse
  - [ ] `validate_record()` - اعتبارسنجی structure (در فاز بعدی با اسکماها)
  - [x] `stream_read()` - خواندن streaming برای فایل‌های بزرگ
- [x] کلاس `BatchMetadata`:
  - [x] تولید metadata file
  - [ ] Validation metadata (در فاز بعدی با اسکماها)
- [x] File naming conventions
  - [x] `generate_filename()`
  - [x] `parse_filename()`
- [x] نوشتن unit tests
  - [x] `JSONLHandler` (write/read cycle, empty lines)
  - [x] `BatchMetadata` (creation and write)
  - [x] `generate_filename` and `parse_filename`
  - [x] `calculate_checksum`

**وابستگی‌ها:** 1.2  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 3.2 Encryption Handler

- [ ] ~~پیاده‌سازی `encryption.py` در shared/~~
- [ ] ~~کلاس `AESCipher` برای رمزنگاری و رمزگشایی~~
- [ ] ~~مدیریت کلیدها و IV~~
- [ ] ~~نوشتن unit tests~~

**وضعیت:** **لغو شد** - طبق تصمیم جدید، رمزنگاری فایل‌ها در این فاز پیاده‌سازی نمی‌شود.
**تخمین زمان:** 0 ساعت  
**اولویت:** 🔴 بالا

---

### 3.3 Shared Schemas (Pydantic)

- [x] ایجاد `shared/schemas/transfer.py`
- [x] Schema برای Request (برای انتقال داده):
  ```python
  class RequestTransferSchema(BaseModel):
      id: UUID
      user_id: UUID
      query_type: str
      query_params: dict
      priority: int
      timestamp: datetime
  ```
- [x] Schema برای Response:
  ```python
  class ResponseSchema(BaseModel):
      request_id: UUID
      result_data: dict
      execution_time_ms: int
      timestamp: datetime
  ```
- [x] Schema برای Batch:
  - `ExportBatchSchema`
  - `ImportBatchSchema`
  - `BatchMetadataSchema`
- [x] Validation rules
  - Field constraints
  - Custom validators
- [ ] Serialization/deserialization helpers
- [ ] نوشتن unit tests

**وابستگی‌ها:** 1.2
**تخمین زمان:** 4 ساعت  
**اولویت:** 🟡 متوسط

---

### 3.3 Logger Configuration

- [x] پیاده‌سازی `logger.py` با structlog
- [x] تابع `get_logger`:
  - [x] JSON output format (برای production)
  - [x] Console output format (برای development)
  - [x] Contextual logging (از طریق structlog.contextvars)
  - [x] Log levels (از طریق logging)
- [ ] کلاس `AuditLogger`:
  - Database logging برای audit trail
  - Async logging برای performance
- [ ] Integration با FastAPI
  - Request/response logging middleware
  - Error logging
- [ ] Log aggregation setup (اختیاری)
  - ELK stack یا Loki

**وابستگی‌ها:** 1.2  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🟡 متوسط

---

## PHASE 4: Request Network - API (هفته 4-5)

### 4.1 FastAPI Application Setup
- [x] ایجاد `main.py` در request-network/api/
- [x] Setup FastAPI app با configurations
  - [x] CORS middleware
  - [x] Exception handlers
  - [x] Request ID middleware
  - [x] Logging middleware
- [x] Database session dependency
  - [x] Connection pooling (handled by SQLAlchemy engine)
  - [x] Transaction management (handled by session context)
- [ ] Redis connection dependency
- [ ] Health check endpoints:
  - `GET /health` - Basic health
  - [x] `GET /health/ready` - Readiness (با DB check)
  - `GET /health/detailed` - تمام services
- [ ] OpenAPI documentation configuration
  - Title, description, version
  - Tags
  - Security schemes
- [ ] Static files serving (اگر لازم باشد)

**وابستگی‌ها:** 2.3  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🔴 بالا

---

### 4.2 Authentication System

- [x] پیاده‌سازی ساختار `auth` در api/ (Done)
- [x] JWT token generation (Done)
  - [x] Access token (1 hour expiry)
  - [ ] ~~Refresh token~~ (لغو شد - نیازی نیست)
  - [x] Token payload (user_id, scopes)
- [x] Password hashing با bcrypt
  - [ ] `hash_password()` (در `response-network` است)
  - [x] `verify_password()` (به مدل اضافه شد)
- [x] OAuth2 password bearer scheme (Done)
- [ ] Dependencies:
  - [x] `get_current_user()` - از JWT token (Done)
  - [x] `get_current_active_user()` - check is_active (Done)
  - [x] `require_role()` - RBAC decorator (Done)
- [x] API key authentication (Done)
  - Header-based: `X-API-Key`
  - Validation و rate limiting
- [ ] نوشتن unit tests
  - Token generation/validation
  - Password hashing
  - Authentication flow

**وابستگی‌ها:** 4.1  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 4.3 Rate Limiting Implementation

- [x] پیاده‌سازی `rate_limiter.py` (Done)
- [x] کلاس `RateLimiter`: (Done)
  - [x] Fixed window algorithm (Done)
  - [x] Multiple windows (minute, hour, day) (Done)
  - [x] Per-user limits based on profile (Done)
- [x] Dependency `check_rate_limit()`: (Done)
  - [x] Check current usage (Done)
  - [x] Increment counter (Done)
  - [x] Return remaining quota in headers (Done)
- [x] Rate limit exceeded exception (Done)
  - [x] Custom HTTP 429 response (Done)
  - [x] Retry-After header (Done)
- [x] Grace period برای soft limits ✅ COMPLETE
  - [x] Warning at 80% usage
  - [x] Soft block at 110% (grace period 5 min)
  - [x] Hard block at 100%
- [x] Admin endpoints برای reset limits
  - [x] GET /admin/rate-limit/user/{user_id}/stats
  - [x] POST /admin/rate-limit/user/{user_id}/reset
  - [x] POST /admin/rate-limit/user/{user_id}/custom-limits
  - [x] GET /admin/rate-limit/all
- [x] نوشتن unit tests
  - [x] Rate limit enforcement
  - [x] Different profiles
  - [x] Grace period flow
  - [x] Admin operations
- [x] Middleware برای grace period
- [x] Documentation (GRACE_PERIOD_GUIDE.md)

**Status:** ✅ COMPLETE (2025-11-25)  
**وابستگی‌ها:** 4.1  
**تخمین زمان:** 3 ساعت (✅ Complete)  
**اولویت:** 🔴 بالا

---

### 4.4 User Management Endpoints

- [x] ایجاد Router برای مدیریت کاربران توسط ادمین (`admin_router.py`) (Done)
- [x] `POST /auth/login`: (انجام شده در بخش 4.2)
  - احراز هویت کاربر و صدور توکن دسترسی.
- [ ] ~~`GET /users/me`~~ (لغو شد - در `request-network` کاربر فقط replica است)
- [ ] ~~`PUT /users/me`~~ (لغو شد - مدیریت کاربر در `response-network` انجام می‌شود)
- [ ] ~~`POST /auth/register`~~ (لغو شد - مدیریت کاربران در `response-network` است)
- [ ] ~~`POST /auth/refresh`~~ (لغو شد - نیازی به Refresh Token نیست)
- [ ] ~~`POST /auth/logout`~~ (لغو شد - فعلاً نیازی نیست)
- [ ] ~~`POST /users/me/change-password`~~ (لغو شد - فعلاً نیازی نیست)
- [x] پیاده‌سازی Endpoints برای ادمین: (Done)
  - [x] `GET /admin/users`: لیست تمام کاربران (با pagination و فیلتر). (Done)
  - [x] `GET /admin/users/{user_id}`: مشاهده جزئیات یک کاربر خاص. (Done)
  - [x] `POST /admin/users/{user_id}/activate`: فعال کردن یک کاربر (برای دسترسی فوری). (Done)
  - [x] `POST /admin/users/{user_id}/deactivate`: غیرفعال کردن یک کاربر (برای دسترسی فوری). (Done)
- [ ] نوشتن unit tests برای endpoints ادمین.

**وابستگی‌ها:** 4.2, 4.3  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🔴 بالا

---

### 4.5 Request Submission Endpoints

- [x] Router `requests.py` در api/routers/ (Done)
- [x] `POST /requests`: (Done)
  - دریافت query parameters
  - Validation با Pydantic schema
  - Rate limit check
  - ذخیره در database با status='pending'
  - Return request_id
- [x] `GET /requests`: (Done)
  - لیست درخواست‌های کاربر با pagination
  - Filtering by status
  - Sorting by created_at
- [x] `GET /requests/{request_id}`: (Done)
  - جزئیات درخواست
  - شامل response (اگر موجود باشد)
- [x] `GET /requests/{request_id}/status`: (Done)
  - فقط status درخواست (lightweight)
- [x] `DELETE /requests/{request_id}`: (Done)
  - Cancel request (فقط اگر pending باشد)
- [x] Validation logic: (Done)
  - [x] Query type validation
  - [x] Query params structure validation
  - [x] Elasticsearch index whitelist
- [ ] نوشتن unit tests
- [ ] Integration tests

**وابستگی‌ها:** 4.2, 4.3  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 4.6 Response Retrieval Endpoints

- [x] `GET /requests/{request_id}/response`:
  - [x] دریافت result
  - [x] Cache check (Redis)
  - [x] Return با metadata (execution time, etc.)
- [x] Response caching strategy:
  - [x] Cache در Redis برای hot data (TTL: 24 hours)
  - [x] Fallback به PostgreSQL
  - [x] Auto-cache on first retrieval
- [x] Admin cache management endpoints:
  - [x] `GET /admin/cache/stats` - Cache statistics
  - [x] `DELETE /admin/cache/clear` - Clear all cache
  - [x] `DELETE /admin/cache/user/{user_id}` - Clear user cache
- [x] Cache invalidation در worker tasks
  - [x] Auto-invalidate when new response imported
- [ ] نوشتن tests
- [ ] Load testing for cache effectiveness

**Status:** ✅ IMPLEMENTED (2025-11-25)  
**وابستگی‌ها:** 4.5  
**تخمین زمان:** 3 ساعت (✅ Complete)  
**اولویت:** 🔴 بالا

---

### 4.7 API Key Management Endpoints

- [ ] Router `api_keys.py`
- [ ] `POST /api-keys`:
  - Generate new API key
  - Specify name و scopes
  - Return key (فقط یکبار!)
- [ ] `GET /api-keys`:
  - لیست API keys کاربر
  - بدون نمایش actual key
- [ ] `DELETE /api-keys/{key_id}`:
  - Revoke API key
- [ ] Key generation logic:
  - Random secure string (32 bytes)
  - Prefix برای identification (e.g., "pk_live_...")
  - Hash برای storage (SHA-256)
- [x] Router `api_keys.py` (Done)
- [x] `POST /api-keys`: (Done)
  - [x] Generate new API key (Done)
  - [x] Specify name و scopes (Done)
  - [x] Return key (فقط یکبار!) (Done)
- [x] `GET /api-keys`: (Done)
  - [x] لیست API keys کاربر (Done)
  - [x] بدون نمایش actual key (Done)
- [x] `DELETE /api-keys/{key_id}`: (Done)
  - [x] Revoke API key (Done)
- [x] Key generation logic: (Done)
  - [x] Random secure string (32 bytes) (Done)
  - [x] Prefix برای identification (e.g., "sk_live_...") (Done)
  - [x] Hash برای storage (SHA-256) (Done)
- [ ] نوشتن tests

**وابستگی‌ها:** 4.2  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🟡 متوسط

---

### 4.8 Admin Endpoints

- [ ] Router `admin.py`
- [ ] `GET /admin/stats`:
  - کل درخواست‌ها
  - Active users
  - Success/failure rates
  - Top users by request count
- [ ] `GET /admin/requests`:
  - لیست تمام درخواست‌ها (با filters)
  - Pagination
- [ ] `GET /admin/export-batches`:
  - لیست export batches
  - Status monitoring
- [ ] `GET /admin/import-batches`:
  - لیست import batches
- [ ] `GET /admin/audit-logs`:
  - Audit trail با filters
  - Pagination
- [ ] `POST /admin/users/{user_id}/reset-rate-limit`:
  - Reset rate limit counter
- [ ] تمام endpoints نیاز به role='admin' دارند
- [ ] نوشتن tests

**وابستگی‌ها:** 4.2  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🟡 متوسط

---

## PHASE 5: Request Network - Workers (هفته 5-6)

### 5.1 Celery Setup
- [x] ایجاد `celery_app.py` در request-network/workers/
- [x] Celery configuration:
  - [x] Broker: Redis
  - [x] Backend: Redis
  - [x] Serializer: JSON
  - [ ] Task routes (در آینده اضافه می‌شود)
  - [ ] Rate limits (در آینده اضافه می‌شود)
- [x] ایجاد `config.py` برای worker settings
- [x] Beat scheduler configuration
  - [x] Schedule definitions
- [ ] Task base class با logging
- [ ] Error handling و retries
  - Exponential backoff
  - Max retries: 3
- [ ] Dead letter queue برای failed tasks
- [x] تست connection به Redis (از طریق broker/backend URL)
- [ ] Setup Flower برای monitoring (port 5555)

**وابستگی‌ها:** 1.3  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🔴 بالا

---




### 5.2 Export Requests Task

- [x] ایجاد `tasks/export_requests.py`
- [x] Task `export_pending_requests()`:
  - [x] Schedule: هر 2 دقیقه (via Celery Beat)
  - [x] Query pending requests از database:
    ```sql
    SELECT * FROM requests
    WHERE status = 'pending'
    ORDER BY priority DESC, created_at ASC
    LIMIT 500
    ```
  - [x] Generate batch_id (UUID)
  - [x] تبدیل به JSONL format
  - [x] Calculate checksum (SHA-256)
  - [x] Save to /export/ directory
  - [x] Update requests status به 'exported'
  - [x] Create export_batch record
  - [ ] Generate metadata file (در `BatchMetadata` پیاده‌سازی شده، اما فراخوانی مستقیم آن در تسک بعدی اضافه می‌شود)
- [x] Error handling:
  - [x] Database errors (با `db_session_scope`)
  - [ ] File I/O errors (در آینده بهبود می‌یابد)
  - [ ] Encryption errors (فعلا لغو شده)
  - [x] Rollback on failure (با `db_session_scope`)
- [x] Logging:
  - [x] Start/end timestamps (توسط Celery لاگ می‌شود)
  - [x] Record count
  - [x] File size
  - [ ] Errors (در آینده بهبود می‌یابد)
- [ ] Metrics (در فاز مانیتورینگ اضافه می‌شود):
  - Export duration
  - Batch size
  - Success/failure rate
- [ ] نوشتن unit tests
  - Mock database
  - Mock file operations
- [ ] Integration tests
  - End-to-end با real database

**وابستگی‌ها:** 3.1, 5.1
**تخمین زمان:** 8 ساعت  
**اولویت:** 🔴 بالا

---

### 5.3 Import Results Task

- [x] ایجاد `tasks/import_results.py`
- [x] Task `import_response_files()`:
  - [x] Schedule: هر 30 ثانیه (polling)
  - [x] Scan /import/ directory
  - [x] For each `.jsonl` file:
    - [x] Check if already processed (by checksum)
    - [ ] Validate metadata file (در آینده اضافه می‌شود)
    - [x] Verify checksum (به عنوان بخشی از چک کردن تکراری)
    - [x] Parse JSONL
    - [x] Validate each record
    - [x] Begin transaction:
      - [x] Insert into responses table
      - [x] Update requests status به 'completed'
      - [x] Update result_received_at
      - [ ] Cache در Redis (در فاز بعدی)
      - [x] Create import_batch record
    - [x] Commit transaction
    - [x] Move file to /import/archive/
    - [x] Delete original file (بخشی از عملیات move)
- [x] Error handling:
  - [x] Corrupted file → move to /import/failed/
  - [x] Duplicate → skip با log و آرشیو
  - [x] Parse error → log و انتقال به failed
  - [x] Database error → rollback و retry (با Celery)
- [x] Logging کامل
- [ ] Metrics (در فاز مانیتورینگ)
- [ ] نوشتن tests

**وابستگی‌ها:** 3.1, 5.1
**تخمین زمان:** 8 ساعت  
**اولویت:** 🔴 بالا

---

### 5.4 Cleanup Task

- [ ] ایجاد `tasks/cleanup.py`
- [ ] Task `cleanup_old_data()`:
  - Schedule: روزانه ساعت 02:00
  - Archive old requests (> 30 days):
    - Export to archive file (JSON/CSV)
    - Move to cold storage
    - Delete from database
  - Delete old export files (> 7 days)
  - Delete old import archives (> 30 days)
  - Clean Redis expired keys (اگر لازم باشد)
  - Vacuum PostgreSQL tables
  - Rotate log files
- [ ] Configuration:
  - Retention periods (configurable)
  - Archive path
- [ ] Logging
- [ ] Metrics
- [ ] نوشتن tests

**وابستگی‌ها:** 5.1  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🟢 پایین

---

### 5.5 Notification Task (Optional)

- [ ] ایجاد `tasks/notifications.py`
- [ ] Task `send_notification()`:
  - Email notification
  - Webhook notification
  - در صورت complete شدن request
- [ ] Template system برای emails
- [ ] Retry logic برای failed notifications
- [ ] User preferences برای enable/disable
- [ ] نوشتن tests

**وابستگی‌ها:** 5.1  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🟢 پایین (Optional)

---

## PHASE 6: Response Network - Workers (هفته 6-7)

### 6.1 Celery Setup (Response Network)

- [x] ایجاد `celery_app.py` در response-network/workers/
- [x] Configuration مشابه Request Network
- [ ] Task routing: (در فازهای بعدی پیاده‌سازی می‌شود)
  - [ ] `import_queue` - high priority
  - [ ] `query_queue` - با priority levels
  - [ ] `export_queue` - medium priority
- [ ] Worker pool configuration: (در `docker-compose.prod.yml` تعریف خواهد شد)
  - [ ] 8 workers (configurable)
  - [ ] Concurrency settings
- [ ] Setup Flower (در فازهای بعدی اضافه می‌شود)

**وابستگی‌ها:** 1.3  
**تخمین زمان:** 3 ساعت  
**اولویت:** 🔴 بالا

---

### 6.2 Elasticsearch Client

- [x] ایجاد `elasticsearch_client.py`
- [x] کلاس `ElasticsearchClient`:
  - [x] Connection management
  - [x] Connection pooling (handled by the client library)
  - [x] Health check
  - [x] Retry logic (handled by the client library)
- [x] Query methods:
  - [x] `execute_query()` - main method
  - [x] `validate_query()` - قبل از اجرا
  - [x] `build_es_query()` - از params به ES query
- [x] Security:
  - [ ] Read-only user credentials (TODO for production)
  - [ ] Index whitelist validation (TODO, placeholder added)
  - [x] Query timeout: 30 seconds (from config)
  - [x] Result size limit: 1000 (from config)
- [x] Error handling:
  - [x] Connection errors
  - [x] Timeout errors (handled by retry)
  - [x] Query syntax errors (via `TransportError`)
- [x] Logging
- [ ] نوشتن unit tests با mock
- [ ] Integration tests با real Elasticsearch

**وابستگی‌ها:** 1.3  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 6.3 Import Requests Task

- [x] ایجاد `tasks/import_requests.py`
- [x] Task `import_request_files()`:
  - [x] Schedule: هر 30 ثانیه
  - [x] Scan /import/ directory
  - [x] For each file:
    - [x] Validate checksum
    - [x] Parse requests
    - [x] Check duplicates (by checksum)
    - [x] Begin transaction:
      - [x] Insert into incoming_requests
      - [x] Create import_batch record
    - [x] Commit
    - [x] برای هر request:
      - [x] Push to Celery queue با priority
      - [x] `execute_query_task.apply_async(args=[...], priority=...)`
    - [x] Archive file
- [x] Error handling (basic try/except, move to failed)
- [x] Logging
- [ ] Metrics (در فاز مانیتورینگ)
- [ ] نوشتن tests

**وابستگی‌ها:** 3.1, 3.2, 6.1  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 6.4 Query Executor Task

- [x] ایجاد `tasks/query_executor.py`
- [x] Task `execute_query_task()`:
  - [x] Triggered: از `import_requests` (via Celery)
  - [x] برای هر request:
    1. [x] Pop from queue (توسط Celery worker)
    2. [x] Load request از database
    3. [x] Update status به 'processing'
    4. [x] Generate cache key:
       ```python
       cache_key = f"es:{index}:{hash(query)}:{size}:{from}"
       ```
    5. [x] Check cache (Redis):
       - [x] If cache hit:
         - [x] Return cached result
       - [x] If cache miss:
         - [x] Build Elasticsearch query
         - [x] Validate query (توسط ES client)
         - [x] Execute query
         - [x] Store result در database (در مرحله ۷)
         - [x] Cache در Redis (با TTL)
    6. [x] Update incoming_requests:
       - [x] status = 'completed'
       - [x] completed_at = now()
    7. [x] Insert into query_results:
       - [x] result_data
       - [x] execution_time_ms
       - [x] cache_hit boolean
- [x] Error handling:
  - [x] Elasticsearch errors → status='failed'
  - [x] Timeout → retry (توسط Celery)
  - [x] Query syntax error → status='failed' (no retry)
- [x] Logging کامل
- [ ] Metrics: (در فاز مانیتورینگ)
  - [ ] Query duration
  - [ ] Cache hit ratio
  - [ ] Success/failure rate
- [ ] نوشتن unit tests
- [ ] Integration tests

**وابستگی‌ها:** 6.2, 6.3  
**تخمین زمان:** 10 ساعت  
**اولویت:** 🔴 بالا

---

### 6.5 Export Results Task

- [x] ایجاد `tasks/export_results.py`
- [x] Task `export_completed_results()`:
  - [x] Schedule: هر 2 دقیقه
  - [x] Query completed results (not exported):
    ```sql
    SELECT * FROM query_results
    WHERE exported_at IS NULL
    ORDER BY executed_at ASC
    LIMIT 500
    ```
  - [x] Generate JSONL:
    ```json
    {"request_id": "uuid", "result_data": {...}, "execution_time_ms": 123}
    ```
  - [x] Calculate checksum
  - [x] Save to /export/
  - [x] Update exported_at timestamp
  - [x] Create export_batch record
  - [ ] Generate metadata (در آینده اضافه می‌شود)
- [x] Error handling (basic, via `db_session_scope`)
- [x] Logging
- [ ] Metrics (در فاز مانیتورینگ)
- [ ] نوشتن tests

**وابستگی‌ها:** 3.1, 6.1
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 6.6 Cache Maintenance Task

- [x] ایجاد `tasks/cache_maintenance.py`
- [x] Task `maintain_cache()`:
  - [x] Schedule: هر ساعت
  - [x] Clean expired cache entries:
    - [x] Redis: TTL-based (automatic, but can be monitored)
  - [x] Update statistics:
    - [x] Cache size monitoring (via logging)
  - [x] Log cache metrics:
    - [ ] Hit ratio (نیاز به مکانیزم جداگانه دارد، در آینده اضافه می‌شود)
    - [x] Memory usage
- [ ] نوشتن tests

**وابستگی‌ها:** 6.1  
**تخمین زمان:** 3 ساعت  
**اولویت:** 🟡 متوسط

---

### 6.7 System Monitoring Task

- [x] ایجاد `tasks/system_monitoring.py` (نام فایل)
- [x] Task `system_health_check()`:
  - [x] Schedule: هر 5 دقیقه
  - [x] Check services:
    - [x] PostgreSQL connection
    - [x] Redis connection
    - [x] Elasticsearch cluster health
  - [ ] Check resources: (در فاز مانیتورینگ پیشرفته با Prometheus اضافه می‌شود)
    - [ ] Disk space (> 80% alert)
    - [ ] Memory usage (> 90% alert)
    - [ ] Queue backlog (> 1000 alert)
  - [ ] Log metrics to system_logs table (در آینده اضافه می‌شود)
  - [ ] Send alerts (در آینده اضافه می‌شود)
- [ ] نوشتن tests

**وابستگی‌ها:** 6.1  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🟡 متوسط

---

## PHASE 7: Response Network - Admin Panel Backend ✅ COMPLETE

### 7.1 Admin Panel Monitoring API ✅ COMPLETE (2025-11-25)

- [x] ایجاد admin_panel.py router
- [x] Health endpoints:
  - [x] `GET /admin/health` - basic health check
  - [x] `GET /admin/health/detailed` - detailed service status
- [x] System Statistics endpoints:
  - [x] `GET /admin/stats/system` - overall system stats
  - [x] `GET /admin/stats/queues` - Celery queue length
  - [x] `GET /admin/stats/cache` - Redis cache metrics
- [x] Cache Management endpoints:
  - [x] `DELETE /admin/cache/clear` - clear all cache
  - [x] `POST /admin/cache/optimize` - optimize cache
- [x] User Management endpoints:
  - [x] `GET /admin/users/list` - list all users (paginated)
  - [x] `GET /admin/users/{user_id}` - user details
- [x] Request Monitoring endpoints:
  - [x] `GET /admin/requests/recent` - recent requests
  - [x] `GET /admin/requests/stats` - request statistics
- [x] Authentication:
  - [x] Require admin role via JWT
  - [x] Per-endpoint authentication
- [x] Integration in main.py
- [x] Documentation (ADMIN_PANEL_BACKEND.md)

**Status:** ✅ COMPLETE (2025-11-25)  
**وابستگی‌ها:** 6.1, require_admin  
**تخمین زمان:** 6 ساعت (✅ Complete)  
**اولویت:** 🔴 بالا

---

## PHASE 8: Admin Panel Frontend (Next.js) - Response Network

### 8.1 Next.js Setup

- [x] انتقال Next.js app به `response-network/admin-panel/`
- [x] Project configuration:
  - [x] TypeScript strict mode (by default)
  - [x] ESLint (by default)
  - [x] Path aliases (@/components, @/lib/utils)
- [x] Install dependencies:
  - [x] shadcn/ui
  - [x] TanStack Query
  - [x] Zustand
  - [x] React Hook Form
  - [x] Zod
  - [x] @hookform/resolvers (برای اتصال به Zod)
  - [x] Axios
  - [x] Lucide icons
  - [x] next-themes
- [x] Setup theme (light/dark)
- [x] Setup layouts:
  - [x] Main layout (پایه اولیه با ThemeProvider ایجاد شد)
  - [x] Auth layout (ایجاد شد)
- [ ] Create API client:
  - [ ] Axios instance برای اتصال به Monitoring API

**وابستگی‌ها:** هیچ  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🟡 متوسط

---

### 8.2 Authentication Pages

- [x] صفحه Login (`/login`):
  - [x] Username/password form (UI created)
  - [x] Remember me checkbox (UI created)
  - [ ] اتصال به API برای احراز هویت (در `response-network`)
  - [ ] Error handling
  - [ ] Redirect to dashboard
- [ ] صفحه Register (`/register`):
  - فرم ثبت‌نام برای ایجاد کاربر جدید در `response-network`
- [ ] Protected routes:
  - Middleware برای check authentication
  - Redirect to /login اگر not authenticated
- [ ] Token management (JWT):
  - [ ] **(Production Security)**: پیاده‌سازی مکانیزم Refresh Token برای افزایش امنیت.
  - [ ] **(Production Security)**: تغییر مکانیزم احراز هویت به استفاده از کوکی‌های `HttpOnly` و `Secure` برای جلوگیری از حملات XSS.
    - [ ] ارسال Access Token (کوتاه‌مدت) در بدنه پاسخ.
    - [ ] ارسال Refresh Token (بلندمدت) در یک کوکی `HttpOnly`.
  - [ ] **(Production Security)**: پیاده‌سازی اندپوینت امن برای Logout (حذف کوکی Refresh Token).
- [ ] نوشتن tests (با Playwright/Cypress)

**وابستگی‌ها:** 8.1  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🔴 بالا

---

### 8.3 Monitoring Dashboard

- [ ] صفحه Dashboard (`/`):
  - System stats (از Monitoring API):
    - Queue length
    - Active workers
    - Elasticsearch health
    - Cache hit ratio
  - Charts:
    - Queries over time
    - Query execution time
  - Recent queries table
  - Alerts/notifications
- [ ] Real-time updates

**وابستگی‌ها:** 8.2, 7.1  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🟡 متوسط

---

### 8.4 Users Management Page (Admin)

- [ ] صفحه Users (`/admin/users`):
  - Data table:
    - مدیریت کامل کاربران (CRUD)
    - Pagination, sorting, filtering
  - View user details:
    - Profile info
    - Rate limits
- [ ] Role-based access:
  - فقط admin ها
- [ ] نوشتن tests

**وابستگی‌ها:** 8.2  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🔴 بالا

---

### 8.5 Requests & Results Page

- [ ] صفحه Requests (`/requests`):
  - Data table برای `incoming_requests`
  - Status monitoring
  - Details modal
- [ ] صفحه Results (`/results`):
  - Data table برای `query_results`
  - Result preview
  - Execution details
  - Cache info
- [ ] Actions:
  - Retry failed
  - View result

**وابستگی‌ها:** 8.2  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🔴 بالا

---

### 8.6 System Management Pages

- [ ] صفحه Cache (`/system/cache`):
  - Cache entries table
  - Actions: Invalidate cache, Clear all
- [ ] صفحه Batches (`/system/batches`):
  - مانیتورینگ export/import batches در `response-network`
- [ ] صفحه Logs (`/system/logs`):
  - نمایش `system_logs` با فیلترینگ

**وابستگی‌ها:** 8.2  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🟡 متوسط

---

### 8.7 Settings Page

- [ ] صفحه Settings (`/settings`):
  - User settings:
    - Profile (name, email)
    - Change password
    - API keys management
    - Notification preferences
  - Admin settings (if admin):
    - System configuration
    - Rate limits defaults
    - Maintenance mode
- [ ] Form validation
- [ ] Success/error notifications
- [ ] نوشتن tests

**وابستگی‌ها:** 8.2  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🟡 متوسط

---

## PHASE 10: Testing (هفته 10)

### 10.1 Unit Tests

- [ ] Backend tests:
  - Models (CRUD, relationships)
  - Utilities (encryption, file format)
  - Authentication
  - Rate limiting
  - API endpoints
  - Celery tasks
- [ ] هدف coverage: >80%
- [ ] Setup pytest-cov برای coverage report
- [ ] CI/CD integration

**وابستگی‌ها:** همه phases قبلی  
**تخمین زمان:** 12 ساعت  
**اولویت:** 🔴 بالا

---

### 10.2 Integration Tests

- [ ] End-to-end workflows:
  - Request submission → Export → Import → Query → Export → Import → Response
- [ ] Database integration tests
- [ ] Redis integration tests
- [ ] Elasticsearch integration tests
- [ ] File operations tests
- [ ] Setup test databases (Docker)

**وابستگی‌ها:** 10.1  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🔴 بالا

---

### 10.3 Performance Tests

- [ ] Setup Locust
- [ ] Load test scenarios:
  - 200 req/min sustained
  - 500 req/min spike
- [ ] Latency tests:
  - p95 < 200ms (API)
  - p95 < 500ms (Query execution)
- [ ] Resource monitoring during tests
- [ ] Performance report

**وابستگی‌ها:** 10.1, 10.2  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🟡 متوسط

---

### 10.4 Security Tests

- [ ] OWASP Top 10 checks
- [ ] SQL injection tests
- [ ] XSS tests
- [ ] Authentication bypass attempts
- [ ] Rate limiting validation
- [ ] Encryption verification
- [ ] API security scan
- [ ] Security report

**وابستگی‌ها:** 10.1  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 10.5 Frontend Tests

- [ ] Component tests (React Testing Library)
- [ ] E2E tests (Playwright/Cypress):
  - Login flow
  - Admin operations
- [ ] Visual regression tests (optional)
- [ ] Accessibility tests

**وابستگی‌ها:** Phase 8  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🟡 متوسط

---

## PHASE 11: Documentation (هفته 11)

### 11.1 API Documentation

- [ ] OpenAPI/Swagger documentation:
  - همه endpoints documented
  - Request/response examples
  - Authentication guide
  - Error codes
- [ ] Postman collection
- [ ] API usage guide با examples

**وابستگی‌ها:** Phase 4  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🟡 متوسط

---

### 11.2 Deployment Guide

- [ ] نوشتن `DEPLOYMENT.md`:
  - Prerequisites
  - Server requirements
  - Installation steps
  - Configuration
  - Database setup
  - Initial data/seed
  - Starting services
  - Verification
- [ ] Docker deployment guide
- [ ] Production checklist

**وابستگی‌ها:** همه phases  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🔴 بالا

---

### 11.3 Operations Guide

- [ ] نوشتن `OPERATIONS.md`:
  - Daily operations
  - Monitoring
  - Backup/restore procedures
  - Log management
  - Performance tuning
  - Troubleshooting common issues
  - Disaster recovery
- [ ] Runbooks برای common scenarios

**وابستگی‌ها:** همه phases  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🟡 متوسط

---

### 11.4 User Manual

- [ ] نوشتن `USER_GUIDE.md`:
  - Getting started
  - Submitting requests
  - Checking status
  - Retrieving results
  - API key management
  - Rate limiting explained
  - Query syntax guide
  - Examples
- [ ] Admin manual:
  - User management
  - System monitoring
  - Batch management
  - Troubleshooting

**وابستگی‌ها:** Phase 8  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🟡 متوسط

---

### 11.5 Developer Documentation

- [ ] نوشتن `CONTRIBUTING.md`:
  - Code style guide
  - Git workflow
  - Testing guidelines
  - PR process
- [ ] Code documentation:
  - Inline comments
  - Docstrings
  - Type hints
- [ ] Architecture diagrams:
  - System architecture
  - Data flow
  - Database schema
  - Deployment architecture

**وابستگی‌ها:** همه phases  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🟢 پایین

---

## PHASE 12: Production Preparation (هفته 11-12)

### 12.1 Docker Production Images

- [ ] ایجاد `Dockerfile` برای API (Request Network)
  - Multi-stage build
  - Minimize image size
  - Non-root user
- [ ] ایجاد `Dockerfile` برای Workers (Request Network)
- [ ] ایجاد `Dockerfile` برای API (Response Network)
- [ ] ایجاد `Dockerfile` برای Workers (Response Network)
- [ ] ایجاد `Dockerfile` برای Admin Panels
- [ ] ایجاد `docker-compose.prod.yml`
  - Production configurations
  - Environment variables
  - Volumes
  - Networks
  - Resource limits
- [ ] تست images در محیط staging

**وابستگی‌ها:** همه phases  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 12.2 Environment Configuration

- [ ] ایجاد `.env.production` templates
- [ ] Secret management:
  - Database passwords
  - JWT secret
  - API keys
- [ ] Configuration validation
- [ ] Environment-specific settings:
  - Log levels
  - Debug mode
  - CORS origins
  - Rate limits

**وابستگی‌ها:** 12.1  
**تخمین زمان:** 3 ساعت  
**اولویت:** 🔴 بالا

---

### 12.3 Database Migrations & Seeding

- [ ] Review همه migrations
- [ ] Production seed data:
  - Admin user
  - Default settings
- [ ] Migration testing:
  - Fresh install
  - Upgrade path
  - Rollback procedure
- [ ] Backup strategy before migrations

**وابستگی‌ها:** Phase 2  
**تخمین زمان:** 2 ساعت  
**اولویت:** 🔴 بالا

---

### 12.4 Monitoring & Logging Setup

- [ ] Prometheus setup (optional):
  - Exporters
  - Scrape configurations
  - Recording rules
  - Alert rules
- [ ] Grafana setup (optional):
  - Dashboards
  - Data sources
  - Alerts
- [ ] Loki setup برای logs (optional)
- [ ] Application metrics:
  - Integrate prometheus-client در FastAPI
  - Celery metrics
- [ ] Health monitoring:
  - Uptime checks
  - Service dependencies

**وابستگی‌ها:** همه phases  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🟡 متوسط (Optional)

---

### 12.5 Backup & Recovery

- [ ] Automated backup scripts:
  - PostgreSQL dumps (daily + hourly incremental)
  - Redis snapshots (daily)
  - Elasticsearch snapshots (daily)
  - File backups (export/import directories)
- [ ] Backup rotation:
  - Retention policy: 30 days
  - Archive old backups
- [ ] Recovery procedures:
  - Database restore
  - Point-in-time recovery
  - File recovery
- [ ] Test recovery process
- [ ] Documentation

**وابستگی‌ها:** Phase 2  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 12.6 Security Hardening

- [ ] Review security checklist (از ARCHITECTURE.md)
- [ ] SSL/TLS certificates:
  - Generate/obtain certificates
  - Configure Nginx/Traefik
  - Force HTTPS
- [ ] Firewall configuration:
  - iptables/firewalld rules
  - Allow only necessary ports
  - Block external access to databases
- [ ] Secrets rotation:
  - Database passwords
  - JWT secret
- [ ] Security audit:
  - Penetration testing
  - Vulnerability scan
- [ ] Security documentation

**وابستگی‌ها:** همه phases  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 12.7 Performance Optimization

- [ ] Database optimization:
  - Index review
  - Query optimization
  - Connection pooling (PgBouncer)
  - Vacuum schedule
- [ ] Redis optimization:
  - Memory limits
  - Eviction policy
  - Persistence configuration
- [ ] API optimization:
  - Response caching
  - Query optimization
  - Connection pooling
- [ ] Elasticsearch optimization:
  - Shard configuration
  - Replica settings
  - Index lifecycle management
- [ ] Load testing و tuning

**وابستگی‌ها:** Phase 10.3  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🟡 متوسط

---

### 12.8 Deployment Automation

- [ ] CI/CD pipeline (optional):
  - GitHub Actions / GitLab CI
  - Automated testing
  - Docker image build
  - Deployment to staging
  - Deployment to production (manual approval)
- [ ] Deployment scripts:
  - `deploy.sh` برای deployment
  - `rollback.sh` برای rollback
  - `health_check.sh` برای verification
- [ ] Documentation

**وابستگی‌ها:** 12.1, 12.2  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🟢 پایین (Optional)

---

## PHASE 13: Staging & Pre-Production Testing (هفته 12)

### 13.1 Staging Environment Setup

- [ ] راه‌اندازی staging servers
- [ ] Deploy همه services
- [ ] Configuration staging environment
- [ ] Load sample data
- [ ] Smoke tests

**وابستگی‌ها:** Phase 12  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🔴 بالا

---

### 13.2 Integration Testing (Staging)

- [ ] End-to-end testing:
  - Full request/response cycle
  - Multiple users
  - Different scenarios
- [ ] Performance testing
- [ ] Stress testing
- [ ] Failover testing
- [ ] Recovery testing

**وابستگی‌ها:** 13.1  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🔴 بالا

---

### 13.3 User Acceptance Testing (UAT)

- [ ] UAT plan
- [ ] Test cases
- [ ] User training
- [ ] Feedback collection
- [ ] Bug fixes
- [ ] Re-testing

**وابستگی‌ها:** 13.2  
**تخمین زمان:** 8 ساعت  
**اولویت:** 🔴 بالا

---

### 13.4 Production Checklist Review

- [ ] Review pre-deployment checklist (از ARCHITECTURE.md)
- [ ] Verify همه items
- [ ] Final security scan
- [ ] Performance verification
- [ ] Backup verification
- [ ] Documentation completeness
- [ ] Go/No-Go meeting

**وابستگی‌ها:** 13.3  
**تخمین زمان:** 2 ساعت  
**اولویت:** 🔴 بالا

---

## PHASE 14: Production Deployment (هفته 13)

### 14.1 Production Servers Setup

- [ ] Provision servers:
  - Request Network server
  - Response Network server
- [ ] Install OS (Ubuntu 22.04 LTS)
- [ ] System updates
- [ ] Install Docker & Docker Compose
- [ ] Network configuration
- [ ] Firewall configuration
- [ ] DNS configuration (اگر نیاز باشد)

**وابستگی‌ها:** Phase 13  
**تخمین زمان:** 4 ساعت  
**اولویت:** 🔴 بالا

---

### 14.2 Services Deployment

- [ ] Deploy Request Network:
  - Clone repository
  - Set environment variables
  - Run migrations
  - Start services
  - Verify health checks
- [ ] Deploy Response Network:
  - مشابه Request Network
  - Setup Elasticsearch
  - Verify connectivity
- [ ] Setup monitoring
- [ ] Setup backups
- [ ] Verify logging

**وابستگی‌ها:** 14.1  
**تخمین زمان:** 6 ساعت  
**اولویت:** 🔴 بالا

---

### 14.3 Initial Data & Configuration

- [ ] Create admin user
- [ ] Create initial users (if needed)
- [ ] Configure rate limits
- [ ] Setup API keys
- [ ] Configure Elasticsearch indices
- [ ] Test file transfer:
  - Export from Request Network
  - Manual transfer
  - Import to Response Network

**وابستگی‌ها:** 14.2  
**تخمین زمان:** 2 ساعت  
**اولویت:** 🔴 بالا

---

### 14.4 Production Smoke Tests

- [ ] API tests:
  - Authentication
  - Request submission
  - Response retrieval
- [ ] Worker tests:
  - Export job
  - Import job
  - Query execution
- [ ] Admin panel tests:
  - Login
  - Dashboard
  - User management
- [ ] End-to-end test:
  - کامل workflow

**وابستگی‌ها:** 14.3  
**تخمین زمان:** 3 ساعت  
**اولویت:** 🔴 بالا

---

### 14.5 Production Launch

- [ ] Announce go-live
- [ ] Enable services
- [ ] Monitor closely:
  - Logs
  - Metrics
  - Errors
  - Performance
- [ ] User onboarding
- [ ] Documentation distribution
- [ ] Support readiness

**وابستگی‌ها:** 14.4  
**تخمین زمان:** 2 ساعت  
**اولویت:** 🔴 بالا

---

## PHASE 15: Post-Launch (هفته 13+)

### 15.1 Monitoring & Maintenance

- [ ] Daily monitoring:
  - System health
  - Error rates
  - Performance metrics
  - Queue backlogs
- [ ] Weekly reviews:
  - Usage statistics
  - Performance trends
  - User feedback
- [ ] Monthly tasks:
  - Security updates
  - Dependency updates
  - Backup verification
  - Performance tuning

**وابستگی‌ها:** Phase 14  
**تخمین زمان:** Ongoing  
**اولویت:** 🔴 بالا

---

### 15.2 User Feedback & Iteration

- [ ] Collect user feedback
- [ ] Bug reports
- [ ] Feature requests
- [ ] Prioritization
- [ ] Implementation planning

**وابستگی‌ها:** Phase 14  
**تخمین زمان:** Ongoing  
**اولویت:** 🟡 متوسط

---

### 15.3 Optimization & Scaling

- [ ] Performance analysis
- [ ] Bottleneck identification
- [ ] Optimization implementation
- [ ] Scaling planning:
  - Horizontal scaling
  - Resource upgrades
- [ ] Load testing

**وابستگی‌ها:** 15.1  
**تخمین زمان:** As needed  
**اولویت:** 🟡 متوسط

---

## Future Enhancements (Phase 4 از ARCHITECTURE.md)

### Advanced Features (Optional, Month 6+)

- [ ] Query templates:
  - Pre-defined queries
  - Template management UI
- [ ] Scheduled queries:
  - Cron-like scheduling
  - Recurring queries
- [ ] Data export features:
  - Export results to CSV/Excel
  - Bulk export
- [ ] Advanced analytics:
  - Usage analytics
  - Query performance analytics
  - User behavior analytics
- [ ] Multi-tenancy support:
  - Tenant isolation
  - Tenant-specific configurations
- [ ] Kubernetes deployment:
  - Helm charts
  - Auto-scaling
  - High availability
- [ ] Webhook support:
  - Notify on completion
  - Custom webhooks

**وابستگی‌ها:** Phase 14  
**تخمین زمان:** TBD  
**اولویت:** 🟢 پایین (Future)

---

## 📊 خلاصه تخمین زمان به فاز

| فاز | توضیحات | تخمین زمان |
|-----|---------|-------------|
| Phase 1 | راه‌اندازی اولیه | 10 ساعت |
| Phase 2 | Database & Models | 24 ساعت |
| Phase 3 | Shared Components | 14 ساعت |
| Phase 4 | Request Network API | 37 ساعت |
| Phase 5 | Request Network Workers | 28 ساعت |
| Phase 6 | Response Network Workers | 38 ساعت |
| Phase 7 | Response Network Monitoring API | 4 ساعت |
| Phase 8 | Admin Panel (Response Network) | 42 ساعت |
| Phase 10 | Testing | 40 ساعت |
| Phase 11 | Documentation | 20 ساعت |
| Phase 12 | Production Prep | 45 ساعت |
| Phase 13 | Staging Testing | 22 ساعت |
| Phase 14 | Production Deploy | 17 ساعت |
| Phase 15 | Post-Launch | Ongoing |
| **کل** | | **~363 ساعت** |

**تخمین با 2 developer:** حدود **8-9 هفته** (full-time)  
**تخمین با 1 developer:** حدود **12-13 هفته** (full-time)

---

## 🎯 اولویت‌بندی

### 🔴 بالا (Critical Path)
- Phase 1, 2, 3, 4, 5, 6: Backend core
- Phase 10.1, 10.4: Testing اصلی
- Phase 12: Production prep
- Phase 13, 14: Deployment

### 🟡 متوسط (Important)
- Phase 8: Admin panel
- Phase 11: Documentation
- Monitoring & logging features

### 🟢 پایین (Nice to have)
- Advanced admin features
- Optional monitoring (Prometheus/Grafana)
- Future enhancements

---

## ✅ نکات مهم

1. **شروع با MVP:**
   - Focus روی core functionality
   - Admin panels ساده در ابتدا
   - Optional features را بعداً

2. **Testing از اول:**
   - Unit tests همراه با development
   - Integration tests پس از هر phase
   - CI/CD از ابتدا (optional ولی توصیه می‌شود)

3. **Security First:**
   - Authentication/Authorization محکم
   - Regular security reviews

4. **Documentation همزمان:**
   - Code comments همزمان با coding
   - API docs همزمان با endpoints
   - User docs پیش از deployment

5. **Monitoring Early:**
   - Logging از اول
   - Health checks در هر service
   - Metrics از ابتدا

6. **Incremental Deployment:**
   - Staging environment اول
   - Beta testing با limited users
   - Gradual production rollout

---

**تاریخ ایجاد:** 2025-01-15  
**آخرین به‌روزرسانی:** 2025-01-15  
**وضعیت:** Ready for Development

---

## 📝 یادداشت‌ها

- این TODO list یک roadmap کامل است ولی flexible
- تخمین‌های زمانی تقریبی هستند
- اولویت‌ها بر اساس نیاز قابل تغییر هستند
- برای هر task می‌توانید subtask های جزئی‌تر ایجاد کنید
- به‌روزرسانی این فایل را فراموش نکنید!
