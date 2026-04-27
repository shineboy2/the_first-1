# TODO: رفع مشکلات External API (بحرانی)

## ❌ مشکلات موجود

### 1. عدم وجود UI برای مدیریت دسترسی
**مشکل**: در Response Network Admin Panel صفحه‌ای برای مدیریت دسترسی External API ها وجود ندارد.

**وضعیت فعلی**:
- ✅ Backend endpoint موجود است: `PATCH /api/v1/external-apis/profile-types/{profile_type}/access`
- ❌ Frontend صفحه ندارد
- ❌ منو لینک ندارد

**راه‌حل**:
```
response-network/admin-panel/src/pages/ExternalAPIAccess.tsx
├── لیست External API ها
├── لیست Profile Types
├── Matrix برای تنظیم دسترسی
└── دکمه Save
```

**فایل‌های نیاز به تغییر**:
- [ ] `admin-panel/src/pages/ExternalAPIAccess.tsx` (جدید)
- [ ] `admin-panel/src/services/api.ts` (اضافه کردن API calls)
- [ ] `admin-panel/src/App.tsx` یا `Router.tsx` (اضافه کردن route)
- [ ] `admin-panel/src/components/Sidebar.tsx` (اضافه کردن منو)

**زمان تخمینی**: 3-4 ساعت

---

### 2. خطا در پردازش درخواست External API
**مشکل**: درخواست‌های ارسال شده به خطا می‌خورند.

**بررسی لازم**:
- [ ] چک کردن لاگ‌های response-network celery-worker
- [ ] بررسی `execute_query.py` برای external_api
- [ ] تست کردن API key صحیح است یا نه
- [ ] بررسی format پارامترها درست است یا نه

**دستورات بررسی**:
```bash
# لاگ worker
ssh response@192.168.214.141 "docker compose -f /home/response/response-network/docker-compose.yml logs celery-worker --tail 100"

# لاگ API
ssh response@192.168.214.141 "docker compose -f /home/response/response-network/docker-compose.yml logs api --tail 100"

# بررسی درخواست‌ها
curl -H "Authorization: Bearer TOKEN" "http://192.168.214.141:8000/api/v1/admin/requests?limit=10"
```

**احتمال خطا**:
1. API key اشتباه است
2. Format base64 اشتباه است
3. External API handler مشکل دارد
4. Payload template اشتباه است

**زمان تخمینی**: 1-2 ساعت

---

### 3. عدم تفکیک درخواست‌های Elasticsearch و External API
**مشکل**: در صفحه درخواست‌های Response Network نمی‌توان تشخیص داد کدام Elasticsearch و کدام External API است.

**راه‌حل Backend**:
```python
# در response-network/api/crud/requests.py
# اضافه کردن فیلد is_external_api به response

def get_requests(...):
    # ...
    item = {
        # ...
        "is_external_api": r.query_type == "external_api",
        "api_name": r.query_params.get("api_type") if r.query_type == "external_api" else None,
    }
```

**راه‌حل Frontend**:
```typescript
// در admin-panel/src/pages/Requests.tsx
// اضافه کردن badge یا icon برای تفکیک

{request.is_external_api ? (
  <Badge color="purple">External API: {request.api_name}</Badge>
) : (
  <Badge color="blue">Elasticsearch</Badge>
)}
```

**فایل‌های نیاز به تغییر**:
- [ ] `response-network/api/crud/requests.py`
- [ ] `response-network/admin-panel/src/pages/Requests.tsx`
- [ ] `response-network/admin-panel/src/types/request.ts` (اضافه کردن type)

**زمان تخمینی**: 1 ساعت

---

## 📋 TODO به ترتیب اولویت

### مرحله 1: رفع خطای پردازش (بحرانی)
**اولویت**: 🔴 بالا
**زمان**: 1-2 ساعت

- [ ] بررسی لاگ‌های worker
- [ ] شناسایی دقیق خطا
- [ ] رفع خطا در execute_query.py یا external_api_handler.py
- [ ] تست مجدد با یک درخواست ساده

### مرحله 2: تفکیک درخواست‌ها در UI
**اولویت**: 🟡 متوسط
**زمان**: 1 ساعت

- [ ] اضافه کردن `is_external_api` و `api_name` به backend response
- [ ] اضافه کردن badge/icon در frontend
- [ ] تست UI

### مرحله 3: صفحه مدیریت دسترسی
**اولویت**: 🟢 پایین (چون backend کار می‌کند و می‌توان با curl مدیریت کرد)
**زمان**: 3-4 ساعت

- [ ] ساخت صفحه ExternalAPIAccess.tsx
- [ ] اضافه کردن API calls
- [ ] اضافه کردن route
- [ ] اضافه کردن منو
- [ ] تست کامل

---

## 🔍 بررسی فوری لازم

### چک کردن وضعیت درخواست OCR
```bash
# لاگ worker
ssh response@192.168.214.141 "docker compose -f /home/response/response-network/docker-compose.yml logs celery-worker --tail 50 | grep -i ocr"

# لاگ API
ssh response@192.168.214.141 "docker compose -f /home/response/response-network/docker-compose.yml logs api --tail 50 | grep -i external"

# بررسی درخواست در database
ssh response@192.168.214.141 "docker compose -f /home/response/response-network/docker-compose.yml exec -T postgres psql -U postgres -d response_network -c \"SELECT id, status, query_type, error_message FROM incoming_requests WHERE query_type='external_api' ORDER BY created_at DESC LIMIT 5;\""
```

### تست API Key
```bash
# تست مستقیم OCR.space API
curl -X POST "https://api.ocr.space/parse/image" \
  -H "apikey: K82850920188957" \
  -H "Content-Type: application/json" \
  -d '{"base64Image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mNk+M9Qz0AEYBxVSF+FABJADveWkH6oAAAAAElFTkSuQmCC", "language": "eng"}'
```

---

## 📊 وضعیت کلی

| بخش | وضعیت | توضیح |
|-----|-------|-------|
| Backend Response | ⚠️ نیمه‌کامل | API ها موجود اما execute با خطا |
| Backend Request | ✅ کامل | Endpoint کار می‌کند |
| Frontend Response | ❌ ناقص | صفحه مدیریت دسترسی ندارد |
| Frontend Request | ✅ کامل | می‌توان درخواست فرستاد |
| Execute Query | ❌ خطا | نیاز به debug |
| Export/Import | ✅ کامل | کار می‌کند |

---

## 🎯 هدف نهایی

یک سیستم کامل External API که:
1. ✅ کاربر بتواند درخواست بفرستد (کار می‌کند)
2. ❌ درخواست پردازش شود (خطا دارد)
3. ❌ Admin بتواند دسترسی مدیریت کند (UI ندارد)
4. ❌ درخواست‌ها قابل تفکیک باشند (UI ندارد)

---

## ⏱️ زمان کل تخمینی

- رفع خطا: 1-2 ساعت
- تفکیک UI: 1 ساعت
- صفحه مدیریت: 3-4 ساعت
- تست و debug: 1 ساعت

**جمع**: 6-8 ساعت کار

---

## 🚨 نکته مهم

**قبل از ادامه کار روی UI، باید خطای execute را رفع کنیم!**
بدون execute کار، بقیه کارها بی‌فایده است.
