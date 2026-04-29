# طرح جداسازی شبکه‌ها

## مشکل فعلی
- پوشه shared/ دارای کدهای مشترک بین دو شبکه
- هر دو شبکه وابسته به shared/ هستند
- موقع deployment باید کل پروژه روی هر سرور کپی شود
- نقض اصل جداسازی شبکه‌ها

## راه‌حل پیشنهادی

### 1. کپی کردن کدهای shared به هر شبکه
```
request-network/
├── api/
│   ├── shared/          # کپی از shared/
│   ├── models/
│   ├── routers/
│   └── ...

response-network/
├── api/
│   ├── shared/          # کپی از shared/
│   ├── models/
│   ├── routers/
│   └── ...
```

### 2. حذف وابستگی به shared/ مرکزی
- تغییر import ها از `from shared.` به `from .shared.`
- هر شبکه shared مخصوص خود را دارد
- امکان تغییر مستقل shared در هر شبکه

### 3. بروزرسانی Dockerfile ها
- request-network فقط request-network/ را کپی کند
- response-network فقط response-network/ را کپی کند
- حذف کامل دسترسی به کدهای شبکه مقابل

### 4. مزایا
- جداسازی کامل امنیتی
- هر شبکه مستقل از دیگری
- امکان تغییر shared بدون تأثیر بر شبکه مقابل
- deployment مجزا و امن

### 5. مراحل پیاده‌سازی
1. کپی shared/ به هر دو شبکه
2. تغییر import ها
3. بروزرسانی Dockerfile ها
4. تست عملکرد
5. حذف shared/ مرکزی