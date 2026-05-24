# پروژه شبکه درخواست و پاسخ‌دهی

یک سیستم توزیع‌شده برای مدیریت درخواست‌ها و پاسخ‌دهی با استفاده از Elasticsearch، PostgreSQL، Redis و Celery.

## 📋 ساختار پروژه

```
the_first/
├── request-network/          # شبکه درخواست
│   ├── admin-panel/          # فرانت‌اند (Next.js)
│   ├── api/                  # بکند (FastAPI)
│   ├── docker-compose.yml
│   └── Dockerfile
├── response-network/         # شبکه پاسخ‌دهی
│   ├── admin-panel/          # فرانت‌اند (Next.js)
│   ├── api/                  # بکند (FastAPI)
│   ├── docker-compose.yml
│   └── Dockerfile
├── deploy/                   # فایل‌های deployment
├── docs/                     # مستندات
├── scripts/                  # اسکریپت‌های فعال
├── tests/                    # تست‌های یکپارچه
├── archive/                  # فایل‌های قدیمی (برای مرجع)
└── CRITICAL_FIXES_TODO.md    # لیست اصلاحات
```

## 🚀 شروع سریع

### پیش‌نیازها
- Docker و Docker Compose
- Python 3.10+
- Node.js 20+

### راه‌اندازی محلی

```bash
# شبکه درخواست
cd request-network
docker-compose up -d

# شبکه پاسخ‌دهی
cd ../response-network
docker-compose up -d
```

### دسترسی به پنل‌های مدیریت

- **Request Network Admin**: http://localhost:3001
- **Response Network Admin**: http://localhost:3000
- **API Request Network**: http://localhost:8001
- **API Response Network**: http://localhost:8000

## 📚 مستندات

- [معماری سیستم](docs/ARCHITECTURE.md)
- [وظایف تکمیل‌شده](docs/COMPLETED_TASKS.md)
- [اصلاحات حیاتی](CRITICAL_FIXES_TODO.md)

## 🔧 اصلاحات اخیر

### مشکل 1: Elasticsearch SSL ✅
- اصلاح کد `execute_query.py` برای handle کردن HTTPS URLs
- SSL verification اکنون به درستی غیرفعال می‌شود

### مشکل 2: فرانت‌اند IP قدیمی ✅
- حذف rewrite ثابت از `next.config.ts`
- استفاده از runtime config.js برای API URL
- اضافه کردن Cache-Control headers

### مشکل 3: پاکسازی پروژه ✅
- انتقال مستندات قدیمی به `archive/docs/`
- انتقال اسکریپت‌های قدیمی به `archive/scripts/`
- حذف فایل‌های موقت و cache

## 📝 نکات مهم

### Deploy به پروداکشن

1. **Build روی سرور دولوپ** (چون سرور پروداکشن اینترنت ندارد):
   ```bash
   docker-compose build
   docker save response-network:latest | gzip > response-network.tar.gz
   docker save request-network:latest | gzip > request-network.tar.gz
   ```

2. **انتقال به سرور پروداکشن**:
   ```bash
   scp response-network.tar.gz user@production:/tmp/
   scp request-network.tar.gz user@production:/tmp/
   ```

3. **Load و اجرا روی پروداکشن**:
   ```bash
   docker load < response-network.tar.gz
   docker load < request-network.tar.gz
   docker-compose up -d
   ```

### تنظیمات Elasticsearch

- URL: `https://10.1.0.23:9200`
- Username: `3136`
- SSL Verification: `false`
- تنظیمات از دیتابیس خوانده می‌شود

### تنظیمات فرانت‌اند

- API URL از `config.js` خوانده می‌شود (runtime)
- Cache-Control headers برای `config.js` تنظیم شده
- بدون rewrite ثابت در `next.config.ts`

## 🐛 عیب‌یابی

### مشکل: فرانت‌اند به IP قدیمی متصل می‌شود
- بررسی کنید که `config.js` در مرورگر صحیح است
- پاک کردن cache مرورگر (Ctrl+Shift+Delete)
- بررسی Network tab برای مشاهده API URL

### مشکل: Elasticsearch SSL error
- بررسی لاگ worker: `docker logs response-celery-worker | grep ELASTICSEARCH`
- اطمینان از اینکه `verify_ssl=false` در دیتابیس تنظیم شده

## 📞 تماس و پشتیبانی

برای سوالات و مشکلات، لطفاً به مستندات در `docs/` مراجعه کنید.

---

**آخرین به‌روزرسانی**: 2026-05-23  
**نسخه**: 1.0
