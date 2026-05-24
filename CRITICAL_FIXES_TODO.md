# لیست اصلاحات حیاتی پروژه

تاریخ ایجاد: 2026-05-23
تاریخ به‌روزرسانی: 2026-05-23
نسخه: 3.0 (تحلیل نهایی)

---

## 🔴 مشکل 1: فرانت‌اند با IP قدیمی (192.168.214.141) به بکند متصل می‌شود

### تشخیص نهایی:

**✅ بررسی‌های انجام شده:**
1. فایل `config.js` در کانتینر صحیح است: `API_URL: 'http://10.1.0.206:8000'`
2. فایل `config.js` در مرورگر هم صحیح است
3. فایل `.env.local` در build time توسط `.dockerignore` ignore می‌شود ✅
4. کد `app/(auth)/api.ts` به درستی از runtime config استفاده می‌کند ✅

**❌ مشکل اصلی پیدا شد:**

#### مشکل 1: `next.config.ts` (خط 19-22)
```typescript
async rewrites() {
  return {
    beforeFiles: [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/:path*`,
      },
    ],
  };
},
```

**توضیح:** این rewrite rule در **build time** ارزیابی می‌شود و مقدار `NEXT_PUBLIC_API_URL` در bundle پخته می‌شود. حتی اگر runtime config تغییر کند، این rewrite همچنان IP قدیمی را دارد.

#### مشکل 2: `app/(auth)/login/page.tsx` (خط 60)
```typescript
console.log("Sending login request with:", {
  url: `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login`,
  data: formData.toString(),
});
```

این فقط console.log است، اما نشان می‌دهد که کد ممکن است جای دیگری هم از build-time env استفاده کند.

### راه‌حل نهایی (Best Practice):

**انتخاب: استفاده از Runtime Config با Rewrite داینامیک**

#### گام 1: اصلاح `next.config.ts`

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // ❌ حذف rewrite ثابت که IP را پخته می‌کند
  // async rewrites() {
  //   return {
  //     beforeFiles: [
  //       {
  //         source: "/api/:path*",
  //         destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
  //       },
  //     ],
  //   };
  // },
  
  // ✅ اضافه کردن headers برای config.js
  async headers() {
    return [
      {
        source: '/config.js',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
```

#### گام 2: اطمینان از عدم استفاده از `process.env.NEXT_PUBLIC_API_URL` در کد

جستجو در کل پروژه و جایگزینی با `getApiUrl()` یا `(window as any).__RUNTIME_CONFIG__?.API_URL`

#### گام 3: Rebuild و Deploy

```bash
# روی سرور دولوپ
cd /home/docker/the_first/the_first/response-network
docker-compose build admin-panel

# خروجی گرفتن از image
docker save response-network-admin-panel:latest | gzip > /tmp/admin-panel.tar.gz

# انتقال به سرور پروداکشن و load
docker load < /tmp/admin-panel.tar.gz

# restart سرویس
docker-compose restart admin-panel
```

### فایل‌های نیازمند تغییر:
- `/response-network/admin-panel/next.config.ts`
- `/request-network/admin-panel/next.config.ts` (اگر مشابه است)

---

### تشخیص مشکل:
✅ **بررسی شد:**
- فایل `config.js` در کانتینر صحیح است: `API_URL: 'http://10.1.0.206:8000'`
- فایل `config.js` در مرورگر هم صحیح است و از cache لود می‌شود
- کد TypeScript در `app/(auth)/api.ts` به درستی از `window.__RUNTIME_CONFIG__.API_URL` استفاده می‌کند

❌ **مشکل واقعی:**
- در خطای مرورگر می‌بینیم: `url: "http://192.168.214.141:8000/api/v1/auth/login"`
- یعنی **IP قدیمی سرور دولوپ (192.168.214.141) در bundle Next.js پخته شده است!**
- این اتفاق در build time رخ می‌دهد نه runtime

### علت اصلی:
وقتی image را روی سرور دولوپ build می‌کنید:
1. Next.js در build time مقدار `NEXT_PUBLIC_API_URL` را می‌خواند
2. این مقدار در JavaScript bundles پخته می‌شود (hardcoded)
3. وقتی image را به پروداکشن می‌برید، این IP قدیمی در bundle باقی می‌ماند
4. حتی اگر `config.js` را runtime تغییر دهید، کدهای bundle شده همچنان IP قدیمی را دارند

### راه‌حل:

**گزینه 1: Build بدون NEXT_PUBLIC_API_URL (توصیه می‌شود)**

در `Dockerfile` فرانت‌اند، مطمئن شوید که در build time هیچ `NEXT_PUBLIC_API_URL` تنظیم نشده:

