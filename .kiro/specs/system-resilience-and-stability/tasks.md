# طرح پیاده‌سازی: پایداری و استحکام سامانه

## مرور کلی

این طرح پیاده‌سازی برای ایجاد یک معماری مقاوم در برابر قطع دسترسی به سرویس‌های خارجی حیاتی (FTP، Elasticsearch، Redis) است. پیاده‌سازی در ۷ فاز طی ۸ هفته انجام می‌شود و شامل Circuit Breaker، Retry Handler، Queue Management، In-Memory Rate Limiter، و سیستم‌های مانیتورینگ است.

## وظایف

- [ ] ۱. فاز ۱: پایه‌گذاری - ایجاد کامپوننت‌های اصلی و مدل‌های داده
  - [ ] ۱.۱ ایجاد مدل‌های داده جدید و migration های دیتابیس
    - ایجاد جدول CircuitBreakerState برای ذخیره وضعیت circuit breaker ها
    - ایجاد جدول ServiceHealthHistory برای تاریخچه سلامت سرویس‌ها
    - ایجاد جدول QueuedItem برای مدیریت صف‌های محلی
    - ایجاد جدول RateLimitCounter برای fallback rate limiting
    - به‌روزرسانی مدل Request با فیلدهای error_type، estimated_recovery_time، retry_count
    - به‌روزرسانی مدل IncomingRequest با فیلدهای queued_at، last_retry_at
    - _الزامات: ۱.۷، ۱.۸، ۴.۱، ۵.۷_

  - [ ] ۱.۲ پیاده‌سازی Circuit Breaker کامپوننت
    - ایجاد کلاس CircuitBreaker با state machine (CLOSED/OPEN/HALF_OPEN)
    - پیاده‌سازی منطق failure threshold و timeout
    - پیاده‌سازی decorator pattern برای سهولت استفاده
    - ذخیره وضعیت در دیتابیس برای persistence
    - _الزامات: ۲.۳، ۳.۳، ۴.۳_

  - [ ]* ۱.۳ نوشتن تست‌های property برای Circuit Breaker
    - **خصوصیت ۴: Circuit Breaker State Machine**
    - **اعتبارسنجی الزامات: ۲.۳، ۲.۶، ۳.۳، ۳.۶، ۴.۳**

  - [ ] ۱.۴ پیاده‌سازی Retry Handler با Exponential Backoff
    - ایجاد کلاس RetryHandler با پیکربندی قابل تنظیم
    - پیاده‌سازی الگوریتم Exponential Backoff با jitter
    - محاسبه تاخیر بر اساس فرمول: delay = min(initial_delay * (base ** attempt), max_delay)
    - _الزامات: ۲.۱، ۲.۲، ۳.۱، ۳.۲، ۴.۲، ۵.۸_

  - [ ]* ۱.۵ نوشتن تست‌های property برای Retry Handler
    - **خصوصیت ۳: Retry Handler Exhaustion**
    - **اعتبارسنجی الزامات: ۲.۱، ۲.۲، ۳.۱، ۳.۲، ۴.۲، ۵.۸**

  - [ ] ۱.۶ پیاده‌سازی Health Check Service
    - ایجاد کلاس HealthCheckService برای مانیتورینگ سرویس‌ها
    - پیاده‌سازی health checker های مخصوص FTP، Elasticsearch، Redis
    - اجرای بررسی‌های دوره‌ای هر ۳۰ ثانیه
    - ثبت نتایج در ServiceHealthHistory
    - _الزامات: ۱.۱، ۱.۲، ۱.۳، ۱.۴_

  - [ ]* ۱.۷ نوشتن تست‌های property برای Health Check
    - **خصوصیت ۱: Health Check State Transition**
    - **خصوصیت ۲: Health Check Metadata Recording**
    - **اعتبارسنجی الزامات: ۱.۵، ۱.۶، ۱.۷، ۱.۸**

- [ ] ۲. نقطه بررسی - اطمینان از عملکرد صحیح کامپوننت‌های پایه
  - اطمینان از پاس شدن تمام تست‌ها، در صورت بروز سوال با کاربر مشورت کنید.

