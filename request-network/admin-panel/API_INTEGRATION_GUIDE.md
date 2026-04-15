# 🔌 راهنمای یکپارچه‌سازی API - پنل ادمین

> تمام جزئیات و اندپوینت‌های API به زبان فارسی

---

## 📋 Endpoints Overview

### بررسی سلامت سیستم

#### `GET /admin/health`
**هدف:** بررسی سلامت پایه سیستم

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-26T10:30:00Z",
  "uptime": 3600
}
```

**Implementation:**
```typescript
// lib/services/admin-api.ts
export const getHealth = async () => {
  return apiClient.get('/admin/health');
};
```

**نحوه استفاده:**
```typescript
import { getHealth } from '@/lib/services/admin-api';

const health = await getHealth();
console.log(health);
```

---

#### `GET /admin/health/detailed`
**هدف:** دریافت اطلاعات سلامت به صورت جزئی

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "elasticsearch": "connected",
  "workers": {
    "active": 3,
    "pending": 0
  },
  "timestamp": "2025-11-26T10:30:00Z"
}
```

---

### اندپوینت‌های آمار

#### `GET /admin/stats/system`
**هدف:** آمار سیستم

**Response:**
```json
{
  "cpu_usage": 45.2,
  "memory_usage": 2048,
  "memory_total": 8192,
  "disk_usage": 500,
  "disk_total": 1000,
  "uptime": 86400
}
```

**در داشبورد:**
```typescript
const stats = await getSystemStats();
setSystemHealth({
  cpu: stats.cpu_usage,
  memory: (stats.memory_usage / stats.memory_total) * 100,
  disk: (stats.disk_usage / stats.disk_total) * 100
});
```

---

#### `GET /admin/stats/queues`
**هدف:** اطلاعات صف Celery

**Response:**
```json
{
  "total_tasks": 150,
  "pending_tasks": 30,
  "processing_tasks": 5,
  "completed_tasks": 115,
  "failed_tasks": 0,
  "queue_names": ["celery", "default", "priority"]
}
```

---

#### `GET /admin/stats/cache`
**هدف:** آمار کش

**Response:**
```json
{
  "hit_rate": 85.5,
  "miss_rate": 14.5,
  "eviction_rate": 2.1,
  "size": 2048,
  "items": 450,
  "memory_used": 512,
  "memory_limit": 1024
}
```

---

### مدیریت کاربران

#### `GET /admin/users`
**هدف:** دریافت لیست همه کاربران

**Query Parameters:**
```
?page=1
&limit=50
&search=admin
&sort_by=created_at
&order=desc
&role=admin
&status=active
```

**Response:**
```json
{
  "users": [
    {
      "id": "uuid-1",
      "email": "admin@example.com",
      "name": "Admin User",
      "role": "admin",
      "status": "active",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-11-26T10:30:00Z",
      "last_login": "2025-11-26T09:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50,
  "total_pages": 3
}
```

**Implementation:**
```typescript
// lib/services/admin-api.ts
export const getUsers = async (params?: UserFilters) => {
  return apiClient.get('/admin/users', { params });
};

interface UserFilters {
  page?: number;
  limit?: number;
  search?: string;
  sort_by?: 'name' | 'email' | 'created_at' | 'role';
  order?: 'asc' | 'desc';
  role?: 'admin' | 'user' | 'moderator';
  status?: 'active' | 'inactive' | 'banned';
}
```

**در داشبورد:**
```typescript
const [users, setUsers] = useState([]);
const [filters, setFilters] = useState({ page: 1, limit: 50 });

useEffect(() => {
  const fetchUsers = async () => {
    try {
      const response = await getUsers(filters);
      setUsers(response.data.users);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };
  
  fetchUsers();
}, [filters]);
```

---

### مدیریت درخواست‌ها

#### `GET /admin/requests/recent`
**هدف:** دریافت درخواست‌های اخیر

**Query Parameters:**
```
?page=1
&limit=50
&status=all
&start_date=2025-11-01
&end_date=2025-11-26
&user_id=uuid
```

