# چک‌لیست اجرای جداسازی شبکه‌ها

## مرحله 1: آماده‌سازی و بک‌آپ (5 دقیقه)

### 1.1 بک‌آپ گیری
- [ ] بک‌آپ کامل از پروژه: `cp -r . ../project-backup-$(date +%Y%m%d)`
- [ ] بررسی وضعیت git: `git status`
- [ ] commit تغییرات فعلی: `git add . && git commit -m "Pre-separation backup"`
- [ ] ایجاد branch جدید: `git checkout -b network-separation`

### 1.2 بررسی وابستگی‌ها
- [ ] لیست فایل‌های shared: `find shared/ -name "*.py" | wc -l`
- [ ] بررسی import های shared در request-network: `grep -r "from shared" request-network/`
- [ ] بررسی import های shared در response-network: `grep -r "from shared" response-network/`

## مرحله 2: کپی کردن shared به request-network (10 دقیقه)

### 2.1 کپی پوشه shared
- [ ] ایجاد پوشه: `mkdir -p request-network/api/shared`
- [ ] کپی فایل‌ها: `cp -r shared/* request-network/api/shared/`
- [ ] بررسی کپی: `ls -la request-network/api/shared/`

### 2.2 تغییر import ها در request-network
- [ ] تغییر `from shared.database.base` به `from .shared.database.base` در:
  - [ ] `request-network/api/models/*.py` (8 فایل)
  - [ ] `request-network/api/create_settings_table.py`
  - [ ] `request-network/api/alembic/env.py`
  - [ ] `request-network/api/manage.py`
  - [ ] `request-network/api/create_tables.py`

- [ ] تغییر `from shared.logger` به `from .shared.logger` در:
  - [ ] `request-network/api/main.py`
  - [ ] `request-network/api/routers/api_key_router.py`

- [ ] تغییر `from shared.config` به `from .shared.config` در:
  - [ ] `request-network/api/setup/setup_worker_settings.py`

### 2.3 تست import ها در request-network
- [ ] تست import: `cd request-network/api && python -c "from .shared.database.base import BaseModel; print('OK')"`
- [ ] بررسی syntax errors: `python -m py_compile request-network/api/main.py`

## مرحله 3: کپی کردن shared به response-network (10 دقیقه)

### 3.1 کپی پوشه shared
- [ ] ایجاد پوشه: `mkdir -p response-network/api/shared`
- [ ] کپی فایل‌ها: `cp -r shared/* response-network/api/shared/`
- [ ] بررسی کپی: `ls -la response-network/api/shared/`

### 3.2 تغییر import ها در response-network
- [ ] تغییر `from shared.database.base` به `from .shared.database.base` در:
  - [ ] `response-network/api/models/*.py` (15+ فایل)
  - [ ] `response-network/api/create_settings_table.py`
  - [ ] `response-network/api/alembic/env.py`
  - [ ] `response-network/api/manage.py`
  - [ ] `response-network/api/test_import.py`
  - [ ] `response-network/api/test_path.py`

- [ ] تغییر `from shared.config` به `from .shared.config` در:
  - [ ] `response-network/api/setup/setup_worker_settings.py`

- [ ] تغییر `from shared.models` به `from .shared.models` در:
  - [ ] `response-network/api/alembic/env.py`

### 3.3 تست import ها در response-network
- [ ] تست import: `cd response-network/api && python -c "from .shared.database.base import BaseModel; print('OK')"`
- [ ] بررسی syntax errors: `python -m py_compile response-network/api/main.py`

## مرحله 4: پیاده‌سازی Runtime Configuration برای Frontend (20 دقیقه)

### 4.1 ایجاد Runtime Config Script برای Request Network
- [ ] ایجاد فایل: `request-network/admin-panel/public/config.js`
```javascript
window.__RUNTIME_CONFIG__ = {
  API_URL: '${NEXT_PUBLIC_API_URL}' || 'http://localhost:8001'
};
```
- [ ] ایجاد فایل: `request-network/admin-panel/generate-config.sh`
```bash
#!/bin/bash
envsubst < /app/public/config.template.js > /app/public/config.js
```