- [ ] ۳. فاز ۲: مدیریت FTP - پیاده‌سازی resilience برای سرویس‌های FTP
  - [ ] ۳.۱ پیاده‌سازی Local Storage Manager
    - ایجاد کلاس LocalStorageManager برای ذخیره فایل‌ها در استوریج محلی
    - پیاده‌سازی متدهای save_file، list_files، get_file، delete_file
    - ایجاد ساختار دایرکتوری /app/local_storage/requests و /app/local_storage/results
    - محدودیت حداکثر ۱۰۰۰ فایل در هر نوع استوریج
    - _الزامات: ۲.۴، ۲.۸، ۳.۴، ۳.۸_

  - [ ]* ۳.۲ نوشتن تست‌های property برای Local Storage
    - **خصوصیت ۵: Local Storage Fallback**
    - **اعتبارسنجی الزامات: ۲.۴، ۲.۹، ۳.۴، ۳.۹**

  - [ ] ۳.۳ یکپارچه‌سازی Circuit Breaker با عملیات FTP
    - اضافه کردن circuit breaker به تابع upload_to_ftp در export_requests.py
    - اضافه کردن circuit breaker به تابع download_from_ftp در import_results.py
    - پیاده‌سازی fallback به local storage در صورت باز بودن circuit
    - _الزامات: ۲.۳، ۲.۴، ۳.۳، ۳.۴_

  - [ ] ۳.۴ پیاده‌سازی Auto-Recovery برای FTP
    - ایجاد کلاس FTPRecoveryService برای بازیابی خودکار
    - پیاده‌سازی پردازش فایل‌های ذخیره شده با rate limiting
    - حداکثر ۱۰ فایل در ثانیه برای جلوگیری از اضافه‌بار
    - حذف فایل‌ها پس از پردازش موفق
    - _الزامات: ۲.۷، ۲.۹، ۳.۷، ۳.۹، ۹.۱، ۹.۲_

  - [ ]* ۳.۵ نوشتن تست‌های property برای Queue-Based Recovery
    - **خصوصیت ۶: Queue-Based Recovery**
    - **اعتبارسنجی الزامات: ۲.۷، ۳.۷، ۴.۸، ۹.۱، ۹.۲، ۹.۳**

  - [ ]* ۳.۶ نوشتن تست‌های یکپارچگی برای FTP resilience
    - تست سناریوی کامل قطع و بازیابی Request_FTP
    - تست سناریوی کامل قطع و بازیابی Response_FTP
    - تست ذخیره و بازیابی فایل‌ها از local storage

- [ ] ۴. فاز ۳: مدیریت Elasticsearch - پیاده‌سازی resilience برای Elasticsearch
  - [ ] ۴.۱ پیاده‌سازی Queue Manager
    - ایجاد کلاس QueueManager برای مدیریت صف‌های محلی
    - پیاده‌سازی متدهای enqueue، dequeue، peek، get_size
    - استفاده از جدول QueuedItem برای persistence
    - اولویت‌بندی بر اساس priority و created_at
    - حداکثر ۵۰۰۰ درخواست در صف Elasticsearch
    - _الزامات: ۴.۱، ۴.۱۱_

  - [ ]* ۴.۲ نوشتن تست‌های property برای Queue Priority
    - **خصوصیت ۱۰: Queue Priority Ordering**
    - **اعتبارسنجی الزامات: ۴.۸، ۹.۵**

  - [ ] ۴.۳ پیاده‌سازی Error File Generator
    - ایجاد کلاس ErrorFileGenerator برای تولید فایل‌های خطا
    - تولید فایل JSON با اطلاعات خطا، زمان تخمینی بازیابی، و موقعیت صف
    - پشتیبانی از انواع خطای مختلف: service_unavailable، system_busy
    - _الزامات: ۴.۴، ۴.۵_

  - [ ] ۴.۴ یکپارچه‌سازی با Execute Query Task
    - اضافه کردن circuit breaker به تابع execute_elasticsearch_query
    - پیاده‌سازی fallback به queue در صورت باز بودن circuit
    - تولید و ارسال فایل خطا به Request_Network
    - _الزامات: ۴.۱، ۴.۳، ۴.۴_

  - [ ]* ۴.۵ نوشتن تست‌های property برای Elasticsearch Queue
    - **خصوصیت ۷: Elasticsearch Queue and Error File**
    - **اعتبارسنجی الزامات: ۴.۱، ۴.۴**

  - [ ] ۴.۶ پیاده‌سازی Queue Processor
    - ایجاد task پردازش صف Elasticsearch با rate limiting
    - پردازش درخواست‌ها به ترتیب اولویت
    - ارسال نتایج واقعی به Request_Network پس از بازگشت سرویس
    - _الزامات: ۴.۸، ۴.۹، ۹.۳_

  - [ ] ۴.۷ به‌روزرسانی وضعیت درخواست‌ها در Request_Network
    - پیاده‌سازی منطق تشخیص فایل‌های خطا در import_results.py
    - به‌روزرسانی وضعیت به "service_unavailable" برای فایل‌های خطا
    - به‌روزرسانی وضعیت به "completed" برای نتایج واقعی
    - _الزامات: ۴.۶، ۴.۱۰_

  - [ ]* ۴.۸ نوشتن تست‌های property برای Status Updates
    - **خصوصیت ۸: Error File Status Update**
    - **خصوصیت ۹: Success Result Status Update**
    - **اعتبارسنجی الزامات: ۴.۶، ۴.۱۰**

