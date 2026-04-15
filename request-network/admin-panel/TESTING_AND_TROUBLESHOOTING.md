# 🔍 راهنمای تست و رفع اشکال - پنل ادمین فاز ۸

> **توضیح:** این راهنما به شما کمک می‌کند تا رایج‌ترین مشکلات را به‌راحتی حل کنید.

---

## 🧪 Test Checklist

### 1️⃣ Build & Start
```bash
# ✅ آیا پروژه را در حالت توسعه اجرا کردید؟
cd response-network/admin-panel
npm run dev

# ✅ آیا پروژه را در داکر اجرا کردید؟
docker-compose up -d
docker ps  # بررسی کنید که همه سرویس‌ها اجرا می‌شوند
```

### 2️⃣ Login Test
```
Username: admin
Password: admin@123456

انتظار می‌رود:
✅ به صفحه `/dashboard` منتقل شود
✅ توکن در کوکی ذخیره شود
✅ اطلاعات کاربر نمایش داده شود
```

### 3️⃣ Dashboard Pages
```
✅ /dashboard        - نمای کلی سیستم
✅ /dashboard/users  - لیست کاربران
✅ /dashboard/requests - پیگیری درخواست‌ها
✅ /dashboard/cache  - مدیریت کش
✅ /dashboard/settings - صفحه تنظیمات
```

### 4️⃣ Dark Mode Test
```
✅ از تنظیمات فعال/غیرفعال کنید
✅ در localStorage ذخیره شود
✅ در همه صفحات کار کند
```

### 5️⃣ Responsive Design
```
Desktop (1920px)  ✅ چیدمان کامل
Tablet (768px)    ✅ جمع شدن سایدبار
Mobile (375px)    ✅ منوی همبرگری
```

---

## ❌ مشکلات رایج و راه‌حل‌ها

### **مشکل ۱: خطای "Cannot find module"**
```
❌ Error: Cannot find module 'js-cookie'
✅ راه‌حل:
npm install js-cookie @types/js-cookie
npm install @radix-ui/react-switch @radix-ui/react-select
npm install @radix-ui/react-tabs
```

### **مشکل ۲: پورت ۳۰۰۰ قبلاً استفاده می‌شود**
```
❌ Error: listen EADDRINUSE: address already in use :::3000
✅ راه‌حل:
# پردازش قبلی را متوقف کنید:
lsof -i :3000
kill -9 <PID>

# یا از پورت دیگری استفاده کنید:
npm run dev -- -p 3001
```

### **مشکل ۳: اتصال به API ممکن نیست**
```
❌ Error: Network error or 404
✅ راه‌حل:

# ✅ آیا بک‌اند فعال است؟
curl http://localhost:8000/admin/health

# ✅ اگر در داکر هستید:
docker logs response_api
docker-compose ps

# ✅ متغیرهای محیطی:
echo $NEXT_PUBLIC_API_URL

# ✅ شبکه داکر:
docker network inspect response_network
```

### **مشکل ۴: ورود انجام نمی‌شود**
```
❌ Error: Invalid credentials
✅ راه‌حل:

# اطلاعات ورود صحیح:
admin / admin@123456

# در پایگاه داده بررسی کنید:
docker exec response_db psql -U postgres -d response_db
SELECT * FROM users WHERE email='admin@example.com';

# یا ریست کنید:
python manage_db.py
```

### **مشکل ۵: حالت تیره کار نمی‌کند**
```
❌ حالت تیره فعال نمی‌شود
✅ راه‌حل:

# بررسی در localStorage:
localStorage.getItem('theme')

# ریست کنید:
localStorage.removeItem('theme')

# کش مرورگر را پاک کنید:
Ctrl+Shift+Delete
```

### **مشکل ۶: صفحات خالی هستند**
```
❌ صفحات بارگذاری می‌شوند اما داده‌ای نمایش داده نمی‌شود
✅ راه‌حل:

# خطاهای کنسول را بررسی کنید:
F12 → تب Console

# درخواست‌های شبکه را بررسی کنید:
F12 → تب Network → بررسی API calls

# لاگ‌های بک‌اند:
docker logs response_api

# سلامت بک‌اند:
curl http://localhost:8000/admin/health
```

### **مشکل ۷: خطاهای TypeScript**
```
❌ Error: TS2345: Argument of type 'X' is not assignable
✅ راه‌حل:

# بررسی بیلد:
npm run build

# رفع خطاهای تایپ:
npm install --save-dev @types/node @types/react @types/react-dom

# پاک‌سازی کش:
rm -rf .next
npm run build
```

### **مشکل ۸: Tailwind CSS کار نمی‌کند**
```
❌ استایل‌ها در صفحه نمایش داده نمی‌شوند
✅ راه‌حل:

# پیکربندی tailwind را بررسی کنید:
cat tailwind.config.ts

# مجدداً بیلد کنید:
npm run build

# کش مرورگر را پاک کنید:
Ctrl+Shift+Delete
```

### **مشکل ۹: بیلد داکر با خطا مواجه می‌شود**
```
❌ Error: docker build failed
✅ راه‌حل:

# لاگ‌های بیلد را ببینید:
docker-compose build --no-cache

# سرویس خاص:
docker-compose build admin-panel

# ریست کامل:
docker system prune -a
docker-compose up --build
```

### **مشکل ۱۰: با Middleware از سیستم خارج می‌شوید**
```
❌ در هر صفحه به صفحه ورود هدایت می‌شوید
✅ راه‌حل:

# بررسی توکن:
console.log(document.cookie)

# بررسی استور:
localStorage.getItem('auth-store')

# در فایل auth-store.ts بررسی کنید:
getInitialState() → منطق توکن
```