```dockerfile
# Build stage
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# ❌ حذف این خط (اگر وجود دارد):
# ARG NEXT_PUBLIC_API_URL
# ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# ✅ Build بدون environment variable
RUN npm run build

# Runtime stage
FROM node:20-slim
WORKDIR /app
# ... بقیه کد
```

**گزینه 2: استفاده از placeholder در build time**

```dockerfile
# Build با placeholder
ARG NEXT_PUBLIC_API_URL=__PLACEHOLDER__
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN npm run build
```

سپس در runtime با `sed` یا `envsubst` جایگزین کنید.

**گزینه 3: Build روی سرور پروداکشن (اگر امکان دارد)**

اگر سرور پروداکشن به اینترنت دسترسی موقت داشته باشد، image را روی خود سرور build کنید.

### فایل‌های نیازمند بررسی:
- `/response-network/admin-panel/Dockerfile`
- `/response-network/admin-panel/.env` یا `.env.production`
- `/request-network/admin-panel/Dockerfile`
- `/request-network/admin-panel/.env` یا `.env.production`

### اقدامات:
1. بررسی Dockerfile و حذف `ARG NEXT_PUBLIC_API_URL` از build stage
2. اطمینان از اینکه در build time هیچ `.env` با IP قدیمی لود نمی‌شود
3. Rebuild کردن image روی سرور دولوپ
4. انتقال به پروداکشن و تست

---

## 🔴 مشکل 2: خطای SSL در ارتباط با Elasticsearch

### تشخیص نهایی:

**✅ بررسی‌های انجام شده:**
1. Worker **دارد** config را از دیتابیس می‌خواند: `[ELASTICSEARCH] Loaded config from database: https://10.1.0.23:9200 (user: 3136)`
2. تنظیمات در دیتابیس: `url: "https://10.1.0.23:9200"`, `verify_ssl: false`, `is_active: true`
3. تست اتصال از API (uvicorn) موفق است ✅
4. اما worker خطا می‌دهد: `SSL: CERTIFICATE_VERIFY_FAILED` ❌

**✅ کد اصلاح شد:**

فایل `/response-network/api/workers/tasks/execute_query.py` خطوط 220-232 اصلاح شد.

### اقدامات لازم برای Deploy:

```bash
# روی سرور دولوپ
cd /home/docker/the_first/the_first/response-network
docker-compose build celery-worker

# خروجی گرفتن از image
docker save response-network:latest | gzip > /tmp/response-worker.tar.gz

# انتقال به سرور پروداکشن
scp /tmp/response-worker.tar.gz user@production-server:/tmp/

# روی سرور پروداکشن
docker load < /tmp/response-worker.tar.gz
docker-compose restart celery-worker
```

### تست نهایی:
```bash
# بررسی لاگ worker
docker logs response-celery-worker --tail 50 | grep ELASTICSEARCH

# باید پیام زیر را ببینید:
# [ELASTICSEARCH] SSL verification disabled for https://10.1.0.23:9200/...
```

---

---

## 🔴 مشکل 3: ساختار پروژه نامرتب و فایل‌های اضافی

### استراتژی پاکسازی:

به جای حذف، فایل‌ها را به پوشه‌های مناسب منتقل می‌کنیم:

```
the_first/
├── archive/              # فایل‌های قدیمی و مستندات تاریخی
│   ├── docs/            # مستندات قدیمی
│   ├── scripts/         # اسکریپت‌های قدیمی
│   └── logs/            # لاگ‌های قدیمی
├── docs/                 # مستندات فعال
│   ├── ARCHITECTURE.md
│   └── README.md
├── scripts/              # فقط اسکریپت‌های فعال (deploy)
├── request-network/
├── response-network/
└── tests/
```

### فایل‌های قابل انتقال به archive/:

#### 1. مستندات قدیمی → archive/docs/
```
DEPLOYMENT_ELASTICSEARCH_SSL_FIX.md
DEPLOYMENT_FIXES_TODO.md
ELASTICSEARCH_ACCESS.md
EXTERNAL_API_ACCESS_FIX.md
EXTERNAL_API_ACCESS_REFACTOR.md
EXTERNAL_API_ACCESS_TODO.md
EXTERNAL_API_COMPLETE.md
EXTERNAL_API_DESIGN_ANALYSIS.md
EXTERNAL_API_FINAL_SUMMARY.md
EXTERNAL_API_IMPLEMENTATION_COMPLETE.md
EXTERNAL_API_TODO_CRITICAL.md
EXTERNAL_API_USER_ACCESS_COMPLETE.md
EXTERNAL_API_USER_ACCESS_TODO.md
FINAL_SUMMARY.md
INTEGRATION_CHANGES.md
NETWORK_SEPARATION_EXECUTION_CHECKLIST.md
NETWORK_SEPARATION_PLAN.md
OVF_EXPORT_CHECKLIST.md
PRODUCTION_DEPLOYMENT_GUIDE.md
PRODUCTION_IMPORT_GUIDE.md
RUNTIME_CONFIG_EXAMPLE.md
SAMPLE_REQUESTS.md
SEPARATION_SUMMARY.md
SESSION_COMPLETION_REPORT.txt
SIMPLE_VM_GUIDE.md
TODO_EXECUTION_PLAN.md
TODO.md
```

