# طرح استقرار و تست عملیاتی آژانس هواپیمایی (Airline Agency E2E Plan)

با توجه به توضیحات شما، سیستم را برای شبیه‌سازی دقیق عملیات کارمندان آژانس هواپیمایی آماده می‌کنیم. در این سناریو، کارمندان به جای مسافران، درخواست‌های رزرو و صدور بلیط را ثبت می‌کنند.

## User Review Required

> [!IMPORTANT]
> - نقش "Passenger" حذف و نقش‌هایی مانند `Sales_Agent` و `IT_Manager` جایگزین می‌شوند.
> - درخواست‌های تستی شامل فیلدهایی مثل PNR، شماره پرواز و اطلاعات مسافر (نام و کد ملی) خواهد بود که توسط کارمند پر می‌شود.
> - برای تست دقیق، رمز عبور ادمین در هر دو شبکه به `admin123456` تنظیم خواهد شد.

## Proposed Changes

### 1. اصلاحات زیرساختی (Infrastructure Fixes)

#### [MODIFY] [main.py](file:///home/docker/the_first/the_first/response-network/api/main.py)
- تغییر مکانیزم لود Swagger UI به حالت Offline (استفاده از فایل‌های محلی در `/static/`) برای رفع مشکل عدم نمایش در محیط ایزوله.

#### [NEW] [custom_swagger.py](file:///home/docker/the_first/the_first/response-network/api/custom_swagger.py)
- ایجاد ماژول کمکی برای تولید HTML صفحه Swagger با آدرس‌های محلی.

### 2. سناریوی داده‌ای آژانس (Agency Data Scenario)
من از طریق API دستورات زیر را برای آماده‌سازی محیط "واقعی" اجرا می‌کنم:

- **تعریف نقش‌ها (Profile Types)**:
  - `Sales_Agent`: دسترسی به ثبت رزرو.
  - `Agency_Manager`: دسترسی به گزارشات و تاییدات.
- **تعریف نوع درخواست (Request Type)**:
  - `Flight_Booking_Order`: شامل پارامترهای (Passenger_Name, Passport_ID, Flight_Number, PNR).
- **ایجاد کاربر عملیاتی**:
  - ساخت یک کاربر با نقش `Sales_Agent` برای تست ثبت درخواست.

### 3. چرخه تست نهایی (End-to-End Test Loop)
1. **Login**: ورود ادمین و دریافت توکن.
2. **Setup**: ایجاد نقش‌ها و نوع درخواست بالا در نود Response.
3. **Sync**: انتقال تنظیمات آژانس به نود Request از طریق FTP.
4. **Transaction**:
   - ثبت یک "Flight Booking" توسط کارمند در نود Request.
   - انتقال درخواست به نود Response.
   - پردازش و بازگشت نتیجه (مثلاً Status: Issued).

## Verification Plan

### Automated Tests
- تست صحت نمایش خروجی `/api/v1/openapi.json` پس از تغییرات Swagger.
- بررسی وجود فایل‌های JSONL در پوشه‌های `/srv/ftp/settings` و `/srv/ftp/requests`.

### Manual Verification
- تایید نمایش Swagger UI در شبکه پاسخ.
- ورود به پنل ادمین با هویت کارمند آژانس و مشاهده فرم داینامیک رزرو بلیط.