### 4.2 ایجاد Runtime Config Script برای Response Network
- [ ] ایجاد فایل: `response-network/admin-panel/public/config.js`
```javascript
window.__RUNTIME_CONFIG__ = {
  API_URL: '${NEXT_PUBLIC_API_URL}' || 'http://localhost:8000'
};
```
- [ ] ایجاد فایل: `response-network/admin-panel/generate-config.sh`

### 4.3 بروزرسانی API Client ها
- [ ] تغییر `request-network/admin-panel/app/(auth)/api.ts`:
```typescript
const getApiUrl = () => {
  if (typeof window !== 'undefined' && window.__RUNTIME_CONFIG__) {
    return window.__RUNTIME_CONFIG__.API_URL;
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
};

const api = axios.create({
  baseURL: getApiUrl(),
  // ... rest of config
});
```
- [ ] تغییر مشابه در `response-network/admin-panel/app/(auth)/api.ts`

### 4.4 اضافه کردن Runtime Config به HTML
- [ ] بروزرسانی `request-network/admin-panel/app/layout.tsx`:
```tsx
<Script src="/config.js" strategy="beforeInteractive" />
```
- [ ] بروزرسانی `response-network/admin-panel/app/layout.tsx`

## مرحله 5: بروزرسانی Dockerfile ها (15 دقیقه)

### 5.1 بروزرسانی Dockerfile.request
- [ ] تغییر `COPY . /app` به `COPY request-network/ /app/request-network/`
- [ ] تغییر `WORKDIR /app/request-network/api`
- [ ] حذف دسترسی به response-network
- [ ] بروزرسانی PYTHONPATH: `ENV PYTHONPATH="/app/request-network/api:${PYTHONPATH}"`

### 5.2 بروزرسانی Dockerfile.response
- [ ] اطمینان از `COPY response-network/api /app`
- [ ] بررسی PYTHONPATH: `ENV PYTHONPATH="/app:${PYTHONPATH}"`
- [ ] حذف هرگونه ارجاع به shared مرکزی

### 5.3 بروزرسانی Frontend Dockerfile ها
- [ ] بروزرسانی `request-network/admin-panel/Dockerfile`:
```dockerfile
# Runtime stage
FROM node:20-slim
WORKDIR /app
# کپی built files
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json .

# اضافه کردن runtime config generation
COPY generate-config.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/generate-config.sh

# Create config template
RUN echo 'window.__RUNTIME_CONFIG__={API_URL:"${NEXT_PUBLIC_API_URL}"}' > /app/public/config.template.js

EXPOSE 3002
CMD ["/bin/sh", "-c", "generate-config.sh && npm start"]
```
- [ ] بروزرسانی مشابه `response-network/admin-panel/Dockerfile`

### 5.4 بروزرسانی docker-compose فایل‌ها
- [ ] بررسی volume mappings در `docker-compose.request.yml`
- [ ] بررسی volume mappings در `docker-compose.response.yml`
- [ ] حذف shared volume mappings
- [ ] اضافه کردن environment variables برای runtime config

## مرحله 5: بروزرسانی اسکریپت‌های deployment (10 دقیقه)

### 5.1 بروزرسانی deploy_production.sh
- [ ] تغییر rsync excludes برای حذف shared مرکزی
- [ ] اضافه کردن `--exclude="shared"` به rsync
- [ ] بررسی path های کپی شده

### 5.2 بروزرسانی entrypoint scripts
- [ ] بررسی `entrypoint-request.sh`
- [ ] بررسی `entrypoint.sh`
- [ ] اطمینان از صحت path ها

## مرحله 6: تست محلی (25 دقیقه)

### 6.1 تست request-network
- [ ] build image: `docker build -f Dockerfile.request -t test-request .`
- [ ] run container: `docker run --rm test-request python -c "import main; print('Request OK')"`
- [ ] تست docker-compose: `docker-compose -f docker-compose.request.yml up --build -d`
- [ ] بررسی logs: `docker-compose -f docker-compose.request.yml logs api-request`
- [ ] تست API: `curl http://localhost:8001/api/v1/health`
- [ ] تست Frontend: `curl http://localhost:3002`
- [ ] تست Runtime Config: بررسی `http://localhost:3002/config.js` در مرورگر
- [ ] stop: `docker-compose -f docker-compose.request.yml down`