**Response:**
```json
{
  "requests": [
    {
      "id": "uuid-1",
      "user_id": "uuid-user",
      "status": "completed",
      "progress": 100,
      "created_at": "2025-11-26T08:00:00Z",
      "updated_at": "2025-11-26T08:15:00Z",
      "duration_seconds": 900,
      "error": null
    }
  ],
  "by_status": {
    "pending": 5,
    "processing": 3,
    "completed": 150,
    "failed": 2
  },
  "total": 160
}
```

**Type Definition:**
```typescript
interface Request {
  id: string;
  user_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  updated_at: string;
  duration_seconds: number;
  error: string | null;
}
```

---

### مدیریت کش

#### `DELETE /admin/cache/clear`
**هدف:** پاک‌سازی کامل کش

**Request:**
```json
{
  "cache_type": "all"  // یا "redis"، "elasticsearch"
}
```

**Response:**
```json
{
  "success": true,
  "cleared": 450,
  "message": "Cache cleared successfully"
}
```

**Implementation:**
```typescript
export const clearCache = async (type: string = 'all') => {
  return apiClient.delete('/admin/cache/clear', {
    data: { cache_type: type }
  });
};

// استفاده
await clearCache('all');
```

---

#### `POST /admin/cache/optimize`
**هدف:** بهینه‌سازی کش

**Response:**
```json
{
  "success": true,
  "evicted": 50,
  "freed_memory": 256,
  "remaining": 400
}
```

---

## 🔑 احراز هویت

### مدیریت توکن

**فرآیند JWT Token:**
```
1. ورود → Backend
2. Backend یک توکن JWT بازمی‌گرداند
3. توکن در کوکی HttpOnly ذخیره می‌شود
4. Axios توکن را به درخواست‌ها اضافه می‌کند
5. درخواست‌ها با هدر Authorization ارسال می‌شوند
6. توکن پس از ۷ روز منقضی می‌شود
7. خروج خودکار در صورت دریافت 401
```

**Implementation:**
```typescript
// lib/services/api-client.ts
const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30000,
  withCredentials: true, // ارسال کوکی‌ها
});

// Request Interceptor
axiosInstance.interceptors.request.use((config) => {
  const token = Cookies.get('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // خروج و ریدایرکت
      Cookies.remove('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

---

## 🔄 به‌روزرسانی بلادرنگ

### تنظیم رفرش خودکار

```typescript
// app/(dashboard)/page.tsx
useEffect(() => {
  // هر ۳۰ ثانیه یکبار رفرش کن
  const interval = setInterval(async () => {
    await fetchStats();
  }, 30000);
  
  return () => clearInterval(interval);
}, []);
```

**در تنظیمات قابل کنترل:**
```typescript
// app/(dashboard)/settings/page.tsx
const [autoRefresh, setAutoRefresh] = useState(true);
const [refreshInterval, setRefreshInterval] = useState(30000);

useEffect(() => {
  localStorage.setItem('autoRefresh', autoRefresh);
  localStorage.setItem('refreshInterval', refreshInterval);
}, [autoRefresh, refreshInterval]);
```

---

## 📊 تعریف کامل انواع داده

```typescript
// واسط کاربری User
interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'moderator';
  status: 'active' | 'inactive' | 'banned';
  created_at: string;
  updated_at: string;
  last_login: string | null;
  profile_picture?: string;
  permissions?: string[];
}

// واسط کاربری Request
interface Request {
  id: string;
  user_id: string;
  title?: string;
  description?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  created_at: string;
  updated_at: string;
  duration_seconds: number;
  error: string | null;
  result?: Record<string, any>;
}

// واسط کاربری SystemStats
interface SystemStats {
  cpu_usage: number;
  memory_usage: number;
  memory_total: number;
  disk_usage: number;
  disk_total: number;
  uptime: number;
}

// واسط کاربری CacheStats
interface CacheStats {
  hit_rate: number;
  miss_rate: number;
  eviction_rate: number;
  size: number;
  items: number;
  memory_used: number;
  memory_limit: number;
}

