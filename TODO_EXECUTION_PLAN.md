# نقشه اجرای دقیق - رفع مشکلات استقرار

## خلاصه مسائل
1. **الستیک و کیبانا** روی سرور 192.168.214.139 راه‌اندازی نشده
2. **خطای 500** در endpoint لیست درخواست‌ها: `GET /api/v1/requests`
3. **عدم تفکیک وضعیت‌ها** در پاسخ API (pending vs success vs error)

---

## مرحله 1: راه‌اندازی Elasticsearch و Kibana

### 1.1 تست وضعیت فعلی (باید fail شود)
```bash
# بررسی عدم دسترسی به Elasticsearch
curl http://192.168.214.139:9200/_cluster/health
# انتظار: Connection refused

# بررسی عدم دسترسی به Kibana  
curl http://192.168.214.139:5601/api/status
# انتظار: Connection refused

# بررسی عدم وجود کانتینرها
docker ps | grep -E "elasticsearch|kibana"
# انتظار: هیچ خروجی
```

### 1.2 بررسی سرویس‌های موجود (باید سالم باشند)
```bash
# PostgreSQL
docker exec response-db psql -U postgres -c "SELECT 1;"

# Redis  
docker exec response-redis redis-cli ping

# API
curl http://192.168.214.141:8000/docs

# Celery
docker logs response-worker --tail 10
```

### 1.3 بررسی فایل‌های مورد نیاز
```bash
# بررسی وجود docker-compose.elasticsearch.yml
ls -la docker-compose.elasticsearch.yml

# بررسی محتوای فایل
cat docker-compose.elasticsearch.yml
```

### 1.4 اصلاح اسکریپت deploy.sh
- اضافه کردن تابع `deploy_elasticsearch()`
- یکپارچه‌سازی با workflow اصلی
- اضافه کردن health check

### 1.5 اجرای استقرار Elasticsearch
```bash
# اجرای استقرار
./deploy.sh elasticsearch

# یا اگر در deploy.sh یکپارچه شد:
./deploy.sh response  # باید Elasticsearch را هم شامل شود
```

### 1.6 اعتبارسنجی
```bash
# تست دسترسی
curl http://192.168.214.139:9200/_cluster/health
# انتظار: {"status":"green"} یا {"status":"yellow"}

curl http://192.168.214.139:5601/api/status  
# انتظار: {"status":{"overall":{"level":"available"}}}

# بررسی کانتینرها
docker ps | grep -E "elasticsearch|kibana"
# انتظار: دو کانتینر healthy
```

---

## مرحله 2: رفع خطای 500 در endpoint لیست درخواست‌ها

### 2.1 تست خطای فعلی (باید fail شود)
```bash
# دریافت token
TOKEN=$(curl -s -X POST http://192.168.214.141:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

# تست endpoint مشکل‌دار
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests?limit=10
# انتظار: 500 Internal Server Error

# بررسی لاگ خطا
docker logs response-api --tail 20
```

### 2.2 بررسی سایر endpoint‌ها (باید سالم باشند)
```bash
# Authentication
curl -X POST http://192.168.214.141:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Users
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/users

# Stats  
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests/stats
```

### 2.3 اصلاح فایل crud/requests.py
**فایل:** `response-network/api/crud/requests.py`

**تغییرات:**
1. اضافه کردن eager loading:
```python
from sqlalchemy.orm import selectinload

# در تابع get_requests():
query = select(IncomingRequest, User.username).options(
    selectinload(IncomingRequest.result)
).outerjoin(User, IncomingRequest.user_id == User.id)
```

2. اصلاح null-safe access:
```python
"result": r.result.result_data if r.result else None,
"error_message": r.error_message if r.error_message else None,
```

3. اضافه کردن exception handling:
```python
try:
    # کد موجود
except Exception as e:
    logger.error(f"Error in get_requests: {str(e)}", exc_info=True)
    raise
```

### 2.4 اصلاح router/request_router.py
**فایل:** `response-network/api/router/request_router.py`

**تغییرات:**
```python
from fastapi import HTTPException
import logging

@router.get("/requests")
async def list_requests(...):
    try:
        # کد موجود
        return await get_requests(...)
    except Exception as e:
        logger.error(f"Error in list_requests endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 2.5 اعتبارسنجی
```bash
# تست endpoint اصلاح شده
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests?limit=10
# انتظار: 200 OK با JSON معتبر

# تست با فیلترها
curl -H "Authorization: Bearer $TOKEN" \
  "http://192.168.214.141:8000/api/v1/requests?status=pending&limit=5"
