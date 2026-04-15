# راهنمای جامع استقرار سیستم ایزوله درخواست/پاسخ

## نمای کلی معماری

این سیستم از سه بخش تشکیل شده:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         معماری Air-Gapped                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────────┐   │
│  │   Request   │       │     FTP     │       │    Response     │   │
│  │   Network   │◄─────►│   Server    │◄─────►│    Network      │   │
│  │  (Host 1)   │       │  (واسط)     │       │   (Host 2)      │   │
│  └─────────────┘       └─────────────┘       └─────────────────┘   │
│        │                                            │               │
│        │                                            │               │
│   کاربران نهایی                              Elasticsearch         │
│   ثبت درخواست                               پردازش کوئری          │
│                                               پنل ادمین            │
└─────────────────────────────────────────────────────────────────────┘
```

## ترتیب نصب

1. **ابتدا**: سرور FTP واسط را راه‌اندازی کنید
2. **سپس**: Response Network را نصب کنید
3. **در آخر**: Request Network را نصب کنید

## چک‌لیست پیش از نصب

### سخت‌افزار

| سرور | CPU | RAM | Disk |
|------|-----|-----|------|
| Request Network | 4 Core | 8 GB | 100 GB |
| Response Network | 8 Core | 16 GB | 500 GB |
| FTP Server | 2 Core | 4 GB | 200 GB |

### شبکه

- [ ] آدرس IP ثابت برای هر سرور
- [ ] اتصال شبکه بین سرورها
- [ ] پورت‌های مورد نیاز باز شده

### نرم‌افزار

- [ ] سیستم‌عامل: Ubuntu 22.04 LTS (پیشنهادی)
- [ ] Docker نصب شده
- [ ] Docker Compose نصب شده

## محتویات پکیج

```
deploy/
├── request-network/
│   ├── docker-compose.yml      # تنظیمات Docker
│   ├── Dockerfile              # Build image
│   ├── .env.example            # الگوی تنظیمات
│   └── DEPLOYMENT_GUIDE.md     # راهنمای نصب
│
├── response-network/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── .env.example
│   └── DEPLOYMENT_GUIDE.md
│
├── FTP_SETUP_GUIDE.md          # راهنمای FTP
└── README.md                   # این فایل
```

## گام‌های نصب سریع

### 1. FTP Server

```bash
# روی سرور FTP
sudo apt install vsftpd -y
# تنظیم طبق FTP_SETUP_GUIDE.md
```

### 2. Response Network

```bash
# کپی فایل‌ها به سرور Response
scp -r deploy/response-network/* user@response-server:/opt/response-network/
scp -r response-network/api user@response-server:/opt/response-network/
scp -r response-network/admin-panel user@response-server:/opt/response-network/

# SSH به سرور
ssh user@response-server

# راه‌اندازی
cd /opt/response-network
cp .env.example .env
nano .env  # تنظیم مقادیر
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python create_admin.py
```

### 3. Request Network

```bash
# کپی فایل‌ها به سرور Request
scp -r deploy/request-network/* user@request-server:/opt/request-network/
scp -r request-network/api user@request-server:/opt/request-network/

# SSH به سرور
ssh user@request-server

# راه‌اندازی
cd /opt/request-network
cp .env.example .env
nano .env  # تنظیم مقادیر
docker compose up -d --build
docker compose exec api alembic upgrade head
```

## تست سیستم

### 1. تست FTP

```bash
# از هر سرور
ftp FTP_SERVER_IP
```

### 2. تست API ها

```bash
# Request Network
curl http://REQUEST_SERVER:8001/health/ready

# Response Network
curl http://RESPONSE_SERVER:8000/health/ready
```

### 3. تست پنل ادمین

در مرورگر باز کنید:
```
http://RESPONSE_SERVER:3000
```

### 4. تست سناریوی کامل

1. در پنل ادمین یک کاربر ایجاد کنید
2. چند دقیقه صبر کنید تا Sync انجام شود
3. بررسی لاگ Worker ها

```bash
# لاگ Response Worker
docker compose logs celery-worker --tail 50

# لاگ Request Worker
docker compose logs celery-worker --tail 50
```

## پورت‌های مورد نیاز

| سرور | پورت | سرویس |
|------|------|-------|
| FTP | 20, 21, 10000-10100 | FTP |
| Response | 8000 | API |
| Response | 3000 | Admin Panel |
| Request | 8001 | API |

## مستندات تکمیلی

- [راهنمای Request Network](./request-network/DEPLOYMENT_GUIDE.md)
- [راهنمای Response Network](./response-network/DEPLOYMENT_GUIDE.md)
- [راهنمای FTP](./FTP_SETUP_GUIDE.md)

## پشتیبانی

در صورت بروز مشکل:

1. لاگ‌های Docker را ذخیره کنید
2. وضعیت Container ها را بررسی کنید
3. فایل‌های .env را چک کنید
4. با تیم توسعه تماس بگیرید