#### 2. لاگ‌ها → archive/logs/
```
deploy_fix.log
deploy_request.log
deploy_response.log
deploy.log
loop_output.log
```

#### 3. اسکریپت‌های قدیمی/تستی → archive/scripts/
```
change_ip.sh
check_config.py
cleanup_error_results.py
create_request_types.py
deploy-offline.sh
deploy_frontend.sh
deploy_production.sh
deploy.sh
fix_tables.py
local-env.sh
manage_db.py
prepare_vm_template.sh
reset_stuck_requests.py
run_end_to_end_test.py
seed_elasticsearch.py
separate_networks.sh
setup_env.sh
setup_production_data.py
setup_request_network.sh
test_ext_api.py
test_ftp_connection.py
test_ocr_request.sh
test_production.sh
test_separation.sh
update_request_types.py
validate_setup.sh
```

#### 4. فایل‌های قابل حذف (بعد از backup):
```
frontend_fix.tar
latest.json
sql_query.sql
```

#### 5. Dockerfiles و docker-compose اضافی → archive/docker/
```
Dockerfile (در root)
Dockerfile.beat
Dockerfile.request
Dockerfile.request-network
Dockerfile.response
Dockerfile.worker
docker-compose.dev.yml
docker-compose.elasticsearch.yml
docker-compose.request.yml
docker-compose.response.yml
docker-compose.yml (در root)
alembic.ini (در root)
conftest.py (در root)
entrypoint-request.sh (در root)
entrypoint.sh (در root)
```

#### 6. پوشه‌های قابل حذف/انتقال:
```
shared_old_backup/ → archive/backups/
dist/ → archive/releases/
__pycache__/ → حذف
.pytest_cache/ → حذف
```

### اسکریپت‌های فعال (نگه داشتن در scripts/):
```
scripts/
├── pack_release.sh
└── deploy/ (پوشه deploy فعلی)
```

### اقدامات:

#### گام 1: ایجاد ساختار archive
```bash
mkdir -p archive/{docs,scripts,logs,docker,backups,releases}
```

#### گام 2: انتقال مستندات قدیمی
```bash
mv DEPLOYMENT_*.md ELASTICSEARCH_*.md EXTERNAL_API_*.md \
   FINAL_SUMMARY.md INTEGRATION_CHANGES.md NETWORK_*.md \
   OVF_*.md PRODUCTION_*.md RUNTIME_*.md SAMPLE_*.md \
   SEPARATION_*.md SESSION_*.txt SIMPLE_*.md TODO*.md \
   archive/docs/
```

#### گام 3: انتقال لاگ‌ها
```bash
mv *.log archive/logs/
rm -f request-network/*.log request-network/celerybeat-schedule.*
```

#### گام 4: انتقال اسکریپت‌های قدیمی
```bash
mv change_ip.sh check_config.py cleanup_error_results.py \
   create_request_types.py deploy-offline.sh deploy_frontend.sh \
   deploy_production.sh deploy.sh fix_tables.py local-env.sh \
   manage_db.py prepare_vm_template.sh reset_stuck_requests.py \
   run_end_to_end_test.py seed_elasticsearch.py separate_networks.sh \
   setup_env.sh setup_production_data.py setup_request_network.sh \
   test_*.py test_*.sh update_request_types.py validate_setup.sh \
   archive/scripts/
```

#### گام 5: انتقال Dockerfiles اضافی
```bash
mv Dockerfile Dockerfile.* docker-compose.*.yml \
   alembic.ini conftest.py entrypoint*.sh \
   archive/docker/
```

#### گام 6: انتقال پوشه‌ها
```bash
mv shared_old_backup archive/backups/
mv dist archive/releases/
```

