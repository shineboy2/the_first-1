# راهنمای پیاده‌سازی شبکه پاسخ (Response Network)

## پیش‌نیازها

| نیازمندی | حداقل | پیشنهادی |
|----------|-------|----------|
| CPU | 4 Core | 8 Core |
| RAM | 8 GB | 16 GB |
| Disk | 100 GB | 500 GB |
| Docker | 24.0+ | آخرین نسخه |
| Docker Compose | 2.20+ | آخرین نسخه |

> **توجه**: Elasticsearch حافظه بیشتری نیاز دارد

## ساختار دایرکتوری

```
response-network/
├── api/                    # کد سورس API
├── admin-panel/            # کد سورس پنل ادمین
├── docker-compose.yml      # تنظیمات Docker
├── Dockerfile              # Build image API
├── .env                    # تنظیمات محیطی
└── .env.example            # الگوی تنظیمات
```

## گام‌های نصب

### گام 1: کپی فایل‌ها به سرور

```bash
# ایجاد دایرکتوری
mkdir -p /opt/response-network
cd /opt/response-network

# کپی فایل‌ها
# scp -r deploy/response-network/* user@server:/opt/response-network/

# کپی کدها
# scp -r response-network/api user@server:/opt/response-network/
# scp -r response-network/admin-panel user@server:/opt/response-network/
```

### گام 2: تنظیم Environment

```bash
cp .env.example .env
nano .env
```

**تنظیمات ضروری:**
```bash
# دیتابیس
DB_PASSWORD=YourSecurePassword123!

# Redis
REDIS_PASSWORD=YourRedisPassword456!

# Elasticsearch (حافظه)
ES_MEMORY=4g

# JWT
SECRET_KEY=YourSuperSecretKey32CharactersOrMore!

# Admin Panel (آدرس API قابل دسترس از مرورگر)
ADMIN_API_URL=http://YOUR_SERVER_IP:8000

# FTP
FTP_HOST=192.168.1.100
FTP_USER=response_user
FTP_PASSWORD=FtpPassword789!
```

### گام 3: اجرای سرویس‌ها

```bash
# Build و اجرا
docker compose up -d --build

# بررسی وضعیت
docker compose ps

# لاگ‌ها (Elasticsearch ممکن است چند دقیقه طول بکشد)
docker compose logs -f elasticsearch
```

### گام 4: Migration و Seed

```bash
# اجرای migrations
docker compose exec api alembic upgrade head

# ایجاد کاربر ادمین اولیه
docker compose exec api python create_admin.py
```

**اطلاعات ورود پیش‌فرض:**
- نام کاربری: `admin`
- رمز عبور: `admin123`

> ⚠️ **مهم**: فوراً رمز عبور را تغییر دهید!

### گام 5: تست سلامت

```bash
# API
curl http://localhost:8000/health/ready

# Elasticsearch
curl http://localhost:9200/_cluster/health

# Admin Panel (در مرورگر)
# http://YOUR_SERVER_IP:3000
```

## پورت‌ها

| سرویس | پورت | توضیح |
|-------|------|-------|
| API | 8000 | REST API |
| Admin Panel | 3000 | رابط کاربری وب |
| PostgreSQL | 5432 (داخلی) | دیتابیس |
| Redis | 6379 (داخلی) | Cache |
| Elasticsearch | 9200 (داخلی) | موتور جستجو |

## تنظیمات FTP

```
📥 Import (از FTP):
   FTP:/requests/*.jsonl → /imports/requests/

📤 Export (به FTP):
   /exports/users/*.jsonl → FTP:/users/
   /exports/settings/*.jsonl → FTP:/settings/
   /exports/results/*.jsonl → FTP:/results/
```

### ساختار FTP

```
/ftp-root/
├── requests/       # درخواست‌ها (Request → Response)
├── results/        # نتایج (Response → Request)
├── users/          # کاربران (Response → Request)
└── settings/       # تنظیمات (Response → Request)
```

## پنل ادمین

پس از راه‌اندازی، پنل ادمین در آدرس زیر در دسترس است:

```
http://YOUR_SERVER_IP:3000
```

### امکانات پنل ادمین:
- مدیریت کاربران
- تعریف انواع پروفایل
- تعریف انواع درخواست  
- مانیتورینگ درخواست‌ها
- مدیریت Workers و Tasks
- تنظیمات Export
- مدیریت Cache

## بارگذاری داده در Elasticsearch

```bash
# اجرای اسکریپت setup
docker compose exec api python setup_elasticsearch.py
```

## عیب‌یابی

### Elasticsearch Start نمی‌شود

```bash
# بررسی لاگ
docker compose logs elasticsearch

# بررسی حافظه
free -h

# افزایش vm.max_map_count (در host)
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

### Admin Panel Load نمی‌شود

```bash
# بررسی ADMIN_API_URL در .env
# باید آدرس قابل دسترس از مرورگر باشد

# اگر پشت Firewall هستید، پورت 8000 را باز کنید
```

### مشکل اتصال بین سرویس‌ها

```bash
# Restart همه سرویس‌ها
docker compose down
docker compose up -d
```

## Backup

```bash
# دیتابیس
docker compose exec postgres pg_dump -U response_user response_db > backup.sql

# Elasticsearch
curl -X PUT "localhost:9200/_snapshot/my_backup" -H 'Content-Type: application/json' -d'{"type": "fs", "settings": {"location": "/backup"}}'
```

## Security

### تغییر رمز ادمین

1. وارد پنل ادمین شوید
2. به Settings → Account بروید
3. رمز عبور جدید تنظیم کنید

### Firewall

```bash
# فقط پورت‌های ضروری را باز کنید
sudo ufw allow 8000/tcp  # API
sudo ufw allow 3000/tcp  # Admin Panel
sudo ufw enable
```

## به‌روزرسانی

```bash
git pull
docker compose up -d --build
docker compose exec api alembic upgrade head
```
