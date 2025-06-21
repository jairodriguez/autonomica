'use client';

import { ProjectLayout } from '@/components';
import { ProtectedRoute } from '@/components/auth/protected-route';

export default function ProjectsPage() {
  return (
    <ProtectedRoute>
      <div className="h-screen w-full">
        <ProjectLayout />
      </div>
    </ProtectedRoute>
  );
} 