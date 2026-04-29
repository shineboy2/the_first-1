# مثال Runtime Configuration برای Frontend

## مشکل فعلی
- `NEXT_PUBLIC_API_URL` در build time تنظیم می‌شود
- برای تغییر API URL باید frontend را rebuild کرد
- در production نمی‌توان API URL را بدون rebuild تغییر داد

## راه‌حل Runtime Configuration

### 1. ایجاد Config Template

#### Request Network
```javascript
// request-network/admin-panel/public/config.template.js
window.__RUNTIME_CONFIG__ = {
  API_URL: '${NEXT_PUBLIC_API_URL}' || 'http://localhost:8001'
};
```

#### Response Network
```javascript
// response-network/admin-panel/public/config.template.js
window.__RUNTIME_CONFIG__ = {
  API_URL: '${NEXT_PUBLIC_API_URL}' || 'http://localhost:8000'
};
```

### 2. اسکریپت تولید Config

```bash
#!/bin/bash
# generate-config.sh
envsubst < /app/public/config.template.js > /app/public/config.js
```

### 3. بروزرسانی API Client

#### قبل
```typescript
// app/(auth)/api.ts
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  // ...
});
```

#### بعد
```typescript
// app/(auth)/api.ts
const getApiUrl = () => {
  // Runtime config has priority
  if (typeof window !== 'undefined' && window.__RUNTIME_CONFIG__) {
    return window.__RUNTIME_CONFIG__.API_URL;
  }
  // Fallback to build-time config
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
};

const api = axios.create({
  baseURL: getApiUrl(),
  // ...
});
```

### 4. اضافه کردن به HTML Layout

```tsx
// app/layout.tsx
import Script from 'next/script';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fa" dir="rtl">
      <head>
        <Script src="/config.js" strategy="beforeInteractive" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
```

### 5. بروزرسانی Dockerfile

```dockerfile
# Frontend Dockerfile
FROM node:20-slim AS builder
# ... build stage

FROM node:20-slim
WORKDIR /app

# کپی built files
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json .

# اضافه کردن runtime config generation
COPY generate-config.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/generate-config.sh

# Create config template
COPY config.template.js /app/public/

EXPOSE 3002
CMD ["/bin/sh", "-c", "generate-config.sh && npm start"]
```

### 6. استفاده در Docker Compose

```yaml
# docker-compose.request.yml
services:
  admin-panel:
    build:
      context: request-network/admin-panel
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=http://192.168.1.100:8001
    ports:
      - "3002:3002"
```

## مزایای Runtime Configuration

### 1. انعطاف‌پذیری
- تغییر API URL بدون rebuild
- تنظیمات مختلف برای محیط‌های مختلف
- امکان تغییر در runtime

### 2. DevOps Friendly
- یک image برای همه محیط‌ها
- تنظیمات از environment variables
- CI/CD ساده‌تر

### 3. Production Ready
- تغییر سریع تنظیمات
- rollback آسان
- monitoring بهتر

## مثال استفاده

### Development
```bash
docker run -p 3002:3002 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8001 \
  request-admin-panel:latest
```

### Production
```bash
docker run -p 3002:3002 \
  -e NEXT_PUBLIC_API_URL=https://api.production.com \
  request-admin-panel:latest
```

### تست تغییر Runtime
```bash
# شروع با API محلی
docker run -d --name test-panel \
  -p 3002:3002 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8001 \
  request-admin-panel:latest

# تغییر به API production (بدون rebuild)
docker stop test-panel
docker run -d --name test-panel \
  -p 3002:3002 \
  -e NEXT_PUBLIC_API_URL=https://api.production.com \
  request-admin-panel:latest
```

## بررسی عملکرد

### 1. بررسی Config File
```bash
curl http://localhost:3002/config.js
# خروجی:
# window.__RUNTIME_CONFIG__ = {
#   API_URL: 'http://localhost:8001'
# };
```

### 2. بررسی در مرورگر
```javascript
// در Console مرورگر
console.log(window.__RUNTIME_CONFIG__);
// خروجی: {API_URL: "http://localhost:8001"}
```

### 3. تست API Calls
```javascript
// در Network tab مرورگر
// باید API calls به URL صحیح ارسال شوند
```

## نکات مهم

### ⚠️ هشدارها
- config.js باید قبل از سایر script ها load شود
- window.__RUNTIME_CONFIG__ باید در client-side در دسترس باشد
- fallback به build-time config ضروری است

### 🔧 بهینه‌سازی
- cache کردن config در memory
- validation کردن URL ها
- error handling برای config نامعتبر

### 📊 مانیتورینگ
- log کردن API URL در استفاده
- tracking تغییرات config
- alert برای config نامعتبر