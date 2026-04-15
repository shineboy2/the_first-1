import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware for authentication and route protection
 *
 * Features:
 * - Protects dashboard routes requiring authentication
 * - Redirects unauthenticated users to login
 * - Prevents authenticated users from accessing login page
 * - Validates token existence via cookies
 * - Handles graceful route redirection
 *
 * Protected Routes:
 * - /dashboard/* (all dashboard pages)
 * - / (root redirects to dashboard if authenticated)
 *
 * Public Routes:
 * - /login (login page)
 * - /auth/* (auth routes)
 *
 * Token Storage:
 * - Stored in 'auth-token' cookie
 * - Set by auth store with 7-day expiry
 * - HttpOnly flag for production security
 */

export async function middleware(request: NextRequest) {
  // Get the access token from cookies
  // The auth store sets this as 'auth-token'
  const token = request.cookies.get("auth-token")?.value;

  const { pathname } = request.nextUrl;

  // Define public routes (no authentication required)
  const publicRoutes = ["/login", "/register", "/auth"];
  const isPublicRoute = publicRoutes.some((route) => pathname.startsWith(route));

  // Define protected routes (authentication required)
  const protectedRoutes = ["/dashboard"];
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  );

  // Route: User on login page
  if (pathname === "/login" || pathname === "/register") {
    // If authenticated, redirect to dashboard
    if (token) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
    // Otherwise allow access to login page
    return NextResponse.next();
  }

  // Route: Protected dashboard routes
  if (isProtectedRoute) {
    // If not authenticated, redirect to login
    if (!token) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("callbackUrl", pathname);
      return NextResponse.redirect(loginUrl);
    }
    // Otherwise allow access
    return NextResponse.next();
  }

  // Route: Root path (/)
  if (pathname === "/") {
    // If authenticated, redirect to dashboard
    if (token) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
    // If not authenticated, redirect to login
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Route: All other paths
  // Allow public access to other routes (API, static files, etc.)
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes should be handled separately)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     * - .well-known (for SSL certificates, etc.)
     */
    "/((?!api|_next/static|_next/image|favicon.ico|.well-known).*)",
  ],
};

