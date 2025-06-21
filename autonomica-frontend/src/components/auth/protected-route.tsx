'use client';

import { useAuth, useUser } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { AuthLoading } from './auth-loading';

interface ProtectedRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}

export function ProtectedRoute({ 
  children, 
  redirectTo = '/sign-in' 
}: ProtectedRouteProps) {
  const { isLoaded: authLoaded, isSignedIn } = useAuth();
  const { isLoaded: userLoaded } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (authLoaded && !isSignedIn) {
      router.push(redirectTo);
    }
  }, [authLoaded, isSignedIn, router, redirectTo]);

  // Show loading while auth is checking
  if (!authLoaded || !userLoaded) {
    return <AuthLoading />;
  }

  // Redirect if not signed in
  if (!isSignedIn) {
    return <AuthLoading />;
  }

  // User is authenticated, show protected content
  return <>{children}</>;
} 