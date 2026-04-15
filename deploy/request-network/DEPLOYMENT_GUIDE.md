# راهنمای پیاده‌سازی شبکه درخواست (Request Network)

## پیش‌نیازها

| نیازمندی | حداقل | پیشنهادی |
|----------|-------|----------|
| CPU | 2 Core | 4 Core |
| RAM | 4 GB | 8 GB |
| Disk | 50 GB | 100 GB |
| Docker | 24.0+ | آخرین نسخه |
| Docker Compose | 2.20+ | آخرین نسخه |

## ساختار دایرکتوری

```
request-network/
├── api/                    # کد سورس API (کپی می‌شود)
├── docker-compose.yml      # تنظیمات Docker
├── Dockerfile              # Build image
├── .env                    # تنظیمات محیطی (از .env.example ساخته می‌شود)
└── .env.example            # الگوی تنظیمات
```

## گام‌های نصب

### گام 1: کپی فایل‌ها به سرور

```bash
# ایجاد دایرکتوری
mkdir -p /opt/request-network
cd /opt/request-network

# کپی فایل‌ها (از سیستم شما به سرور)
# scp -r deploy/request-network/* user@server:/opt/request-network/

# کپی کد API
# scp -r request-network/api user@server:/opt/request-network/
```

### گام 2: تنظیم Environment

```bash
# کپی الگوی تنظیمات
cp .env.example .env

# ویرایش تنظیمات
nano .env
```

**تنظیمات ضروری:**
```bash
# رمز عبور دیتابیس (امن و تصادفی)
DB_PASSWORD=YourSecurePassword123!

# رمز Redis (امن)
REDIS_PASSWORD=YourRedisPassword456!

# کلید امنیتی JWT (حداقل 32 کاراکتر)
SECRET_KEY=YourSuperSecretKey32CharactersOrMore!

# تنظیمات FTP
FTP_HOST=192.168.1.100      # آدرس سرور FTP واسط
FTP_PORT=21
FTP_USER=request_user
FTP_PASSWORD=FtpPassword789!
```

### گام 3: اجرای سرویس‌ها

```bash
# Build و اجرا
docker compose up -d --build

# بررسی وضعیت
docker compose ps
docker compose logs -f
```

### گام 4: اجرای Migrations

```bash
# اجرای migration دیتابیس
docker compose exec api alembic upgrade head
```

### گام 5: تست سلامت سیستم

```bash
# بررسی API
curl http://localhost:8001/health/ready

# بررسی لاگ‌ها
docker compose logs api --tail 50
docker compose logs celery-worker --tail 50
```

## پورت‌ها

| سرویس | پورت | توضیح |
|-------|------|-------|
| API | 8001 | REST API |
| PostgreSQL | 5432 (داخلی) | دیتابیس |
| Redis | 6379 (داخلی) | Cache & Queue |

## تنظیمات FTP

شبکه درخواست با سرور FTP به این صورت کار می‌کند:

```
📤 Export (به FTP):
   /exports/requests/*.jsonl → FTP:/requests/

📥 Import (از FTP):
   FTP:/users/*.jsonl → /imports/users/
   FTP:/settings/*.jsonl → /imports/settings/
   FTP:/results/*.jsonl → /imports/results/
```

### ساختار مسیرهای FTP

روی سرور FTP این دایرکتوری‌ها باید وجود داشته باشد:

```
/ftp-root/
├── requests/       # درخواست‌ها (Request → Response)
├── results/        # نتایج (Response → Request)
├── users/          # کاربران (Response → Request)
└── settings/       # تنظیمات (Response → Request)
```

## عیب‌یابی

### مشکل: Container ها Start نمی‌شوند

```bash
# بررسی لاگ‌ها
docker compose logs

# بررسی وضعیت
docker compose ps

# Restart
docker compose restart
```

### مشکل: اتصال به دیتابیس

```bash
# تست اتصال
docker compose exec postgres pg_isready -U request_user -d request_db
```

### مشکل: اتصال FTP

```bash
# تست اتصال FTP از داخل container
docker compose exec api python -c "
import ftplib
ftp = ftplib.FTP('FTP_HOST')
ftp.login('USER', 'PASS')
print(ftp.nlst())
ftp.quit()
"
```

## Backup

```bash
# Backup دیتابیس
docker compose exec postgres pg_dump -U request_user request_db > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20241230.sql | docker compose exec -T postgres psql -U request_user request_db
```

## به‌روزرسانی

```bash
# Pull تغییرات جدید
git pull

# Rebuild و Restart
docker compose up -d --build

# اجرای migrations جدید
docker compose exec api alembic upgrade head
```

## تماس با پشتیبانی

در صورت بروز مشکل:
1. لاگ‌ها را ذخیره کنید: `docker compose logs > logs.txt`
2. فایل `.env` را بررسی کنید (بدون رمز عبور)
3. با تیم توسعه تماس بگیرید
