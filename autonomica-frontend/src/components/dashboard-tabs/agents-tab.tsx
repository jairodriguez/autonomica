'use client';

import { UserGroupIcon } from '@heroicons/react/24/outline';

export default function AgentsTab() {
  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Agent Management</h1>
        <p className="text-gray-400">Monitor and manage your AI agent workforce</p>
      </div>

      {/* Placeholder Content */}
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-12">
        <div className="text-center">
          <UserGroupIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">Agent Management Dashboard</h3>
          <p className="text-gray-500">
            Agent analytics and management components will be implemented in later subtasks
          </p>
          <div className="mt-6 text-sm text-gray-400">
            Features to include:
            <ul className="mt-2 space-y-1 text-left max-w-md mx-auto">
              <li>• Agent performance analytics</li>
              <li>• Resource utilization metrics</li>
              <li>• Agent status monitoring</li>
              <li>• Task assignment tracking</li>
              <li>• Agent configuration management</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
} 