# لیست کارهای رفع مشکلات استقرار و مانیتورینگ

## خلاصه

این سند شامل سه مشکل اصلی است که باید به ترتیب حل شوند:

1. **راه‌اندازی Elasticsearch و Kibana** روی سرور 192.168.214.139
2. **رفع خطای 500** در endpoint لیست درخواست‌ها
3. **تفکیک وضعیت‌های خطا** در پاسخ‌های API

## ⚠️ نکات مهم

- همه تغییرات باید با دقت انجام شوند تا سرویس‌های موجود مختل نشوند
- قبل از هر تغییر، تست‌های preservation اجرا شوند
- بعد از هر تغییر، تست‌های validation اجرا شوند
- هیچ تغییری در schema دیتابیس نیاز نیست

---

## بخش 1: راه‌اندازی Elasticsearch و Kibana

### گام 1: تست اولیه (باید fail شود)
```bash
# بررسی دسترسی به Elasticsearch
curl http://192.168.214.139:9200/_cluster/health
# انتظار: Connection refused

# بررسی دسترسی به Kibana
curl http://192.168.214.139:5601/api/status
# انتظار: Connection refused

# بررسی کانتینرها
ssh response@192.168.214.139 "docker ps | grep elasticsearch"
# انتظار: هیچ کانتینری یافت نشود
```

### گام 2: تست preservation (باید pass شود)
```bash
# بررسی PostgreSQL
docker exec -it response-db psql -U postgres -c "SELECT 1;"

# بررسی Redis
docker exec -it response-redis redis-cli ping

# بررسی API
curl http://192.168.214.141:8000/api/v1/health

# بررسی Celery workers
docker logs response-worker --tail 20
```

### گام 3: پیاده‌سازی

#### 3.1: ایجاد تابع deploy برای Elasticsearch
- فایل: `deploy.sh`
- اضافه کردن تابع `deploy_elasticsearch()`
- استفاده از `docker-compose.elasticsearch.yml`
- استقرار روی سرور 192.168.214.139

#### 3.2: اضافه کردن health check
- پیاده‌سازی حلقه polling برای `/_cluster/health`
- timeout 60 ثانیه
- لاگ کردن پیشرفت

#### 3.3: یکپارچه‌سازی با workflow اصلی
- تغییر منطق deployment برای اجرای Elasticsearch قبل از response-network
- اضافه کردن flag اختیاری `--skip-elasticsearch`

#### 3.4: پیکربندی شبکه Docker
- اطمینان از ارتباط بین کانتینرها
- استفاده از bridge network یا host mode

### گام 4: اعتبارسنجی
```bash
# تست دسترسی به Elasticsearch
curl http://192.168.214.139:9200/_cluster/health
# انتظار: {"status":"green"} یا {"status":"yellow"}

# تست دسترسی به Kibana
curl http://192.168.214.139:5601/api/status
# انتظار: {"status":{"overall":{"level":"available"}}}

# بررسی کانتینرها
docker ps | grep -E "elasticsearch|kibana"
# انتظار: دو کانتینر در حال اجرا

# تست preservation مجدد
# همه تست‌های گام 2 باید همچنان pass شوند
```

---

## بخش 2: رفع خطای 500 در endpoint لیست درخواست‌ها

### گام 5: تست اولیه (باید fail شود)
```bash
# دریافت token
TOKEN=$(curl -X POST http://192.168.214.141:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

# تست endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests?limit=10
# انتظار: 500 Internal Server Error

# بررسی لاگ‌ها
docker logs response-api --tail 50
# انتظار: exception traceback
```

### گام 6: تست preservation (باید pass شود)
```bash
# تست authentication
curl -X POST http://192.168.214.141:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
# انتظار: 200 OK با token

# تست user endpoints
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/users
# انتظار: 200 OK

# تست stats endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests/stats
# انتظار: 200 OK
```

### گام 7: پیاده‌سازی

#### 7.1: اضافه کردن eager loading
- فایل: `response-network/api/crud/requests.py`
- import: `from sqlalchemy.orm import selectinload`
- اضافه کردن: `.options(selectinload(IncomingRequest.result))`

#### 7.2: اضافه کردن null-safe access
- تغییر: `"result": r.result.result_data if r.result else None`

#### 7.3: اضافه کردن exception handling به get_requests()
- wrap کردن function body در try-except
- لاگ کردن خطاها با traceback کامل

#### 7.4: اضافه کردن error handling به endpoint
- فایل: `response-network/api/router/request_router.py`
- wrap کردن endpoint logic در try-except
- برگرداندن HTTPException با status مناسب

#### 7.5: بررسی async consistency
- اطمینان از استفاده از await برای همه db.execute()
- بررسی عدم استفاده از متدهای sync

### گام 8: اعتبارسنجی
```bash
# تست endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests?limit=10
# انتظار: 200 OK با JSON معتبر

# تست با فیلتر status
curl -H "Authorization: Bearer $TOKEN" \
  "http://192.168.214.141:8000/api/v1/requests?status=pending"
# انتظار: 200 OK

# تست preservation مجدد
# همه تست‌های گام 6 باید همچنان pass شوند
```

