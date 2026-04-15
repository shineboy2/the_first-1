# 🎨 Response Network Admin Panel - Frontend

Professional Next.js 15 Admin Dashboard for Response Network system monitoring and management.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Start development server
npm run dev
```

Visit `http://localhost:3000` in your browser.

## 📦 Features

### ✅ Authentication
- JWT-based login
- Secure token storage (cookies)
- Auto-logout on token expiry
- Protected routes via middleware

### ✅ Dashboard
- System health monitoring
- Real-time statistics
- User count and activity
- Request status overview
- Processing metrics

### ✅ User Management
- View all users
- Search and filter
- Sort by multiple criteria
- Active/inactive status
- User roles display

### ✅ Request Tracking
- Monitor all requests
- Filter by status
- View request details
- Progress indicators
- Timeline view

### ✅ Cache Management
- View cache statistics
- Clear cache operation
- Optimize cache
- Performance metrics
- Memory usage

### ✅ Settings
- Theme selection (Light/Dark/System)
- Auto-refresh configuration
- Notification preferences
- Account information

### ✅ UI/UX
- Dark mode support
- Responsive design (mobile/tablet/desktop)
- Smooth animations
- Loading states
- Error handling
- Real-time updates

## 🏗️ Project Structure

```
admin-panel/
├── app/                    # Next.js app directory
│   ├── (auth)/            # Authentication pages
│   ├── (dashboard)/       # Dashboard pages
│   └── layout.tsx         # Root layout
├── lib/
│   ├── services/          # API services layer
│   └── stores/            # Zustand stores
├── components/
│   └── ui/                # shadcn/ui components
└── middleware.ts          # Route protection
```

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| Framework | Next.js 15.5.5 |
| UI | React 19.1.0 |
| Language | TypeScript 5 |
| Styling | Tailwind CSS 4 |
| Components | shadcn/ui |
| State | Zustand 5.0.8 |
| HTTP | Axios 1.12.2 |
| Forms | React Hook Form 7.65.0 |
| Data | TanStack Query 5.90.3 |
| Theme | next-themes 0.4.6 |

## 📖 Documentation

Comprehensive documentation available:

- **[ADMIN_PANEL_FRONTEND_DOCUMENTATION.md](./ADMIN_PANEL_FRONTEND_DOCUMENTATION.md)** - Complete guide
- **[API Integration Guide](#api-integration)** - Backend connection
- **[Component Guide](#component-library)** - UI components

## 🔐 Environment Variables

Create `.env.local`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Debug Mode
NEXT_PUBLIC_DEBUG=true

# Node Environment
NODE_ENV=development
```

## 🚀 Development

### Start Dev Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
npm run start
```

### Type Check
```bash
npm run type-check
```

### Lint Code
```bash
npm run lint
```

## 📱 Pages

### Public Pages
- `/login` - Login form

### Protected Pages
- `/dashboard` - Home dashboard
- `/dashboard/users` - Users management
- `/dashboard/requests` - Request tracking
- `/dashboard/cache` - Cache management
- `/dashboard/settings` - Admin settings

## 🔑 Key Features Breakdown

### Dashboard Overview
Shows:
- System health (Database, Redis status)
- Key metrics (Users, Requests, Processing, Failed)
- Request status breakdown
- Database info

**Auto-refreshes every 30 seconds**

### Users Page
Displays:
- Total users count
- Active users count
- Admin count
- Searchable user list
- Sort by name, email, date, or role
- User details (status, role, creation date, last login)

### Requests Page
Shows:
- Total requests
- Status distribution (Pending, Processing, Completed, Failed)
- Status filters
- Request ID and user ID search
- Progress indicators
- Real-time updates

### Cache Page
Includes:
- Cache size and item count
- Hit rate percentage
- Clear cache button
- Optimize cache button
- Performance metrics
- Memory usage graphs

### Settings Page
Allows:
- Theme selection
- Auto-refresh toggle
- Refresh interval selection
- Notifications toggle
- Account info display

## 🎨 Styling

### Theme Support
- Light Mode
- Dark Mode
- System Preference

### Responsive Design
- Mobile-first approach
- Tablet optimization
- Desktop full experience
- Touch-friendly buttons

### Custom Animations
- Blob animations (background)
- Slide-in effects
- Fade transitions
- Loading spinners

## 🔄 API Integration

### Base Configuration
```
Base URL: http://localhost:8000
Authentication: JWT Bearer Token
Timeout: 30 seconds
Headers: Content-Type: application/json
```

### Key Endpoints

| Service | Endpoints |
|---------|-----------|
| Health | `/health`, `/health/detailed` |
| Stats | `/stats/system`, `/stats/queue`, `/stats/cache` |
| Users | `/users`, `/users/{id}` |
| Requests | `/requests/recent`, `/requests/stats` |
| Cache | `/cache/clear`, `/cache/optimize` |

### Error Handling
- 401: Auto-logout and redirect to login
- 403: Admin access denied
- Other errors: Display user-friendly messages

## 🧪 Testing

### Run Tests
```bash
npm test
```

### Lint
```bash
npm run lint
```

### Type Check
```bash
npm run type-check
```

## 📦 Build & Deploy

### Development Build
```bash
npm run dev
# Server on: http://localhost:3000
```

### Production Build
```bash
npm run build
npm run start
```

### Docker Deployment
```bash
docker build -t admin-panel .
docker run -p 3000:3000 admin-panel
```

### Vercel Deployment
```bash
npm install -g vercel
vercel deploy --prod
```

## 🔒 Security

- ✅ JWT authentication
- ✅ Secure cookie storage
- ✅ Protected routes via middleware
- ✅ Input validation (Zod)
- ✅ CORS configured
- ✅ No sensitive data in logs
- ✅ Error messages sanitized

## 🐛 Troubleshooting

### Can't connect to backend
- Check API URL in `.env.local`
- Ensure backend is running
- Check CORS configuration

### Login fails
- Verify credentials
- Check backend logs
- Ensure JWT token format

### Styling not applied
- Clear `.next` folder: `rm -rf .next`
- Rebuild: `npm run build`
- Check Tailwind config

### Token not persisting
- Check browser cookies enabled
- Verify cookie settings
- Check localStorage (settings)

## 📝 Common Tasks

### Add New Dashboard Page
1. Create file: `app/(dashboard)/new-page/page.tsx`
2. Use data from `lib/services/admin-api.ts`
3. Import components from `components/ui/`
4. Add navigation link in layout

### Add New API Service
1. Extend `lib/services/admin-api.ts`
2. Define request/response types
3. Create service object with methods
4. Export from file

### Customize Theme
1. Edit `tailwind.config.ts`
2. Modify colors in `globals.css`
3. Update shadcn/ui component themes
4. Restart dev server

## 📚 Resources

- [Next.js Docs](https://nextjs.org/docs)
- [React Docs](https://react.dev)
- [TypeScript Docs](https://www.typescriptlang.org)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com)

## 📄 License

Part of Response Network project.

## 🤝 Support

For issues or questions:
1. Check the full documentation
2. Review error messages
3. Check backend logs
4. Verify environment variables

---

**Version:** 1.0.0  
**Last Updated:** November 2024  
**Status:** ✅ Production Ready

**Made with ❤️ for Response Network**