---

## 🔧 دستورات رفع اشکال

### **Check Services**
```bash
#+ مشاهده همه کانتینرها
docker ps

#+ لاگ‌های پنل ادمین
docker logs response_admin_panel

#+ لاگ‌های بک‌اند
docker logs response_api

#+ لاگ‌های پایگاه داده
docker logs response_db

#+ لاگ‌های Redis
docker logs response_redis
```

### **تست شبکه**
```bash
#+ سلامت بک‌اند
curl http://localhost:8000/admin/health

#+ بررسی دسترسی فرانت‌اند
curl http://localhost:3000

#+ شبکه داکر
docker network inspect response_network

#+ بررسی DNS
docker exec response_admin_panel ping api
```

### **تست پایگاه داده**
```bash
#+ اتصال به پایگاه داده
docker exec -it response_db psql -U postgres -d response_db

#+ بررسی جدول کاربران
SELECT id, email, role FROM users LIMIT 5;

#+ بررسی کاربر ادمین
SELECT * FROM users WHERE email='admin@example.com';

#+ ریست رمز عبور
UPDATE users SET password='$2b$12$...' WHERE email='admin@example.com';
```

### **تست فرانت‌اند**
```bash
#+ بررسی محیط
cat response-network/admin-panel/.env.local

#+ بررسی بیلد
npm run build

#+ بررسی تایپ
npm run type-check

#+ بررسی Lint
npm run lint

#+ تست دستی
curl http://localhost:3000/login
curl http://localhost:3000/api/health
```

---

## 🚀 Quick Restart Guide

### **ریست کامل**
```bash
#+ همه چیز را متوقف کنید
docker-compose down -v

#+ دوباره اجرا کنید
docker-compose up -d

#+ منتظر سرویس‌ها باشید
sleep 10

#+ لاگ‌ها را بررسی کنید
docker-compose logs -f
```

### **فقط ریستارت فرانت‌اند**
```bash
docker-compose restart admin-panel

#+ یا بازسازی
docker-compose up -d --build admin-panel
```

### **فقط ریستارت بک‌اند**
```bash
docker-compose restart api

#+ منتظر بمانید
sleep 5

#+ بررسی کنید
curl http://localhost:8000/admin/health
```

---

## 📊 Performance Testing

### **زمان بارگذاری**
```bash
#+ در تب Network (F12 → Network) بررسی کنید
# زمان‌های هدف:
- بارگذاری داشبورد: کمتر از ۲ ثانیه
- فراخوانی API: کمتر از ۵۰۰ میلی‌ثانیه
- بارگذاری تصویر: کمتر از ۱ ثانیه
```

### **مصرف حافظه**
```bash
#+ فرایند فرانت‌اند
docker stats response_admin_panel

# هدف:
- RAM: کمتر از ۲۰۰ مگابایت
- CPU: کمتر از ۱۰٪
```

### **درخواست‌های شبکه**
```bash
#+ کنسول مرورگر
console.table(performance.getEntries())

#+ فراخوانی‌های API
window.fetch logs
```

---

## 🐛 Development Debugging

### **Enable Debug Logging**
```typescript
// lib/services/api-client.ts میں:
const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30000,
});

// Request interceptor
axiosInstance.interceptors.request.use((config) => {
  console.log('🚀 Request:', config.url, config.data);
  return config;
});

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => {
    console.log('✅ Response:', response.config.url, response.data);
    return response;
  },
  (error) => {
    console.error('❌ Error:', error.config?.url, error.response?.status);
    return Promise.reject(error);
  }
);
```

### **Check Zustand Store**
```typescript
// Browser console میں:
import { useAuthStore } from '@/lib/stores/auth-store';

const state = useAuthStore.getState();
console.log('Auth state:', state);
```

### **Network Inspection**
```bash
# Browser DevTools
F12 → Network → Filter: XHR
# تمام API calls دیکھیں

# Request/Response headers
# Status codes check
# Response payloads
```

---

## ✅ Validation Checklist

```
Before going to production:

✅ npm run build - کوئی errors نہیں
✅ npm run type-check - تمام types صحیح
✅ npm run lint - کوئی warnings نہیں
✅ Docker build successful
✅ docker-compose up کام کرے
✅ Login successful
✅ تمام pages load ہوں
✅ API calls successful
✅ Dark mode کام کرے
✅ Mobile responsive ہو
✅ No console errors
✅ Performance acceptable
✅ Security headers present
```

---

## 📞 Emergency Contacts

**اگر کچھ غلط ہو جائے:**

1. **npm errors** → `npm cache clean --force && npm install`
2. **Docker errors** → `docker system prune -a && docker-compose up --build`
3. **API errors** → Check backend logs: `docker logs response_api`
4. **Type errors** → Run: `npm run type-check`
5. **Build errors** → Clear cache: `rm -rf .next node_modules && npm install && npm run build`

---

## 🎯 Success Indicators

✅ Frontend چل رہی ہے: `http://localhost:3000`  
✅ Backend چل رہی ہے: `http://localhost:8000`  
✅ Login کام کر رہا ہے: `admin/admin@123456`  
✅ Dashboard دکھائی دے رہا ہے: صفحات load ہو رہے ہیں  
✅ API calls کام کر رہی ہیں: Network tab میں green status  
✅ Dark mode کام کر رہی ہے: Settings میں toggle  

---

**آخری اپڈیٹ:** 26 نوامبر 2025  
**حالت:** ✅ Ready for Testing