---

## بخش 3: تفکیک وضعیت‌های خطا

### گام 9: تست اولیه (باید fail شود)
```bash
# دریافت لیست درخواست‌ها
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests?limit=10 | jq '.[0]'
# انتظار: پاسخ بدون فیلد "outcome"

# بررسی ساختار پاسخ
# باید فیلدهای status, has_error, result وجود داشته باشد
# اما فیلد outcome نباید وجود داشته باشد
```

### گام 10: تست preservation (باید pass شود)
```bash
# تست status transitions در Celery
docker logs response-worker --tail 50
# بررسی: pending → processing → completed

# تست database updates
docker exec -it response-db psql -U postgres -d response_db \
  -c "SELECT id, status, has_error FROM incoming_requests LIMIT 5;"
# بررسی: مقادیر status صحیح هستند
```

### گام 11: پیاده‌سازی

#### 11.1: اضافه کردن outcome computation به get_requests()
- فایل: `response-network/api/crud/requests.py`
- اضافه کردن منطق محاسبه outcome:
```python
if r.status in ['pending', 'processing']:
    outcome = 'pending'
elif r.has_error or r.status == 'failed':
    outcome = 'error'
elif r.status == 'completed' and r.result:
    outcome = 'success'
else:
    outcome = 'unknown'
```
- اضافه کردن `"outcome": outcome` به dictionary

#### 11.2: اضافه کردن outcome به get_request()
- همان منطق را برای endpoint تک درخواست اعمال کنید

#### 11.3: اضافه کردن مستندات
- docstring برای توضیح مقادیر outcome
- کامنت‌های inline برای منطق محاسبه

#### 11.4: بروزرسانی Pydantic schema (اختیاری)
- فایل: `response-network/api/models/schemas.py`
- اضافه کردن: `outcome: Optional[str] = None`

### گام 12: اعتبارسنجی
```bash
# تست outcome field
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests?limit=10 | jq '.[0].outcome'
# انتظار: "pending" یا "success" یا "error"

# تست درخواست pending
curl -H "Authorization: Bearer $TOKEN" \
  "http://192.168.214.141:8000/api/v1/requests?status=pending" | jq '.[0].outcome'
# انتظار: "pending"

# تست درخواست completed
curl -H "Authorization: Bearer $TOKEN" \
  "http://192.168.214.141:8000/api/v1/requests?status=completed" | jq '.[0].outcome'
# انتظار: "success" یا "error" بسته به has_error

# تست preservation مجدد
# همه تست‌های گام 10 باید همچنان pass شوند
```

---

## اعتبارسنجی نهایی

### گام 13: تست end-to-end کامل
```bash
# 1. بررسی Elasticsearch و Kibana
curl http://192.168.214.139:9200/_cluster/health
curl http://192.168.214.139:5601/api/status

# 2. بررسی endpoint لیست درخواست‌ها
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests?limit=10

# 3. بررسی outcome field
curl -H "Authorization: Bearer $TOKEN" \
  http://192.168.214.141:8000/api/v1/requests | jq '.[].outcome' | sort | uniq

# 4. بررسی همه سرویس‌های موجود
docker ps
# انتظار: همه کانتینرها healthy باشند

# 5. تست workflow کامل
# - ایجاد یک درخواست جدید
# - بررسی outcome="pending"
# - منتظر پردازش
# - بررسی outcome="success" یا "error"
```

---

## چک‌لیست نهایی

- [ ] Elasticsearch در دسترس است: http://192.168.214.139:9200
- [ ] Kibana در دسترس است: http://192.168.214.139:5601
- [ ] Endpoint لیست درخواست‌ها 200 OK برمی‌گرداند
- [ ] همه پاسخ‌های API شامل فیلد outcome هستند
- [ ] PostgreSQL بدون مشکل کار می‌کند
- [ ] Redis بدون مشکل کار می‌کند
- [ ] Celery workers بدون مشکل کار می‌کنند
- [ ] Authentication و Authorization بدون تغییر است
- [ ] Status transitions صحیح هستند
- [ ] هیچ regression در سرویس‌های موجود نیست

---

## مستندات مرجع

- Spec Requirements: `.kiro/specs/deployment-fixes-and-monitoring/bugfix.md`
- Spec Design: `.kiro/specs/deployment-fixes-and-monitoring/design.md`
- Spec Tasks: `.kiro/specs/deployment-fixes-and-monitoring/tasks.md`
- Elasticsearch Config: `docker-compose.elasticsearch.yml`
- Deployment Script: `deploy.sh`

## دستورات مفید

```bash
# مشاهده لاگ‌های Elasticsearch
docker logs airline_elasticsearch --tail 50

# مشاهده لاگ‌های Kibana
docker logs airline_kibana --tail 50

# مشاهده لاگ‌های API
docker logs response-api --tail 50

# مشاهده لاگ‌های Worker
docker logs response-worker --tail 50

# ری‌استارت سرویس‌ها
docker-compose -f docker-compose.elasticsearch.yml restart

# بررسی health همه سرویس‌ها
docker ps --format "table {{.Names}}\t{{.Status}}"
```
