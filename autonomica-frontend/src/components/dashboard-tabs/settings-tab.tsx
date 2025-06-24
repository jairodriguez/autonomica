'use client';

import { Cog6ToothIcon } from '@heroicons/react/24/outline';

export default function SettingsTab() {
  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Settings</h1>
        <p className="text-gray-400">Configure your dashboard and system preferences</p>
      </div>

      {/* Placeholder Content */}
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-12">
        <div className="text-center">
          <Cog6ToothIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">Settings Panel</h3>
          <p className="text-gray-500">
            Configuration and settings components will be implemented in later subtasks
          </p>
          <div className="mt-6 text-sm text-gray-400">
            Features to include:
            <ul className="mt-2 space-y-1 text-left max-w-md mx-auto">
              <li>• User preferences</li>
              <li>• Theme customization</li>
              <li>• Notification settings</li>
              <li>• API configuration</li>
              <li>• System monitoring settings</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
} 