// واسط کاربری HealthStatus
interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  database: 'connected' | 'disconnected';
  redis: 'connected' | 'disconnected';
  elasticsearch: 'connected' | 'disconnected';
  workers: {
    active: number;
    pending: number;
    failed: number;
  };
  timestamp: string;
}
```

---

## ⚠️ خطاهای رایج

```typescript
// 401 Unauthorized
{
  status: 401,
  message: "Invalid or expired token",
  action: "Redirect to login"
}

// 403 Forbidden
{
  status: 403,
  message: "Insufficient permissions",
  action: "Show error alert"
}

// 404 Not Found
{
  status: 404,
  message: "Endpoint not found",
  action: "Show not found page"
}

// 500 Server Error
{
  status: 500,
  message: "Internal server error",
  action: "Retry or show error"
}
```

### الگوی مدیریت خطا

```typescript
try {
  const data = await getUsers();
  setUsers(data);
} catch (error: any) {
  const statusCode = error.response?.status;
  const message = error.response?.data?.message || 'Unknown error';
  
  if (statusCode === 401) {
    // خروج
    authStore.logout();
  } else if (statusCode === 403) {
    // نمایش عدم دسترسی
    setError('شما اجازه دسترسی به این صفحه را ندارید');
  } else if (statusCode === 404) {
    // پیدا نشد
    setError('داده‌ای یافت نشد');
  } else {
    // خطای عمومی
    setError(`Error: ${message}`);
  }
}
```

---

## 🧪 تست یکپارچه‌سازی API

### تست توسعه

```bash
# بررسی سلامت
curl http://localhost:8000/admin/health

# دریافت کاربران
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/admin/users

# دریافت آمار
curl http://localhost:8000/admin/stats/system

# پاک‌سازی کش
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/admin/cache/clear
```

### تست در مرورگر

```javascript
// در کنسول مرورگر
const apiUrl = process.env.NEXT_PUBLIC_API_URL;

// تست سلامت
fetch(`${apiUrl}/admin/health`).then(r => r.json()).then(console.log);

// تست آمار
fetch(`${apiUrl}/admin/stats/system`).then(r => r.json()).then(console.log);

// تست با احراز هویت
fetch(`${apiUrl}/admin/users`, {
  headers: {
    'Authorization': `Bearer ${Cookies.get('auth_token')}`
  }
}).then(r => r.json()).then(console.log);
```

---

## 📝 نمونه پاسخ‌های API

### پاسخ موفق
```json
{
  "data": {
    "users": [...],
    "total": 100
  },
  "success": true,
  "message": "Data retrieved successfully",
  "timestamp": "2025-11-26T10:30:00Z"
}
```

### پاسخ خطا
```json
{
  "success": false,
  "message": "Invalid request",
  "error": "Validation error",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  }
}
```

---

## 🚀 نکات بهینه‌سازی عملکرد

1. **Caching:** هر جا ممکن است کش کنید
2. **Pagination:** برای داده‌های بزرگ از صفحه‌بندی استفاده کنید
3. **Filters:** فیلترها را در بک‌اند اعمال کنید
4. **Debouncing:** جستجوها را debounce کنید
5. **Error Recovery:** منطق تلاش مجدد پیاده‌سازی کنید

---

## 📞 رفع اشکال

| مشکل | راه‌حل |
|------|-------|
| 404 Not Found | با `/admin/health` سلامت بک‌اند را بررسی کنید |
| 401 Unauthorized | آیا توکن منقضی شده؟ دوباره وارد شوید |
| CORS Error | CORS بک‌اند را پیکربندی کنید |
| Timeout | زمان تایم‌اوت API را افزایش دهید یا شبکه را بررسی کنید |
| 500 Error | لاگ‌های بک‌اند را ببینید: `docker logs response_api` |

---

**Version:** 1.0  
**Last Updated:** 26 نوامبر 2025  
**Status:** ✅ Complete
