# ⚡ Quick Reference - Admin Panel Commands

## 🚀 فوری شروعات | Quick Start

```bash
# Development شروع کریں
cd response-network/admin-panel && npm run dev
# 🌐 http://localhost:3000

# Docker سے شروع کریں
docker-compose up -d
# 🌐 http://localhost:3000

# Production build
npm run build && npm start
```

---

## 👤 Login Credentials
```
Email:    admin@example.com  (یا admin)
Password: admin@123456
```

---

## 📋 API Endpoints

```
/admin/health                    → System health
/admin/stats/system              → System stats
/admin/stats/queues              → Queue stats
/admin/stats/cache               → Cache stats
/admin/users                      → User list
/admin/requests/recent           → Recent requests
/admin/cache/clear               → Clear cache (POST)
/admin/cache/optimize            → Optimize cache (POST)
```

---

## 🌐 Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend | 8000 | http://localhost:8000 |
| DB | 5432 | localhost:5432 |
| Redis | 6380 | localhost:6380 |
| Elasticsearch | 9200 | localhost:9200 |

---

## 📁 اہم Files

```
app/(dashboard)/
├── layout.tsx           → Sidebar & navigation
├── page.tsx             → Dashboard home
├── users/page.tsx       → Users management
├── requests/page.tsx    → Request tracking
├── cache/page.tsx       → Cache management
└── settings/page.tsx    → Settings

lib/services/
├── api-client.ts        → Axios configuration
└── admin-api.ts         → API service layer (260 lines)

lib/stores/
└── auth-store.ts        → Zustand auth store

middleware.ts            → Route protection
```

---

## 🔧 Docker Commands

```bash
# تمام services دیکھیں
docker-compose ps

# Admin panel logs
docker logs response_admin_panel -f

# Restart frontend
docker-compose restart admin-panel

# Rebuild frontend
docker-compose up --build admin-panel

# Full reset
docker-compose down -v && docker-compose up -d

# Database access
docker exec -it response_db psql -U postgres
```

---

## 📊 Debugging

```bash
# Type check
npm run type-check

# Lint check
npm run lint

# Build test
npm run build

# Backend health
curl http://localhost:8000/admin/health

# Frontend test
curl http://localhost:3000/login
```

---

## ❌ مسائل | Issues

| مسئلہ | حل |
|------|-----|
| Port 3000 مصروف | `lsof -i :3000` اور `kill -9 <PID>` |
| npm errors | `npm cache clean --force && npm install` |
| Build fail | `rm -rf .next node_modules && npm install && npm run build` |
| API 404 | `curl http://localhost:8000/admin/health` |
| Login fail | صحیح credentials: `admin/admin@123456` |
| Dark mode نہیں | Browser cache clear: `Ctrl+Shift+Delete` |

---

## 🎯 فنی Details

**Frontend Stack:**
- Next.js 15.5.5
- React 19.1.0
- TypeScript 5
- Tailwind CSS 4
- shadcn/ui components
- Zustand state
- Axios HTTP client

**API Integration:**
- Base URL: `http://localhost:8000` (dev) / `http://api:8000` (docker)
- Timeout: 30 seconds
- Auth: JWT in cookies
- Error handling: 401/403 logout

**Pages:**
1. **Dashboard** - System overview
2. **Users** - User management (search/sort)
3. **Requests** - Request tracking (filter)
4. **Cache** - Cache management (clear/optimize)
5. **Settings** - Admin settings (theme/notifications)

---

## 🔐 Security

✅ Protected routes via middleware  
✅ JWT token management  
✅ Automatic logout on 401  
✅ HttpOnly cookies (production)  
✅ CORS configured  
✅ Input validation (Zod)  

---

## 🚀 Production Deployment

```bash
# Docker build
docker build -t admin-panel:latest response-network/admin-panel

# Docker run
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://api:8000 \
  admin-panel:latest

# Vercel deploy
vercel deploy --prod

# Self-hosted
npm run build && npm start
```

---

## 📞 فوری Help

```bash
# Everything broken?
docker-compose down -v && docker-compose up -d && sleep 10 && docker-compose logs -f

# Just frontend broken?
docker-compose restart admin-panel

# Check if running
curl http://localhost:3000

# Check API connection
curl http://localhost:8000/admin/health
```

---

## ✨ Features

✅ Real-time dashboard  
✅ User management  
✅ Request tracking  
✅ Cache management  
✅ Dark mode  
✅ Responsive design  
✅ Error handling  
✅ Loading states  
✅ Protected routes  
✅ Type-safe API  

---

**Version:** 1.0  
**Last Updated:** 26 نوامبر 2025  
**Status:** ✅ Production Ready
