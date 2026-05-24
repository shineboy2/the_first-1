# تحلیل طراحی External API

## وضعیت فعلی

### مشکلات موجود:

1. **دو endpoint جدا**:
   - `/requests` برای Elasticsearch queries
   - `/external-request/{api_name}` برای External APIs
   - کاربر باید بداند کدام را استفاده کند

2. **نیاز به آپلود فایل**:
   - External API endpoint فقط `UploadFile` می‌پذیرد
   - کاربر نمی‌تواند base64 مستقیم بفرستد
   - برای API call از frontend مشکل‌ساز است

3. **عدم یکپارچگی**:
   - Request Types و External APIs جدا مدیریت می‌شوند
   - دو سیستم دسترسی جدا
   - دو endpoint جدا

## راه‌حل‌های ممکن

### گزینه 1: یکپارچه‌سازی کامل (پیشنهاد شده) ✅

**ایده**: External API ها را مثل Request Type رفتار کنیم

#### تغییرات لازم:

1. **Request-Network**:
   - حذف `/external-request` endpoint
   - اضافه کردن پشتیبانی از `external_api` در `/requests` endpoint
   - تشخیص خودکار: اگر `query_type` با `external_api:` شروع شود → external API
   - مثال: `query_type: "external_api:ocr_space"`

2. **Response-Network**:
   - External API ها را به عنوان Request Type ثبت کنیم
   - `name`: `external_api:ocr_space`
   - `is_external`: `true` (فیلد جدید)
   - همان سیستم دسترسی Profile Type Access

3. **مزایا**:
   - ✅ یک endpoint واحد
   - ✅ یک سیستم دسترسی
   - ✅ کاربر نیازی به تشخیص ندارد
   - ✅ Frontend ساده‌تر می‌شود
   - ✅ پشتیبانی از JSON و base64 مستقیم

4. **معایب**:
   - ❌ نیاز به migration برای اضافه کردن فیلد `is_external`
   - ❌ تغییر در execute_query برای تشخیص
   - ❌ تغییر در frontend

### گزینه 2: بهبود External Request Endpoint (ساده‌تر)

**ایده**: External Request endpoint را بهبود بدهیم تا JSON هم بپذیرد

#### تغییرات لازم:

1. **Request-Network**:
   - اضافه کردن overload به `/external-request/{api_name}`
   - پذیرش هم `UploadFile` و هم JSON با base64
   - استفاده از `Union[UploadFile, dict]`

2. **مزایا**:
   - ✅ تغییرات کمتر
   - ✅ سریع‌تر پیاده‌سازی می‌شود
   - ✅ backward compatible

3. **معایب**:
   - ❌ همچنان دو endpoint جدا
   - ❌ کاربر باید بداند کدام را استفاده کند
   - ❌ دو سیستم دسترسی جدا

### گزینه 3: Hybrid (ترکیبی)

**ایده**: هر دو endpoint را نگه داریم اما `/requests` را هوشمند کنیم

#### تغییرات لازم:

1. **Request-Network `/requests`**:
   - اگر `query_type` با `external_api:` شروع شود → redirect به external handler
   - اگر نه → Elasticsearch query

2. **Request-Network `/external-request`**:
   - برای backward compatibility نگه داریم
   - فقط برای آپلود فایل

3. **مزایا**:
   - ✅ backward compatible
   - ✅ انعطاف‌پذیر
   - ✅ کاربر می‌تواند هر دو را استفاده کند

4. **معایب**:
   - ❌ پیچیدگی بیشتر
   - ❌ دو راه برای یک کار

## تصمیم نهایی: گزینه 2 (بهبود External Request)

**چرا؟**
1. سریع‌تر پیاده‌سازی می‌شود
2. تغییرات کمتر
3. ریسک کمتر برای سیستم موجود
4. می‌توانیم بعداً به گزینه 1 مهاجرت کنیم

## طراحی نهایی

### Endpoint: `/external-request/{api_name}`

#### روش 1: آپلود فایل (موجود)
```bash
curl -X POST "http://server/api/v1/external-request/ocr_space" \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@image.png"
```

#### روش 2: JSON با base64 (جدید)
```bash
curl -X POST "http://server/api/v1/external-request/ocr_space" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "request_name": "my_ocr_request",
    "base64Image": "data:image/png;base64,iVBORw0KG...",
    "language": "eng"
  }'
```

### تغییرات کد:

```python
from pydantic import BaseModel
from typing import Optional

class ExternalAPIRequest(BaseModel):
    request_name: Optional[str] = None
    base64Image: str  # data:image/png;base64,xxxxx
    language: Optional[str] = "eng"
    # سایر پارامترها...

@router.post("/{api_name}")
async def submit_external_request(
    api_name: str,
    file: Optional[UploadFile] = File(None),
    json_data: Optional[ExternalAPIRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    # اگر file آمد → از file استفاده کن
    # اگر json_data آمد → از base64 استفاده کن
    # اگر هیچکدام نیامد → خطا
```

### مزایا این طراحی:
1. ✅ هم file upload و هم JSON پشتیبانی می‌شود
2. ✅ Frontend می‌تواند مستقیم base64 بفرستد
3. ✅ تغییرات minimal
4. ✅ backward compatible
5. ✅ تست آسان با curl

### نکات پیاده‌سازی:
1. بررسی کنیم که یا `file` یا `json_data` ارسال شده باشد (نه هر دو، نه هیچکدام)
2. اگر `base64Image` با `data:image/...;base64,` شروع شود → prefix را حذف کنیم
3. محدودیت حجم را برای هر دو روش اعمال کنیم
4. validation برای format base64

## مراحل پیاده‌سازی

### مرحله 1: Backend (30 دقیقه)
- [ ] اضافه کردن schema `ExternalAPIRequest`
- [ ] تغییر endpoint برای پذیرش JSON
- [ ] تست با curl

### مرحله 2: تست (15 دقیقه)
- [ ] تست با file upload
- [ ] تست با JSON + base64
- [ ] تست validation و error handling

### مرحله 3: مستندسازی (15 دقیقه)
- [ ] به‌روزرسانی API docs
- [ ] نمونه curl commands

**زمان کل: 1 ساعت**
