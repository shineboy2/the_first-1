# راهنمای Deploy به پروداکشن

## 📋 خلاصه اصلاحات

### 1. Elasticsearch SSL ✅
- **فایل**: `/response-network/api/workers/tasks/execute_query.py`
- **تغییر**: اصلاح منطق SSL context برای HTTPS URLs
- **نتیجه**: SSL verification اکنون به درستی غیرفعال می‌شود

### 2. فرانت‌اند IP قدیمی ✅
- **فایل‌های تغییر یافته**:
  - `/response-network/admin-panel/next.config.ts`
  - `/request-network/admin-panel/next.config.ts`
  - `/response-network/admin-panel/app/(auth)/login/page.tsx`
  - `/request-network/admin-panel/app/(auth)/login/page.tsx`
- **تغییرات**:
  - حذف rewrite ثابت که API URL را build time پخته می‌کند
  - اضافه کردن Cache-Control headers برای `config.js`
  - جایگزینی `process.env.NEXT_PUBLIC_API_URL` با runtime config
- **نتیجه**: API URL اکنون از runtime config خوانده می‌شود

### 3. پاکسازی پروژه ✅
- **اقدامات**:
  - انتقال مستندات قدیمی به `archive/docs/`
  - انتقال اسکریپت‌های قدیمی به `archive/scripts/`
  - انتقال لاگ‌ها به `archive/logs/`
  - انتقال Dockerfiles اضافی به `archive/docker/`
  - حذف فایل‌های موقت و cache
  - ایجاد `docs/` برای مستندات فعال
  - ایجاد `README.md` جامع

---

## 🚀 مراحل Deploy

### مرحله 1: Build روی سرور دولوپ

```bash
# رفتن به پوشه پروژه
cd /home/docker/the_first/the_first

# Build response-network
cd response-network
docker-compose build

# خروجی گرفتن از image
docker save response-network:latest | gzip > /tmp/response-network.tar.gz

# Build request-network
cd ../request-network
docker-compose build

# خروجی گرفتن از image
docker save request-network:latest | gzip > /tmp/request-network.tar.gz

# بررسی فایل‌های ایجاد شده
ls -lh /tmp/*.tar.gz
```

### مرحله 2: انتقال به سرور پروداکشن

```bash
# از سرور دولوپ
scp /tmp/response-network.tar.gz user@production-server:/tmp/
scp /tmp/request-network.tar.gz user@production-server:/tmp/

# یا استفاده از rsync برای سرعت بیشتر
rsync -avz /tmp/*.tar.gz user@production-server:/tmp/
```

### مرحله 3: Load و اجرا روی سرور پروداکشن

```bash
# روی سرور پروداکشن
cd /path/to/production/the_first

# Load response-network image
docker load < /tmp/response-network.tar.gz

# Load request-network image
docker load < /tmp/request-network.tar.gz

# بررسی images
docker images | grep -E "response-network|request-network"

# Restart سرویس‌ها
cd response-network
docker-compose down
docker-compose up -d

cd ../request-network
docker-compose down
docker-compose up -d

# بررسی وضعیت
docker-compose ps
```

### مرحله 4: تأیید Deploy

```bash
# بررسی لاگ‌ها
docker logs response-api --tail 50
docker logs response-celery-worker --tail 50
docker logs response-admin-panel --tail 50

# تست API
curl -X GET http://localhost:8000/api/v1/health

# تست فرانت‌اند
# باز کردن مرورگر و رفتن به http://production-ip:3000
# بررسی Network tab برای مشاهده API URL صحیح

# بررسی Elasticsearch
docker logs response-celery-worker | grep ELASTICSEARCH
# باید پیام زیر را ببینید:
# [ELASTICSEARCH] SSL verification disabled for https://...
```

---

## 🔍 نکات مهم

### فرانت‌اند
- API URL اکنون از `config.js` خوانده می‌شود (runtime)
- `config.js` در هر بار load صفحه دوباره تولید می‌شود
- Cache-Control headers تضمین می‌کند که `config.js` cache نمی‌شود
- بدون نیاز به Ctrl+F5 برای reload

### Elasticsearch
- SSL verification برای HTTPS URLs غیرفعال است
- تنظیمات از دیتابیس خوانده می‌شود
- اگر config در دیتابیس نباشد، SSL به صورت پیش‌فرض غیرفعال است

### پاکسازی
- تمام فایل‌های قدیمی در `archive/` نگه داشته شده‌اند
- می‌توانید در صورت نیاز به آن‌ها مراجعه کنید
- پروژه اکنون تمیز‌تر و قابل نگهداری‌تر است

---

## 🐛 عیب‌یابی

### مشکل: فرانت‌اند به IP قدیمی متصل می‌شود
```bash
# بررسی config.js در کانتینر
docker exec response-admin-panel cat /app/public/config.js

# باید نشان دهد:
# window.__RUNTIME_CONFIG__ = {
#   API_URL: 'http://10.1.0.206:8000' || 'http://localhost:8000'
# };

# اگر IP قدیمی است، restart کنید:
docker-compose restart admin-panel
```

### مشکل: Elasticsearch SSL error
```bash
# بررسی لاگ worker
docker logs response-celery-worker | grep -A 5 ELASTICSEARCH

# باید پیام زیر را ببینید:
# [ELASTICSEARCH] SSL verification disabled for https://...

# اگر خطا می‌دهد، بررسی کنید:
# 1. آیا config در دیتابیس است؟
# 2. آیا verify_ssl=false است؟
# 3. آیا URL صحیح است؟
```

### مشکل: API timeout
```bash
# بررسی اتصال API
curl -X GET http://localhost:8000/api/v1/health

# بررسی لاگ API
docker logs response-api --tail 100

# بررسی شبکه
docker network ls
docker network inspect response-net
```

---

## 📝 Checklist نهایی

- [ ] Build روی سرور دولوپ موفق بود
- [ ] فایل‌های tar.gz ایجاد شدند
- [ ] انتقال به سرور پروداکشن موفق بود
- [ ] Load images روی پروداکشن موفق بود
- [ ] docker-compose up -d موفق بود
- [ ] API health check موفق بود
- [ ] فرانت‌اند با IP صحیح متصل می‌شود
- [ ] Elasticsearch SSL verification غیرفعال است
- [ ] تمام سرویس‌ها در حالت running هستند

---

**تاریخ**: 2026-05-23  
**نسخه**: 1.0