```

---

## مرحله 3: تفکیک وضعیت‌های خطا

### 3.1 تست وضعیت فعلی (عدم تفکیک)
```bash
# دریافت نمونه پاسخ
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests?limit=3 | jq '.[0]'
# بررسی: آیا فیلد "outcome" وجود دارد؟ (نباید وجود داشته باشد)
```

### 3.2 بررسی status management موجود
```bash
# بررسی انواع status در دیتابیس
docker exec response-db psql -U postgres -d response_db \
  -c "SELECT DISTINCT status FROM incoming_requests;"

# بررسی has_error field
docker exec response-db psql -U postgres -d response_db \
  -c "SELECT status, has_error, COUNT(*) FROM incoming_requests GROUP BY status, has_error;"
```

### 3.3 اصلاح crud/requests.py برای outcome field
**فایل:** `response-network/api/crud/requests.py`

**در تابع get_requests() و get_request():**
```python
# اضافه کردن محاسبه outcome
def compute_outcome(status, has_error, result):
    if status in ['pending', 'processing']:
        return 'pending'
    elif has_error or status == 'failed':
        return 'error'  
    elif status == 'completed' and result:
        return 'success'
    else:
        return 'unknown'

# در dictionary ایجاد شده:
item = {
    # فیلدهای موجود...
    "outcome": compute_outcome(r.status, r.has_error, r.result)
}
```

### 3.4 اعتبارسنجی outcome field
```bash
# تست outcome field
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests?limit=5 | jq '.[].outcome'
# انتظار: مقادیر "pending", "success", "error"

# تست تفکیک بر اساس status
curl -H "Authorization: Bearer $TOKEN" \
  "http://192.168.214.141:8000/api/v1/requests?status=pending" | jq '.[0].outcome'
# انتظار: "pending"

curl -H "Authorization: Bearer $TOKEN" \
  "http://192.168.214.141:8000/api/v1/requests?status=completed" | jq '.[].outcome'
# انتظار: "success" یا "error"
```

---

## مرحله 4: اعتبارسنجی نهایی

### 4.1 تست کامل همه بخش‌ها
```bash
# 1. Elasticsearch و Kibana
curl -s http://192.168.214.139:9200/_cluster/health | jq '.status'
curl -s http://192.168.214.139:5601/api/status | jq '.status.overall.level'

# 2. API endpoint
curl -s -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests?limit=3 | jq 'length'

# 3. Outcome field
curl -s -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests | jq '.[].outcome' | sort | uniq -c

# 4. همه سرویس‌ها
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(response|elasticsearch|kibana)"
```

### 4.2 تست عدم regression
```bash
# PostgreSQL
docker exec response-db psql -U postgres -c "SELECT COUNT(*) FROM incoming_requests;"

# Redis
docker exec response-redis redis-cli info replication

# Celery workers
docker logs response-worker --tail 5

# Authentication
curl -X POST http://192.168.214.141:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq '.access_token'
```

### 4.3 تست workflow کامل
```bash
# شبیه‌سازی یک درخواست کامل:
# 1. ایجاد درخواست جدید (اگر امکان دارد)
# 2. بررسی outcome="pending"  
# 3. منتظر پردازش
# 4. بررسی outcome="success" یا "error"
```

---

## چک‌لیست نهایی

- [ ] ✅ Elasticsearch در دسترس: http://192.168.214.139:9200
- [ ] ✅ Kibana در دسترس: http://192.168.214.139:5601  
- [ ] ✅ `/api/v1/requests` برمی‌گرداند 200 OK
- [ ] ✅ همه پاسخ‌ها شامل فیلد `outcome` هستند
- [ ] ✅ PostgreSQL بدون مشکل کار می‌کند
- [ ] ✅ Redis بدون مشکل کار می‌کند
- [ ] ✅ Celery workers بدون مشکل کار می‌کنند
- [ ] ✅ Authentication بدون تغییر است
- [ ] ✅ هیچ regression در سرویس‌های موجود نیست

---

## دستورات مفید برای debugging

```bash
# مشاهده لاگ‌ها
docker logs response-api --tail 50 -f
docker logs response-worker --tail 50 -f  
docker logs elasticsearch --tail 50 -f
docker logs kibana --tail 50 -f

# بررسی health
curl http://192.168.214.139:9200/_cat/health?v
curl http://192.168.214.139:5601/api/status

# ری‌استارت در صورت نیاز
docker-compose restart response-api
docker-compose -f docker-compose.elasticsearch.yml restart

# بررسی شبکه
docker network ls
docker network inspect bridge
```

## نکات مهم

1. **ترتیب اجرا مهم است** - ابتدا Elasticsearch، سپس API fix، سپس outcome field
2. **قبل از هر تغییر** تست preservation انجام دهید
3. **بعد از هر تغییر** تست validation انجام دهید  
4. **هیچ تغییری در schema** دیتابیس نیاز نیست
5. **backup** از فایل‌های مهم قبل از تغییر بگیرید