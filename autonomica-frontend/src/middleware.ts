import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Get the pathname of the request
  const path = request.nextUrl.pathname;

  // Define protected routes
  const protectedRoutes = [
    '/dashboard',
    '/projects',
    '/api/settings',
    '/api/agents',
    '/api/tasks',
  ];

  // Check if the current path is a protected route
  const isProtectedRoute = protectedRoutes.some(route => 
    path.startsWith(route)
  );

  // For now, we'll allow all routes through
  // In production, you would check for authentication tokens here
  // const token = request.headers.get('authorization');
  // if (isProtectedRoute && !token) {
  //   return NextResponse.redirect(new URL('/sign-in', request.url));
  // }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
