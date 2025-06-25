'use client';

import { DashboardLayout } from '@/components';
import { ProtectedRoute } from '@/components/auth/protected-route';

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <div className="h-screen w-full">
        <DashboardLayout />
      </div>
    </ProtectedRoute>
  );
} 