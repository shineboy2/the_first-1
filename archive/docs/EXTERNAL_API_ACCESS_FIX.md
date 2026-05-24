# 🔧 رفع خطای External API Access

## تاریخ: 2026-04-27

---

## ❌ مشکل

صفحه `/dashboard/external-apis` با خطای زیر مواجه بود:
```
Application error: a client-side exception has occurred
```

---

## 🔍 علت

در فایل `app/dashboard/external-apis/page.tsx`:
- آیکون `Users` استفاده شده بود
- اما در import از `lucide-react` وجود نداشت

```tsx
// ❌ قبل
import {
    Plus,
    Search,
    MoreHorizontal,
    Edit,
    Trash2,
    RefreshCw,
    AlertCircle,
} from "lucide-react";

// استفاده شده اما import نشده
<Users className="ml-2 h-4 w-4" />
```

---

## ✅ راه‌حل

اضافه کردن `Users` به import:

```tsx
// ✅ بعد
import {
    Plus,
    Search,
    MoreHorizontal,
    Edit,
    Trash2,
    RefreshCw,
    AlertCircle,
    Users,  // ← اضافه شد
} from "lucide-react";
```

---

## 🚀 Deploy

### فایل اصلاح شده:
```
response-network/admin-panel/app/dashboard/external-apis/page.tsx
```

### دستورات:
```bash
# کپی فایل اصلاح شده
scp page.tsx response@192.168.214.141:/home/response/response-network/admin-panel/app/dashboard/external-apis/

# Rebuild
docker compose up --build -d admin-panel
```

**وضعیت**: ✅ Build موفق و در حال اجرا

---

## ✅ نتیجه

صفحه External APIs حالا بدون خطا کار می‌کند:
- ✅ لیست API ها نمایش داده می‌شود
- ✅ منوی عملیات کار می‌کند
- ✅ دکمه "مدیریت دسترسی" قابل استفاده است

---

## 📝 URL تست

```
http://192.168.214.141:3000/dashboard/external-apis
```

Login: `admin` / `admin123456`

