# راهنمای دیپلوی تغییرات SSL Elasticsearch به Production

## فایل‌های تغییر یافته

این دو فایل تغییر کرده‌اند:
1. `response-network/api/workers/tasks/execute_query.py`
2. `response-network/api/workers/elasticsearch_client.py`

## روش‌های دیپلوی

### روش 1: استفاده از Docker Volumes (توصیه می‌شود - بدون نیاز به rebuild)

اگر از volumes استفاده می‌کنید (که در `docker-compose.response.yml` شما هست):

```yaml
volumes:
  - ./response-network/api:/app
```

**مراحل:**

1. **فایل‌های تغییر یافته را به سرور کپی کنید:**

```bash
# از ماشین محلی:
scp response-network/api/workers/tasks/execute_query.py user@production-server:/path/to/project/response-network/api/workers/tasks/
scp response-network/api/workers/elasticsearch_client.py user@production-server:/path/to/project/response-network/api/workers/
```

2. **Worker را restart کنید:**

```bash
# روی سرور production:
cd /path/to/project
docker-compose -f docker-compose.response.yml restart celery-worker-response
docker-compose -f docker-compose.response.yml restart celery-beat-response
```

3. **لاگ‌ها را بررسی کنید:**

```bash
docker-compose -f docker-compose.response.yml logs -f celery-worker-response
```

✅ **مزایا:**
- سریع است (بدون نیاز به rebuild)
- تغییرات فوری اعمال می‌شود
- برای تست و توسعه مناسب است

❌ **معایب:**
- اگر container را از نو بسازید، تغییرات از بین می‌رود

---

### روش 2: Rebuild کردن Docker Image (توصیه برای production)

این روش تضمین می‌کند که تغییرات در image ذخیره شود.

**مراحل:**

1. **تغییرات را commit کنید (اختیاری ولی توصیه می‌شود):**

```bash
git add response-network/api/workers/tasks/execute_query.py
git add response-network/api/workers/elasticsearch_client.py
git commit -m "fix: SSL verification for Elasticsearch connections"
git push
```

2. **روی سرور، کد جدید را pull کنید:**

```bash
# روی سرور production:
cd /path/to/project
git pull origin main  # یا branch مورد نظر
```

3. **Image را rebuild کنید:**

```bash
docker-compose -f docker-compose.response.yml build api-response celery-worker-response celery-beat-response
```

4. **Container‌ها را restart کنید:**

```bash
docker-compose -f docker-compose.response.yml up -d --force-recreate api-response celery-worker-response celery-beat-response
```

5. **لاگ‌ها را بررسی کنید:**

```bash
docker-compose -f docker-compose.response.yml logs -f celery-worker-response
```

✅ **مزایا:**
- تغییرات دائمی است
- برای production مناسب است
- قابل rollback است

❌ **معایب:**
- زمان‌برتر است (چند دقیقه برای build)
- نیاز به downtime کوتاه دارد

---

### روش 3: استفاده از docker cp (برای تست سریع)

اگر می‌خواهید بدون git یا rebuild تست کنید:

**مراحل:**

1. **فایل‌ها را به container کپی کنید:**

```bash
# روی سرور production:
docker cp response-network/api/workers/tasks/execute_query.py celery-worker-response:/app/workers/tasks/
docker cp response-network/api/workers/elasticsearch_client.py celery-worker-response:/app/workers/
```

2. **Worker را restart کنید:**

```bash
docker-compose -f docker-compose.response.yml restart celery-worker-response
docker-compose -f docker-compose.response.yml restart celery-beat-response
```

⚠️ **توجه:** این تغییرات موقت است و با restart کردن container از بین می‌رود.

---

## روش توصیه شده برای Production

**مرحله به مرحله:**

### 1. آماده‌سازی (روی ماشین محلی)

