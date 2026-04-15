# 🎨 Response Network Admin Panel - Frontend Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Architecture](#architecture)
4. [Features](#features)
5. [Setup & Configuration](#setup--configuration)
6. [Component Guide](#component-guide)
7. [State Management](#state-management)
8. [Authentication](#authentication)
9. [API Integration](#api-integration)
10. [Styling & Theme](#styling--theme)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)

---

## Overview

**Response Network Admin Panel** is a professional Next.js 15 frontend application for managing and monitoring the Response Network system. Built with React 19, TypeScript, and Tailwind CSS 4, it provides:

- ✅ Secure authentication with JWT tokens
- ✅ Complete system monitoring dashboard
- ✅ User management interface
- ✅ Request tracking and statistics
- ✅ Cache management utilities
- ✅ Dark mode support
- ✅ Responsive mobile design
- ✅ Real-time data updates

**Tech Stack:**
- Framework: Next.js 15.5.5
- React: 19.1.0
- Language: TypeScript 5
- Styling: Tailwind CSS 4
- UI Components: shadcn/ui
- State Management: Zustand 5.0.8
- HTTP Client: Axios 1.12.2
- Forms: React Hook Form 7.65.0
- Data Fetching: TanStack Query 5.90.3
- Theme: next-themes 0.4.6

---

## Project Structure

```
/response-network/admin-panel/
├── app/
│   ├── (auth)/
│   │   ├── layout.tsx           # Auth layout (no sidebar)
│   │   ├── login/
│   │   │   └── page.tsx         # Login form with validation
│   │   ├── api.ts               # Auth API client
│   │   └── types.ts             # Form validation schemas
│   ├── (dashboard)/
│   │   ├── layout.tsx           # Dashboard layout with sidebar
│   │   ├── page.tsx             # Dashboard home (system overview)
│   │   ├── users/
│   │   │   └── page.tsx         # Users management page
│   │   ├── requests/
│   │   │   └── page.tsx         # Requests tracking page
│   │   ├── cache/
│   │   │   └── page.tsx         # Cache management page
│   │   └── settings/
│   │       └── page.tsx         # Admin settings page
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Root page (redirects to dashboard)
│   └── globals.css              # Global styles + animations
├── lib/
│   ├── services/
│   │   ├── api-client.ts        # Axios configuration with interceptors
│   │   └── admin-api.ts         # All admin API services & types
│   ├── stores/
│   │   └── auth-store.ts        # Zustand authentication store
│   └── utils/
│       └── cn.ts                # Utility functions (if needed)
├── components/
│   ├── ui/                      # shadcn/ui components (auto-generated)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── table.tsx
│   │   ├── badge.tsx
│   │   ├── alert.tsx
│   │   ├── form.tsx
│   │   ├── select.tsx
│   │   ├── switch.tsx
│   │   └── [more components]
│   └── theme-provider.tsx       # Dark mode provider
├── public/                      # Static assets
├── middleware.ts                # Route protection middleware
├── .env.local                   # Environment variables
├── next.config.ts               # Next.js configuration
├── tsconfig.json                # TypeScript configuration
├── package.json                 # Dependencies
├── tailwind.config.ts           # Tailwind CSS configuration
└── components.json              # shadcn/ui configuration
```

---

## Architecture

### 1. **Layered Architecture**

```
┌─────────────────────────────────┐
│    UI Components (React)         │
│  (Dashboard Pages, Forms)        │
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│   State Management (Zustand)     │
│   (Auth Store, UI State)         │
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│   API Service Layer              │
│   (admin-api.ts Services)        │
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│   HTTP Client (Axios)            │
│   (Error Handling, Interceptors) │
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│   Backend API (http://localhost) │
│   (FastAPI/REST Endpoints)       │
└─────────────────────────────────┘
```

### 2. **Data Flow**

```
User Action
    ↓
UI Component
    ↓
Zustand Store (updates state)
    ↓
API Service (calls admin-api)
    ↓
Axios Client (adds auth headers)
    ↓
Backend API
    ↓
Response (with data)
    ↓
Store (updates state)
    ↓
UI (re-renders with new data)
```

### 3. **Authentication Flow**

```
1. User enters credentials
2. Login form validation (Zod)
3. API call to /auth/login
4. Backend returns token
5. Store saves token + user info
6. Token stored in cookie
7. Middleware checks cookie
8. Axios adds token to requests
9. On 401: Auto-logout + redirect to login
```

---

## Features

### ✅ Dashboard (Home Page)

**Location:** `/dashboard`

**Components:**
- System health status (Database, Redis)
- Key metrics cards (Users, Requests, Processing, Failed)
- Request status breakdown with progress bars
- Database size and results info
- Auto-refresh every 30 seconds

**Data Sources:**
- `healthService.getHealth()` - System status
- `statsService.getSystemStats()` - Overall statistics

---

### ✅ Users Management

**Location:** `/dashboard/users`

**Features:**
- Search users by name or email
- Sort by name, email, date, or role
- Display user roles (Admin/User)
- Show active/inactive status
- Display registration date and last login
- Real-time stats: Total, Active, Admins

**Data Sources:**
- `userService.getUsers()` - All users with details

---

### ✅ Request Tracking

**Location:** `/dashboard/requests`

**Features:**
- View all requests with status
- Filter by status (Pending, Processing, Completed, Failed)
- Search by request ID or user ID
- Display request timestamps
- Progress indicators for each request
- Real-time stats by status

**Data Sources:**
- `requestService.getRecentRequests()` - Recent requests

---

### ✅ Cache Management

**Location:** `/dashboard/cache`

**Features:**
- View cache statistics
- Clear cache operation
- Optimize cache operation
- Display hit rate and eviction rate
- Memory usage monitoring
- Cache performance metrics

**Data Sources:**
- `statsService.getCacheStats()` - Cache details
- `cacheService.clearCache()` - Clear operation
- `cacheService.optimizeCache()` - Optimize operation

---

### ✅ Settings

**Location:** `/dashboard/settings`

**Features:**
- Theme selection (Light/Dark/System)
- Auto-refresh toggle and interval
- Notifications toggle
- Account information display
- Settings persistence (localStorage)

---

## Setup & Configuration

### 1. **Environment Variables**

Create `.env.local`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Debug
NEXT_PUBLIC_DEBUG=true

# Node Environment
NODE_ENV=development
```

### 2. **Installation**

```bash
# Install dependencies
npm install

# Or with yarn
yarn install

# Or with pnpm
pnpm install
```

### 3. **Development Server**

```bash
npm run dev
# Server runs on http://localhost:3000
```

### 4. **Build for Production**

```bash
npm run build
npm run start
```

---

## Component Guide

### UI Components (shadcn/ui)

All UI components are in `components/ui/`:

```tsx
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
```

### Custom Components

```tsx
// Theme Provider (Dark Mode)
import { ThemeProvider } from "@/components/theme-provider";
```

### Example Component Usage

```tsx
"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/lib/stores/auth-store";
import { userService } from "@/lib/services/admin-api";

export default function MyComponent() {
  const { user } = useAuthStore();
  
  const handleClick = async () => {
    const users = await userService.getUsers();
    console.log(users);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>My Component</CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={handleClick}>Load Users</Button>
        <p>Hello, {user?.username}!</p>
      </CardContent>
    </Card>
  );
}
```

---

## State Management

### Zustand Auth Store

**Location:** `lib/stores/auth-store.ts`

```tsx
import { useAuthStore } from "@/lib/stores/auth-store";

// In your component
const { user, token, isAuthenticated, isLoading } = useAuthStore();

// Update auth state
const { setUser, setToken, login, logout, initialize } = useAuthStore();

// Usage examples:
useAuthStore.setState({ isLoading: true });
useAuthStore.getState().logout();
```

**Store Properties:**
- `user: AuthUser | null` - Current user info
- `token: string | null` - JWT access token
- `isLoading: boolean` - Loading state
- `isAuthenticated: boolean` - Auth flag

**Store Actions:**
- `setUser(user)` - Update user
- `setToken(token)` - Update token
- `setLoading(loading)` - Update loading state
- `login(user, token)` - Complete login
- `logout()` - Clear auth (clears cookies)
- `initialize()` - Restore from cookies

---

## Authentication

### Login Flow

1. **Form Submission** → Validates with Zod
2. **API Call** → POST `/auth/login` with credentials
3. **Backend Response** → Returns `{ access_token, user_id, email, role }`
4. **Store Update** → Sets user + token in Zustand
5. **Cookie Save** → Token saved (7-day expiry)
6. **Redirect** → Navigate to `/dashboard`

### Protected Routes

Middleware checks for `auth-token` cookie:
- ✅ Has token + accessing `/login` → Redirect to `/dashboard`
- ✅ Has token + accessing `/dashboard/*` → Allow
- ❌ No token + accessing `/dashboard/*` → Redirect to `/login`
- ✅ No token + accessing `/login` → Allow

### Token Management

**Token Storage:**
- Stored in `auth-token` cookie
- 7-day expiry
- HttpOnly flag (production only)

**Token Injection:**
- Axios interceptor adds `Authorization: Bearer <token>` header
- Automatic on every request

**Token Expiry:**
- Backend returns 401 on expired token
- Axios interceptor catches 401
- Auto-logout triggered
- Redirects to `/login`

---

## API Integration

### Axios Configuration

**Location:** `lib/services/api-client.ts`

```tsx
import { apiClient } from "@/lib/services/api-client";

// Direct API calls
const response = await apiClient.get("/endpoint");
const response = await apiClient.post("/endpoint", data);
```

**Features:**
- Base URL from `NEXT_PUBLIC_API_URL`
- JWT token injection via interceptor
- Error handling (401/403)
- 30-second timeout
- CORS enabled

### API Services

**Location:** `lib/services/admin-api.ts`

```tsx
import {
  healthService,
  statsService,
  userService,
  requestService,
  cacheService,
} from "@/lib/services/admin-api";

// Examples:
const health = await healthService.getHealth();
const stats = await statsService.getSystemStats();
const users = await userService.getUsers();
const requests = await requestService.getRecentRequests();
const cache = await statsService.getCacheStats();
await cacheService.clearCache();
```

### Type Definitions

All responses are fully typed:

```tsx
interface HealthStatus {
  status: "ok" | "warning" | "error";
  services: {
    database: string;
    redis: string;
  };
}

interface SystemStats {
  users: { total: number; active: number };
  requests: { 
    total: number; 
    processing: number; 
    completed: number; 
    failed: number;
  };
  database: { size: string };
  results: { total: number };
}

interface User {
  id: string;
  username: string;
  email: string;
  role: "admin" | "user";
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

// ... and many more
```

---

## Styling & Theme

### Tailwind CSS

All components use Tailwind utility classes:

```tsx
<div className="flex items-center justify-between gap-4 p-4 bg-gray-50 dark:bg-gray-900">
  <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
    Title
  </h1>
</div>
```

### Dark Mode

Using `next-themes`:

```tsx
import { useTheme } from "next-themes";

export default function Component() {
  const { theme, setTheme } = useTheme();

  return (
    <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      Toggle Theme
    </button>
  );
}
```

### Custom Animations

Defined in `globals.css`:

```tsx
// Blob animation (background decoration)
<div className="animate-blob" />

// Other animations
<div className="animate-slideIn" />
<div className="animate-fadeIn" />
<div className="animate-slideDown" />
```

### Color Scheme

**Light Mode:**
- Background: White
- Text: Dark gray
- Primary: Blue (600)
- Accent: Gray (50)

**Dark Mode:**
- Background: Gray (900)
- Text: White
- Primary: Blue (600)
- Accent: Gray (800)

---

## Deployment

### Production Build

```bash
npm run build
# Output: .next/

# Check for errors
npm run lint
npm run type-check
```

### Environment Variables (Production)

Create `.env.production.local`:

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_URL=https://admin.yourdomain.com
NODE_ENV=production
NEXT_PUBLIC_DEBUG=false
```

### Deploy to Vercel

```bash
vercel deploy --prod
```

### Deploy to Docker

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY package.json .
EXPOSE 3000
CMD ["npm", "start"]
```

---

## Troubleshooting

### Issue: Blank page on load

**Cause:** Component rendered before theme provider loads

**Solution:**
```tsx
const [mounted, setMounted] = useState(false);

useEffect(() => {
  setMounted(true);
}, []);

if (!mounted) return null; // Or loading spinner
```

### Issue: Token not being sent

**Cause:** Cookie not set or interceptor not working

**Check:**
1. Cookie exists: `document.cookie`
2. Token in store: `useAuthStore.getState().token`
3. API URL correct in `.env.local`

### Issue: CORS errors

**Cause:** Backend doesn't allow frontend origin

**Solution (Backend):**
```python
CORS_ORIGINS = [
    "http://localhost:3000",  # Dev
    "https://admin.yourdomain.com",  # Prod
]
```

### Issue: Login not working

**Check:**
1. Backend API running (`localhost:8000`)
2. Credentials correct
3. Network tab shows request
4. Backend returns proper JWT token

### Issue: Components not styled

**Cause:** Tailwind CSS not configured

**Solution:**
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Issue: Dark mode not persisting

**Cause:** `next-themes` not properly configured

**Solution:**
```tsx
// In app/layout.tsx
<ThemeProvider>
  {children}
</ThemeProvider>
```

---

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [Axios Documentation](https://axios-http.com/docs)

---

## 🔒 Security Notes

1. **Token Storage:** Always use HttpOnly cookies in production
2. **HTTPS:** Required for production deployment
3. **CORS:** Configure backend to only accept requests from your domain
4. **API Keys:** Never expose sensitive data in environment variables (use `NEXT_PUBLIC_` prefix only for non-sensitive)
5. **Input Validation:** All forms use Zod validation
6. **Error Messages:** Don't expose backend errors to users

---

## 📈 Performance Optimization

1. **Code Splitting:** Next.js automatically splits routes
2. **Image Optimization:** Use `next/image` for images
3. **Data Fetching:** TanStack Query caches API responses
4. **Lazy Loading:** Components are lazy-loaded by default
5. **CSS Optimization:** Tailwind purges unused classes in production

---

## ✅ Checklist for Deployment

- [ ] Environment variables configured
- [ ] Backend API running and accessible
- [ ] CORS configured on backend
- [ ] All tests passing
- [ ] Build completes without errors
- [ ] Dark mode working
- [ ] Mobile responsive layout verified
- [ ] Authentication working end-to-end
- [ ] Error handling working
- [ ] Performance acceptable

---

**Version:** 1.0.0  
**Last Updated:** November 2024  
**Status:** ✅ Production Ready
