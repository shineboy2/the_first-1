# تغییرات یکپارچه‌سازی بین دو شبکه

## تاریخ: 26 آوریل 2026

---

## مشکل

قبلاً، وقتی response-network نتایج را export می‌کرد، فقط این اطلاعات ارسال می‌شد:
```json
{
  "request_id": "...",
  "status": "completed",
  "result_data": {...}
}
```

**مشکلات:**
1. هیچ اطلاعاتی درباره خطا یا موفقیت ارسال نمی‌شد
2. request-network نمی‌توانست تشخیص دهد که آیا نتیجه موفق بوده یا خطا داشته
3. همه درخواست‌ها به عنوان "completed" علامت‌گذاری می‌شدند

---

## راه‌حل

### 1. تغییرات در Response-Network (Export)

**فایل:** `response-network/api/workers/tasks/export_results.py`

**تغییرات:**
```python
export_list.append({
    "request_id": str(res.original_request_id),
    "status": request.status if request else "completed",  # ✅ وضعیت واقعی
    "has_error": has_error,  # ✅ فیلد جدید
    "result_data": res.result_data,
})
```

**منطق `has_error`:**
- `True` اگر `request.has_error == True` یا `request.status == 'failed'`
- `False` در غیر این صورت

---

### 2. تغییرات در Request-Network (Import)

**فایل:** `request-network/api/workers/tasks/results_importer.py`

**تغییرات:**

#### 2.1. خواندن `has_error` از JSON
```python
# Check has_error from the result_data (exported from response-network)
has_error = result_data.get("has_error", False)

# Also check if there's an error in the response_data itself
if not has_error and "error" in response_data:
    has_error = True
```

#### 2.2. تفکیک وضعیت درخواست
```python
# Update request status based on has_error
if has_error:
    request.status = "completed_error"  # ✅ خطا داشته
else:
    request.status = "completed_success"  # ✅ موفق بوده
```

---

## فرمت جدید فایل JSON

### قبل:
```json
{
  "request_id": "abc-123",
  "status": "completed",
  "result_data": {"count": 5, "results": [...]}
}
```

### بعد:
```json
{
  "request_id": "abc-123",
  "status": "completed",
  "has_error": false,
  "result_data": {"count": 5, "results": [...]}
}
```

یا در صورت خطا:
```json
{
  "request_id": "xyz-789",
  "status": "failed",
  "has_error": true,
  "result_data": {"error": "Elasticsearch Connection Error"}
}
```

---

## وضعیت‌های جدید در Request-Network

### قبل:
- `pending` - در انتظار
- `processing` - در حال پردازش
- `completed` - تکمیل شده (موفق یا خطا؟ نامشخص!)

### بعد:
- `pending` - در انتظار
- `processing` - در حال پردازش
- `completed_success` - ✅ تکمیل شده با موفقیت
- `completed_error` - ❌ تکمیل شده با خطا

---

## مزایا

### 1. تفکیک واضح
- Frontend می‌تواند به راحتی بین موفقیت و خطا تفکیک قائل شود
- UI می‌تواند رنگ‌ها و آیکون‌های مختلف نمایش دهد

### 2. گزارش‌گیری بهتر
- آمار دقیق از درخواست‌های موفق و ناموفق
- شناسایی مشکلات سیستمی

### 3. Backward Compatible
- فیلد `has_error` اختیاری است
- اگر وجود نداشته باشد، کد قدیمی همچنان کار می‌کند

---

## تست

### 1. تست Export (Response-Network)
```bash
# بررسی فایل export شده
ssh response@192.168.214.141 "cat ~/response-network/exports/results/results_*.jsonl | tail -5"

# باید has_error را ببینید:
# {"request_id":"...","status":"completed","has_error":false,"result_data":{...}}
```

### 2. تست Import (Request-Network)
```bash
# بررسی وضعیت درخواست‌ها
curl http://192.168.214.146:8000/api/v1/requests | jq '.[] | {status, has_error}'

# باید completed_success یا completed_error ببینید
```

### 3. تست End-to-End
```bash
# 1. ایجاد درخواست جدید در request-network
# 2. صبر برای پردازش در response-network
# 3. بررسی export
# 4. بررسی import
# 5. بررسی وضعیت نهایی در request-network
```

---

## Migration برای Request-Network

اگر درخواست‌های قدیمی با وضعیت "completed" دارید، می‌توانید آنها را به روز کنید:

```sql
-- درخواست‌هایی که پاسخ دارند و خطا ندارند
UPDATE requests 
SET status = 'completed_success' 
WHERE status = 'completed' 
AND id IN (
    SELECT request_id FROM responses WHERE has_error = false
);

-- درخواست‌هایی که پاسخ دارند و خطا دارند
UPDATE requests 
SET status = 'completed_error' 
WHERE status = 'completed' 
AND id IN (
    SELECT request_id FROM responses WHERE has_error = true
);
```

---

## فایل‌های تغییر یافته

### Response-Network
- ✅ `response-network/api/workers/tasks/export_results.py`

### Request-Network
- ✅ `request-network/api/workers/tasks/results_importer.py`

---

## نکات مهم

1. **همه تغییرات در codebase ذخیره شدند**
2. **Backward compatible است** - فایل‌های قدیمی بدون `has_error` همچنان کار می‌کنند
3. **Worker ها restart شدند** - تغییرات فوراً اعمال می‌شوند
4. **فایل‌های export جدید** شامل `has_error` هستند

---

## دستورات مفید

### بررسی لاگ‌های Export (Response-Network)
```bash
ssh response@192.168.214.141 "docker logs response-celery-worker --tail 50 | grep export"
```

### بررسی لاگ‌های Import (Request-Network)
```bash
ssh request@192.168.214.146 "docker logs request-celery-worker --tail 50 | grep import"
```

### بررسی فایل‌های Export
```bash
ssh response@192.168.214.141 "ls -lh ~/response-network/exports/results/"
ssh response@192.168.214.141 "cat ~/response-network/exports/results/results_*.jsonl | jq ."
```