- [ ] ۵. نقطه بررسی - تست عملکرد Elasticsearch resilience
  - اطمینان از عملکرد صحیح صف، error file generation، و status updates، در صورت بروز سوال با کاربر مشورت کنید.

- [ ] ۶. فاز ۴: مدیریت Redis - پیاده‌سازی In-Memory Rate Limiter و fallback
  - [ ] ۶.۱ پیاده‌سازی In-Memory Rate Limiter
    - ایجاد کلاس InMemoryRateLimiter با الگوریتم Sliding Window
    - پیاده‌سازی متدهای is_allowed، get_remaining، reset
    - استفاده از ساختار داده deque برای نگهداری تاریخچه درخواست‌ها
    - اعمال همان محدودیت‌های نرخ Redis
    - _الزامات: ۵.۳، ۵.۴_

  - [ ]* ۶.۲ نوشتن تست‌های property برای Rate Limiter
    - **خصوصیت ۱۱: In-Memory Rate Limiter Activation**
    - **خصوصیت ۱۲: Rate Limiter Equivalence**
    - **اعتبارسنجی الزامات: ۵.۲، ۵.۳، ۵.۴**

  - [ ] ۶.۳ پیاده‌سازی Redis Fallback Handler
    - ایجاد کلاس RedisFallbackHandler برای مدیریت تغییر حالت
    - تشخیص خودکار قطع Redis و فعال‌سازی In-Memory
    - ثبت هشدار در لاگ هنگام تغییر به حالت In-Memory
    - _الزامات: ۵.۱، ۵.۲، ۵.۵_

  - [ ] ۶.۴ یکپارچه‌سازی با Rate Limiting Middleware
    - تغییر middleware موجود برای استفاده از fallback handler
    - حفظ شفافیت برای کاربران نهایی
    - _الزامات: ۵.۱، ۵.۲_

  - [ ] ۶.۵ پیاده‌سازی همگام‌سازی با Redis
    - پیاده‌سازی متد sync_to_redis برای انتقال شمارنده‌های محلی
    - بازگشت تدریجی به Redis پس از بازیابی سرویس
    - حفظ تداوم محدودسازی نرخ
    - _الزامات: ۵.۶، ۵.۷_

  - [ ]* ۶.۶ نوشتن تست‌های property برای Redis Recovery
    - **خصوصیت ۱۳: Rate Limiter Recovery and Sync**
    - **اعتبارسنجی الزامات: ۵.۶، ۵.۷**

  - [ ] ۶.۷ پیاده‌سازی Cache Fallback
    - غیرفعال‌سازی عملیات cache در صورت قطع Redis
    - دسترسی مستقیم به منبع داده
    - _الزامات: ۵.۱۰_

  - [ ]* ۶.۸ نوشتن تست‌های property برای Cache Fallback
    - **خصوصیت ۱۴: Cache Fallback**
    - **اعتبارسنجی الزامات: ۵.۱۰**

- [ ] ۷. فاز ۵: مانیتورینگ و متریک‌ها - پیاده‌سازی metrics، logging، و alerting
  - [ ] ۷.۱ پیاده‌سازی Prometheus Metrics
    - تعریف تمام متریک‌های مورد نیاز: circuit_breaker_state، service_health_status، queue_size
    - متریک‌های retry_attempts، recovery_duration، rate_limiter_mode
    - expose کردن متریک‌ها در endpoint /metrics
    - _الزامات: ۶.۶، ۱۱.۱، ۱۱.۲، ۱۱.۳، ۱۱.۴، ۱۱.۵، ۱۱.۶، ۱۱.۷_

  - [ ] ۷.۲ پیاده‌سازی Structured Logging
    - ایجاد کلاس ResilienceLogger برای لاگ‌گذاری ساختاریافته
    - لاگ‌گذاری رویدادهای circuit breaker، retry، recovery
    - استفاده از فرمت JSON برای لاگ‌ها
    - _الزامات: ۶.۱، ۶.۲، ۶.۳، ۶.۴_

  - [ ] ۷.۳ ایجاد Grafana Dashboards
    - Dashboard برای Service Health Overview
    - Dashboard برای Circuit Breaker Status
    - Dashboard برای Queue Monitoring
    - Dashboard برای Rate Limiting
    - Dashboard برای Recovery Metrics

  - [ ] ۷.۴ تنظیم Alerting Rules
    - Alert برای ServiceDown (سرویس بیش از ۵ دقیقه از کار افتاده)
    - Alert برای CircuitBreakerOpen (circuit بیش از ۱۰ دقیقه باز)
    - Alert برای QueueNearlyFull (صف بیش از ۸۰٪ پر)
    - Alert برای HighRetryRate و InMemoryRateLimiterActive
    - _الزامات: ۶.۵، ۵.۹_