#### گام 7: حذف cache
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
```

#### گام 8: حذف فایل‌های موقت
```bash
rm -f frontend_fix.tar latest.json sql_query.sql
```

#### گام 9: ایجاد README.md در root
ایجاد یک README.md جامع که شامل:
- توضیح کلی پروژه (Request Network + Response Network)
- ساختار پروژه
- نحوه build و deploy
- لینک به مستندات در docs/

#### گام 10: انتقال ARCHITECTURE.md
```bash
mkdir -p docs
mv ARCHITECTURE.md docs/
mv COMPLETED_TASKS.md docs/
```

### ساختار نهایی:

```
the_first/
├── archive/                    # فایل‌های قدیمی (برای مرجع)
│   ├── backups/
│   ├── docs/
│   ├── docker/
│   ├── logs/
│   ├── releases/
│   └── scripts/
├── docs/                       # مستندات فعال
│   ├── ARCHITECTURE.md
│   ├── COMPLETED_TASKS.md
│   └── README.md
├── deploy/                     # فایل‌های deployment
│   ├── request-network/
│   ├── response-network/
│   └── README.md
├── request-network/            # شبکه درخواست
│   ├── admin-panel/
│   ├── api/
│   ├── .env
│   ├── docker-compose.yml
│   └── Dockerfile
├── response-network/           # شبکه پاسخ
│   ├── admin-panel/
│   ├── api/
│   ├── .env
│   ├── docker-compose.yml
│   └── Dockerfile
├── scripts/                    # اسکریپت‌های فعال
│   └── pack_release.sh
├── tests/                      # تست‌های یکپارچه
│   ├── test_grace_period.py
│   └── test_response_retrieval.py
├── .dockerignore
├── .env.example
├── .gitignore
├── CRITICAL_FIXES_TODO.md      # این فایل
├── README.md                   # مستندات اصلی
└── requirements.txt
```

### تست نهایی:
1. اطمینان از build شدن images
2. اطمینان از اجرای تست‌ها
3. بررسی عدم وابستگی به فایل‌های منتقل شده
4. اگر مشکلی پیش آمد، فایل‌ها در archive هستند

---

## 📋 چک‌لیست اجرا (به ترتیب اولویت)

### ✅ مرحله 1: اصلاح مشکل Elasticsearch SSL (بالاترین اولویت)
- [ ] اصلاح کد `execute_query.py` خطوط 220-232
- [ ] Restart کردن `celery-worker`: `docker-compose restart celery-worker`
- [ ] تست ارسال request و بررسی لاگ
- [ ] تأیید عدم وجود خطای SSL

**زمان تخمینی:** 10 دقیقه

---

### ✅ مرحله 2: اصلاح مشکل فرانت‌اند (اولویت بالا)
- [ ] بررسی `Dockerfile` فرانت‌اند response-network
- [ ] بررسی `Dockerfile` فرانت‌اند request-network
- [ ] حذف/تغییر `ARG NEXT_PUBLIC_API_URL` از build stage
- [ ] Rebuild کردن images روی سرور دولوپ
- [ ] انتقال به پروداکشن
- [ ] تست با F5 معمولی (بدون Ctrl+F5)
- [ ] بررسی Network tab برای تأیید IP صحیح

**زمان تخمینی:** 30-45 دقیقه (شامل build و deploy)

---

### ✅ مرحله 3: پاکسازی پروژه (اولویت متوسط)
- [ ] ایجاد پوشه `archive/` و زیرپوشه‌ها
- [ ] انتقال مستندات قدیمی به `archive/docs/`
- [ ] انتقال لاگ‌ها به `archive/logs/`
- [ ] انتقال اسکریپت‌های قدیمی به `archive/scripts/`
- [ ] انتقال Dockerfiles اضافی به `archive/docker/`
- [ ] انتقال پوشه‌های قدیمی
- [ ] حذف cache و فایل‌های موقت
- [ ] ایجاد پوشه `docs/` و انتقال مستندات فعال
- [ ] ایجاد `README.md` جامع در root
- [ ] تست build و اجرای پروژه

**زمان تخمینی:** 20-30 دقیقه

---

## ⚠️ نکات مهم

1. **مشکل Elasticsearch را اول حل کنید** - این مشکل فوری است و سیستم را مختل می‌کند
2. **قبل از هر تغییر، backup بگیرید** - به خصوص قبل از پاکسازی
3. **فایل‌ها را به archive منتقل کنید نه حذف** - برای مرجع آینده
4. **پس از هر مرحله، تست کامل انجام دهید**
5. **لاگ‌های celery-worker را به دقت بررسی کنید**

---

## � نکات تکنیکال

### مشکل Elasticsearch:
- علت: `ssl_context` برای HTTPS URLs به درستی تنظیم نمی‌شود
- راه‌حل: همیشه برای HTTPS یک `ssl_context` بسازید و بر اساس `verify_ssl` تنظیم کنید

### مشکل فرانت‌اند:
- علت: IP در build time در JavaScript bundles پخته می‌شود
- راه‌حل: Build بدون `NEXT_PUBLIC_API_URL` یا با placeholder

### پاکسازی:
- استراتژی: انتقال به archive به جای حذف
- هدف: ساختار تمیز و قابل نگهداری

---

**تاریخ به‌روزرسانی**: 2026-05-23  
**وضعیت**: آماده برای اجرا  
**نسخه**: 2.0 (اصلاح شده بر اساس بررسی دقیق کد)
