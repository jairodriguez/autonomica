'use client';

import { UserButton as ClerkUserButton, useUser } from '@clerk/nextjs';

export function UserButton() {
  const { isLoaded, isSignedIn, user } = useUser();

  if (!isLoaded) {
    return (
      <div className="w-8 h-8 bg-gray-700 rounded-full animate-pulse" />
    );
  }

  if (!isSignedIn) {
    return null;
  }

  return (
    <div className="flex items-center space-x-3">
      <div className="text-right hidden sm:block">
        <p className="text-sm font-medium text-gray-100">
          {user?.fullName || user?.emailAddresses[0]?.emailAddress}
        </p>
        <p className="text-xs text-gray-400">Online</p>
      </div>
      <ClerkUserButton 
        appearance={{
          elements: {
            avatarBox: "w-8 h-8",
            userButtonPopoverCard: {
              background: "#1f2937", // gray-800
              color: "#f3f4f6", // gray-100
              border: "1px solid #374151", // gray-700
            },
            userButtonPopoverActionButton: {
              background: "transparent",
              color: "#f3f4f6", // gray-100
              "&:hover": {
                background: "#374151", // gray-700
              }
            },
            userButtonPopoverActionButtonIcon: {
              color: "#f3f4f6", // gray-100
            },
            userButtonPopoverActionButtonText: {
              color: "#f3f4f6", // gray-100
            },
            userButtonPopoverFooter: {
              background: "#111827", // gray-900
              borderTop: "1px solid #374151", // gray-700
            }
          }
        }}
      />
    </div>
  );
} 