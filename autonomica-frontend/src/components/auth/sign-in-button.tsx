'use client';

import { useUser } from '@clerk/nextjs';
import Link from 'next/link';

export function SignInButton() {
  const { isLoaded, isSignedIn } = useUser();

  if (!isLoaded) {
    return (
      <div className="bg-gray-700 text-gray-300 px-4 py-2 rounded-lg animate-pulse">
        Loading...
      </div>
    );
  }

  if (isSignedIn) {
    return null;
  }

  return (
    <Link href="/sign-in">
      <button className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-900">
        Sign In
      </button>
    </Link>
  );
} 