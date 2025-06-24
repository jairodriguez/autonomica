'use client';

import { useState } from 'react';
import DashboardSidebar from './dashboard-sidebar';
import DashboardMainPanel from './dashboard-main-panel';

export type DashboardTab = 'overview' | 'analytics' | 'tasks' | 'agents' | 'settings';

export default function DashboardLayout() {
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview');

  return (
    <div className="flex h-full bg-gray-900">
      {/* Dashboard Sidebar */}
      <DashboardSidebar 
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
      
      {/* Dashboard Main Panel */}
      <DashboardMainPanel 
        activeTab={activeTab}
      />
    </div>
  );
} 