```bash
# تست کنید که همه چیز کار می‌کند
cd /home/docker/the_first/the_first
docker-compose -f docker-compose.response.yml restart celery-worker-response

# لاگ‌ها را بررسی کنید
docker-compose -f docker-compose.response.yml logs celery-worker-response | grep ELASTICSEARCH

# اگر همه چیز خوب بود، commit کنید
git add response-network/api/workers/tasks/execute_query.py
git add response-network/api/workers/elasticsearch_client.py
git add ELASTICSEARCH_SSL_FIX.md
git add ELASTICSEARCH_SSL_GUIDE_FA.md
git add test_elasticsearch_ssl.py
git commit -m "fix: Add SSL verification support for Elasticsearch connections

- Add SSL context handling in execute_query.py
- Fix close() method in elasticsearch_client.py
- Add documentation and test scripts"

git push origin main
```

### 2. دیپلوی به Production

```bash
# SSH به سرور
ssh user@production-server

# رفتن به دایرکتوری پروژه
cd /path/to/project

# Backup گرفتن (احتیاط)
docker-compose -f docker-compose.response.yml exec celery-worker-response \
  tar czf /tmp/backup-workers-$(date +%Y%m%d-%H%M%S).tar.gz /app/workers/

# Pull کردن تغییرات
git pull origin main

# Rebuild کردن image‌ها
docker-compose -f docker-compose.response.yml build celery-worker-response celery-beat-response

# Restart کردن با image جدید
docker-compose -f docker-compose.response.yml up -d --force-recreate celery-worker-response celery-beat-response

# بررسی وضعیت
docker-compose -f docker-compose.response.yml ps

# بررسی لاگ‌ها
docker-compose -f docker-compose.response.yml logs -f celery-worker-response
```

### 3. تست در Production

```bash
# 1. بررسی لاگ‌ها برای پیام SSL
docker-compose -f docker-compose.response.yml logs celery-worker-response | grep "ELASTICSEARCH"

# باید چیزی شبیه این ببینید:
# [ELASTICSEARCH] Loaded config from database: https://...
# [ELASTICSEARCH] SSL verification disabled for https://...

# 2. از Admin Panel یک query تست ارسال کنید

# 3. نتیجه را بررسی کنید
```

---

## Rollback (در صورت مشکل)

اگر مشکلی پیش آمد:

```bash
# روش 1: برگشت به commit قبلی
git log --oneline  # پیدا کردن commit قبلی
git checkout <previous-commit-hash>
docker-compose -f docker-compose.response.yml build celery-worker-response
docker-compose -f docker-compose.response.yml up -d --force-recreate celery-worker-response

# روش 2: استفاده از backup
docker cp /tmp/backup-workers-*.tar.gz celery-worker-response:/tmp/
docker-compose -f docker-compose.response.yml exec celery-worker-response \
  tar xzf /tmp/backup-workers-*.tar.gz -C /
docker-compose -f docker-compose.response.yml restart celery-worker-response
```

---

## Checklist نهایی

قبل از دیپلوی:
- [ ] تغییرات را در محیط dev تست کردید
- [ ] لاگ‌ها را بررسی کردید
- [ ] تغییرات را commit کردید
- [ ] Backup از production گرفتید

بعد از دیپلوی:
- [ ] Container‌ها healthy هستند
- [ ] لاگ‌ها پیام SSL را نشان می‌دهند
- [ ] یک query تست موفق بود
- [ ] تنظیمات Elasticsearch در Admin Panel صحیح است

---

## نکات مهم

1. **Downtime:** با روش rebuild، حدود 1-2 دقیقه downtime خواهید داشت
2. **Database:** نیازی به تغییر در database نیست
3. **API:** نیازی به restart کردن API نیست (فقط worker‌ها)
4. **Frontend:** نیازی به تغییر در frontend نیست

---

## پشتیبانی

اگر مشکلی پیش آمد:

```bash
# لاگ‌های کامل
docker-compose -f docker-compose.response.yml logs --tail=100 celery-worker-response > worker-logs.txt

# وضعیت container‌ها
docker-compose -f docker-compose.response.yml ps > containers-status.txt

# تنظیمات Elasticsearch از database
docker-compose -f docker-compose.response.yml exec postgres-response-db \
  psql -U respuser -d response_db -c "SELECT * FROM elasticsearch_config;" > es-config.txt
```

این فایل‌ها را برای بررسی ارسال کنید.
