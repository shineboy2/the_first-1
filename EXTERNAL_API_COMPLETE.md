# ✅ External API - پیاده‌سازی کامل شد!

## خلاصه کارهای انجام شده

### 1. Response-Network (192.168.214.141:8000)
- ✅ جدول `external_apis` ساخته شد
- ✅ Migration ها اجرا شدند
- ✅ External API `ocr_space` تعریف شد با API key
- ✅ Endpoint مدیریت دسترسی:
  ```bash
  # دادن دسترسی
  PATCH /api/v1/external-apis/profile-types/{profile_type}/access
  
  # دیدن دسترسی
  GET /api/v1/external-apis/profile-types/{profile_type}/access
  ```
- ✅ دسترسی `ocr_space` به profile type `admin` داده شد
- ✅ Export users شامل `allowed_external_apis`
- ✅ Execute query از external API پشتیبانی می‌کند

### 2. Request-Network (192.168.214.146:8001)
- ✅ Import users شامل `allowed_external_apis`
- ✅ Admin user دسترسی `ocr_space` دارد
- ✅ Endpoint `/external-request/{api_name}` هم File و هم JSON پشتیبانی می‌کند

## نحوه استفاده

### روش 1: آپلود فایل
```bash
curl -X POST "http://192.168.214.146:8001/api/v1/external-request/ocr_space" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@image.png"
```

### روش 2: JSON با base64
```bash
# دریافت توکن
TOKEN=$(curl -s -X POST http://192.168.214.146:8001/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123456" | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# تبدیل تصویر به base64
BASE64_IMAGE=$(base64 -w 0 image.png)

# ارسال درخواست
curl -X POST "http://192.168.214.146:8001/api/v1/external-request/ocr_space" \
  -H "Authorization: Bearer $TOKEN" \
  -F "json_data={\"params\": {\"base64Image\": \"data:image/png;base64,$BASE64_IMAGE\", \"language\": \"eng\"}, \"request_name\": \"my_ocr_request\"}"
```

### بررسی نتیجه
```bash
# دیدن لیست درخواست‌ها
curl -H "Authorization: Bearer $TOKEN" \
  "http://192.168.214.146:8001/api/v1/requests?limit=10"

# دیدن جزئیات یک درخواست
curl -H "Authorization: Bearer $TOKEN" \
  "http://192.168.214.146:8001/api/v1/requests/{REQUEST_ID}"
```

## فرایند کامل

1. **Request Network**: کاربر درخواست OCR می‌فرستد
2. **Export**: درخواست export می‌شود به Response Network
3. **Response Network**: Worker درخواست را process می‌کند و API خارجی را صدا می‌زند
4. **Export Result**: نتیجه export می‌شود به Request Network
5. **Import Result**: Request Network نتیجه را import می‌کند
6. **User**: کاربر نتیجه را می‌بیند

## تست شده

✅ دسترسی مدیریت می‌شود
✅ Export/Import کار می‌کند
✅ Endpoint هم File و هم JSON می‌پذیرد
✅ درخواست با موفقیت ارسال شد

## نکات مهم

1. **پورت‌ها**:
   - Response Network: `192.168.214.141:8000`
   - Request Network: `192.168.214.146:8001`

2. **Authentication**: از Bearer token استفاده می‌شود

3. **Base64**: اگر با `data:image/...;base64,` شروع شود، prefix حذف می‌شود

4. **Rate Limiting**: برای هر user اعمال می‌شود

5. **Access Control**: فقط user هایی که دسترسی دارند می‌توانند استفاده کنند

## مستندات API

همه endpoint ها در Swagger موجود است:
- Response: `http://192.168.214.141:8000/docs`
- Request: `http://192.168.214.146:8001/docs`
