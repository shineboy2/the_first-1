# TODO: مدیریت دسترسی External API ها

## وضعیت فعلی
- ✅ جدول `external_apis` در response-network ساخته شده
- ✅ External API `ocr_space` تعریف شده
- ✅ فیلد `allowed_external_apis` در User model (هر دو شبکه) وجود دارد
- ✅ مکانیزم execute_query برای external_api کار می‌کند
- ✅ Export/Import نتایج external API کار می‌کند

## مشکل فعلی
**دسترسی External API ها مدیریت نمی‌شود!**

کاربران نمی‌توانند از External API ها استفاده کنند چون:
1. در response-network: دسترسی به profile type ها داده نمی‌شود
2. در request-network: endpoint برای ارسال درخواست external API وجود دارد اما دسترسی چک نمی‌شود

## راه‌حل پیشنهادی

### گزینه 1: مدیریت دسترسی مشابه Request Types (پیشنهاد شده)

#### Backend (Response Network):
1. **Model**: از `ProfileTypeConfig.permissions["allowed_external_apis"]` استفاده کنیم (موجود است)
2. **Router**: endpoint های زیر را به `response-network/api/routers/external_apis.py` اضافه کنیم:
   ```python
   PATCH /api/v1/external-apis/profile-types/{profile_type}/access
   GET /api/v1/external-apis/profile-types/{profile_type}/access
   ```
3. **Export**: در `users_exporter.py` فیلد `allowed_external_apis` را از profile type بخوانیم و export کنیم (قبلاً انجام شده)

#### Backend (Request Network):
1. **Validation**: در `request-network/api/routers/external_request.py` چک کنیم:
   ```python
   if not current_user.is_external_api_allowed(api_name):
       raise HTTPException(403, "Access denied")
   ```
   (این قبلاً وجود دارد - خط 42)

2. **Import**: در `users_importer.py` فیلد `allowed_external_apis` را import کنیم (قبلاً انجام شده)

#### Frontend (Response Network Admin Panel):
1. **صفحه جدید**: `admin-panel/src/pages/ExternalAPIAccess.tsx`
   - لیست External API ها
   - لیست Profile Types
   - Matrix برای تنظیم دسترسی (مشابه Request Type Access)

2. **منو**: اضافه کردن لینک به منوی admin panel

3. **API Client**: اضافه کردن endpoint ها به `admin-panel/src/services/api.ts`

#### Frontend (Request Network User Panel):
1. **صفحه External Request**: `user-panel/src/pages/ExternalRequest.tsx`
   - فرم برای انتخاب External API
   - فیلدهای dynamic بر اساس API انتخاب شده
   - آپلود فایل و تبدیل به base64
   - ارسال درخواست

2. **منو**: اضافه کردن لینک به منوی user panel

### گزینه 2: مدیریت دسترسی با جدول جداگانه (پیچیده‌تر)

#### Backend (Response Network):
1. **Model جدید**: `ProfileTypeExternalAPIAccess` (مشابه `ProfileTypeRequestAccess`)
2. **Migration**: ساخت جدول
3. **Router**: endpoint های CRUD برای مدیریت دسترسی
4. **Export**: خواندن از جدول و export کردن

#### Backend (Request Network):
1. **Model جدید**: `UserExternalAPIAccess` (اگر نیاز باشد)
2. **Import**: import کردن دسترسی‌ها از response network

## تصمیم نهایی
**گزینه 1 را انتخاب می‌کنیم** چون:
- ساده‌تر است
- از ساختار موجود استفاده می‌کند
- نیاز به migration ندارد
- سریع‌تر پیاده‌سازی می‌شود

## مراحل اجرا (به ترتیب اولویت)

### مرحله 1: Backend Response Network
- [ ] اضافه کردن endpoint های مدیریت دسترسی به `external_apis.py`
- [ ] تست endpoint ها با curl
- [ ] بررسی export در `users_exporter.py` (باید کار کند)

### مرحله 2: Backend Request Network  
- [ ] بررسی validation در `external_request.py` (باید کار کند)
- [ ] بررسی import در `users_importer.py` (باید کار کند)
- [ ] تست end-to-end: دسترسی بدهیم و درخواست بفرستیم

### مرحله 3: Frontend Response Network
- [ ] ساخت صفحه `ExternalAPIAccess.tsx`
- [ ] اضافه کردن به منو
- [ ] اضافه کردن API client functions
- [ ] تست UI

### مرحله 4: Frontend Request Network
- [ ] ساخت صفحه `ExternalRequest.tsx`
- [ ] اضافه کردن به منو
- [ ] پیاده‌سازی آپلود فایل و base64 encoding
- [ ] تست UI

### مرحله 5: تست کامل
- [ ] دادن دسترسی ocr_space به profile type admin
- [ ] sync کردن users
- [ ] ارسال درخواست OCR از request network
- [ ] بررسی نتیجه

## نکات مهم
1. **فیلد `allowed_external_apis` قبلاً در User model وجود دارد** - نیاز به migration نیست
2. **Export/Import قبلاً پیاده‌سازی شده** - فقط باید تست کنیم
3. **Validation در request-network وجود دارد** - فقط باید فعال باشد
4. **فقط UI و endpoint های مدیریت دسترسی کم است**

## فایل‌های تغییر یافته (که باید revert شوند)
- ❌ `request-network/api/routers/user_management_router.py` - این تغییر لازم نبود! باید revert شود
- ✅ `response-network/api/routers/external_apis.py` - این تغییر درست است اما باید تست شود

## زمان تخمینی
- Backend: 2 ساعت
- Frontend Response: 3 ساعت  
- Frontend Request: 4 ساعت
- تست: 1 ساعت
- **جمع: 10 ساعت**