### 6.2 تست response-network
- [ ] build image: `docker build -f Dockerfile.response -t test-response .`
- [ ] run container: `docker run --rm test-response python -c "import main; print('Response OK')"`
- [ ] تست docker-compose: `docker-compose -f docker-compose.response.yml up --build -d`
- [ ] بررسی logs: `docker-compose -f docker-compose.response.yml logs api-response`
- [ ] تست API: `curl http://localhost:8000/api/v1/health`
- [ ] تست Frontend: `curl http://localhost:3000`
- [ ] تست Runtime Config: بررسی `http://localhost:3000/config.js` در مرورگر
- [ ] stop: `docker-compose -f docker-compose.response.yml down`

### 6.3 تست database migrations
- [ ] تست alembic در request-network: `docker exec request-api alembic check`
- [ ] تست alembic در response-network: `docker exec response-api alembic check`

### 6.4 تست Runtime Configuration
- [ ] تغییر NEXT_PUBLIC_API_URL در docker-compose و restart
- [ ] بررسی تغییر API URL در frontend بدون rebuild
- [ ] تست login با API URL جدید
- [ ] بررسی console logs برای API calls

## مرحله 7: پاکسازی و تمیزکاری (10 دقیقه)

### 7.1 حذف shared مرکزی
- [ ] **هشدار: فقط بعد از تست موفق**
- [ ] rename برای احتیاط: `mv shared shared_old_backup`
- [ ] تست مجدد build ها
- [ ] در صورت موفقیت: `rm -rf shared_old_backup`

### 7.2 حذف فایل‌های غیرضروری
- [ ] حذف core/ مرکزی: `rm -rf core/`
- [ ] حذف فایل‌های test موقت:
  - [ ] `rm response-network/api/test_*.py`
  - [ ] `rm request-network/api/test_*.py` (اگر وجود دارد)

### 7.3 بروزرسانی .gitignore
- [ ] اضافه کردن `shared_old_backup/` به .gitignore
- [ ] حذف `shared/` از .gitignore (اگر وجود دارد)

## مرحله 8: بروزرسانی مستندات (5 دقیقه)

### 8.1 بروزرسانی ARCHITECTURE.md
- [ ] بروزرسانی diagram جداسازی شبکه‌ها
- [ ] توضیح ساختار جدید shared
- [ ] حذف ارجاعات به shared مرکزی

### 8.2 بروزرسانی README ها
- [ ] بروزرسانی `request-network/README.md`
- [ ] بروزرسانی `response-network/README.md`
- [ ] توضیح ساختار جدید

## مرحله 9: تست نهایی و commit (10 دقیقه)

### 9.1 تست کامل
- [ ] build تمام images: `docker-compose build`
- [ ] تست end-to-end اگر موجود است
- [ ] بررسی حجم images: `docker images | grep -E "(request|response)"`

### 9.2 Git operations
- [ ] add تغییرات: `git add .`
- [ ] commit: `git commit -m "Network separation: Move shared code to each network"`
- [ ] push branch: `git push origin network-separation`

## مرحله 10: تست production (اختیاری)

### 10.1 تست در محیط staging
- [ ] deploy روی staging environment
- [ ] تست عملکرد
- [ ] بررسی logs

### 10.2 merge به main
- [ ] ایجاد pull request
- [ ] review تغییرات
- [ ] merge به main branch

---

## نکات مهم:
- ⚠️ **هرگز shared مرکزی را قبل از تست کامل حذف نکنید**
- ⚠️ **قبل از هر مرحله بک‌آپ بگیرید**
- ⚠️ **تست هر مرحله قبل از ادامه**
- ⚠️ **در صورت بروز مشکل، از backup استفاده کنید**

## زمان تخمینی کل: 110 دقیقه (1.8 ساعت)

## فایل‌های تغییر یافته (تقریبی):
- 25+ فایل Python (import changes)
- 4 Dockerfile (2 backend + 2 frontend)
- 2+ docker-compose files  
- 1+ deployment script
- 4+ frontend files (runtime config)
- 2+ documentation files