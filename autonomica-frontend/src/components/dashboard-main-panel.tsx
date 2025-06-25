'use client';

import { DashboardTab } from './dashboard-layout';
import OverviewTab from './dashboard-tabs/overview-tab';
import AnalyticsTab from './dashboard-tabs/analytics-tab';
import TasksTab from './dashboard-tabs/tasks-tab';
import AgentsTab from './dashboard-tabs/agents-tab';
import SettingsTab from './dashboard-tabs/settings-tab';

interface DashboardMainPanelProps {
  activeTab: DashboardTab;
}

export default function DashboardMainPanel({ activeTab }: DashboardMainPanelProps) {
  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab />;
      case 'analytics':
        return <AnalyticsTab />;
      case 'tasks':
        return <TasksTab />;
      case 'agents':
        return <AgentsTab />;
      case 'settings':
        return <SettingsTab />;
      default:
        return <OverviewTab />;
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-gray-800 overflow-hidden">
      {/* Tab Content */}
      <div className="flex-1 overflow-auto">
        {renderTabContent()}
      </div>
    </div>
  );
} 