- [ ] ۸. فاز ۶: Backpressure و بهینه‌سازی - پیاده‌سازی backpressure و gradual recovery
  - [ ] ۸.۱ پیاده‌سازی Backpressure Handler
    - ایجاد کلاس BackpressureHandler برای کنترل اضافه‌بار
    - بررسی ظرفیت صف‌ها و تصمیم‌گیری برای throttling
    - محاسبه زمان تخمینی برای تلاش مجدد
    - _الزامات: ۱۰.۱، ۱۰.۲، ۱۰.۳، ۱۰.۴_

  - [ ]* ۸.۲ نوشتن تست‌های property برای Backpressure
    - **خصوصیت ۱۵: Backpressure Throttling**
    - **اعتبارسنجی الزامات: ۱۰.۱، ۱۰.۲، ۱۰.۳**

  - [ ] ۸.۳ یکپارچه‌سازی Backpressure با API Endpoints
    - اضافه کردن بررسی backpressure به endpoint های اصلی
    - برگرداندن پیام "سامانه مشغول" با retry_after
    - _الزامات: ۱۰.۳، ۱۰.۴_

  - [ ] ۸.۴ پیاده‌سازی Gradual Recovery Service
    - ایجاد کلاس GradualRecoveryService برای بازیابی تدریجی
    - محاسبه نرخ پردازش بر اساس اندازه صف و سلامت سرویس
    - افزایش تدریجی نرخ پردازش
    - حداکثر ۱۰ درخواست در ثانیه
    - _الزامات: ۱۰.۵، ۱۰.۷، ۹.۶_

  - [ ]* ۸.۵ نوشتن تست‌های property برای Gradual Recovery
    - **خصوصیت ۱۶: Gradual Recovery Rate**
    - **اعتبارسنجی الزامات: ۱۰.۵، ۱۰.۷، ۹.۶**

- [ ] ۹. فاز ۷: تست یکپارچگی و مستندات - تست‌های end-to-end و تکمیل مستندات
  - [ ] ۹.۱ پیاده‌سازی Configuration Management
    - ایجاد کلاس ResilienceConfig با Pydantic برای validation
    - خواندن تنظیمات از متغیرهای محیطی و فایل config.yaml
    - اعتبارسنجی تنظیمات در startup
    - استفاده از مقادیر پیش‌فرض معقول
    - _الزامات: ۷.۱، ۷.۲، ۷.۳، ۷.۴، ۷.۵، ۷.۶، ۷.۷_

  - [ ] ۹.۲ پیاده‌سازی Testing API برای شبیه‌سازی خرابی
    - ایجاد endpoint های تست برای فعال/غیرفعال کردن سرویس‌ها
    - امکان تنظیم تاخیر مصنوعی
    - فعال فقط در محیط توسعه
    - _الزامات: ۸.۱، ۸.۲، ۸.۳، ۸.۴، ۸.۵، ۸.۶، ۸.۷، ۸.۸_

  - [ ]* ۹.۳ نوشتن تست‌های یکپارچگی end-to-end
    - تست سناریوی کامل قطع و بازیابی FTP
    - تست سناریوی کامل قطع و بازیابی Elasticsearch
    - تست سناریوی کامل قطع و بازیابی Redis
    - تست سناریوی قطع همزمان چند سرویس

  - [ ]* ۹.۴ نوشتن تست‌های Chaos Testing
    - تست با قطع تصادفی سرویس‌ها
    - تست با network latency
    - تست با partial failures
    - تست با intermittent failures

  - [ ] ۹.۵ ایجاد مستندات عملیاتی
    - راهنمای عملیاتی (Operational Guide)
    - راهنمای troubleshooting
    - مستندات پیکربندی
    - مستندات API

- [ ] ۱۰. نقطه بررسی نهایی - اطمینان از عملکرد کامل سیستم
  - اطمینان از پاس شدن تمام تست‌ها، عملکرد صحیح تمام کامپوننت‌ها، و آماده بودن برای استقرار، در صورت بروز سوال با کاربر مشورت کنید.

## یادداشت‌ها

- وظایف علامت‌گذاری شده با `*` اختیاری هستند و می‌توانند برای MVP سریع‌تر نادیده گرفته شوند
- هر وظیف به الزامات مشخصی از سند requirements.md ارجاع می‌دهد
- نقاط بررسی در فواصل منطقی برای اطمینان از پیشرفت تدریجی قرار داده شده‌اند
- تست‌های property بر اساس ۱۶ خصوصیت صحت تعریف شده در design.md طراحی شده‌اند
- پیاده‌سازی با Python و استفاده از کتابخانه‌های موجود مانند pybreaker، tenacity، prometheus_client انجام می‌شود
- تمام کامپوننت‌ها برای کار در معماری دو شبکه‌ای با Air-Gap طراحی شده‌اند