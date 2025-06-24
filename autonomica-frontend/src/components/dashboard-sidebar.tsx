'use client';

import { 
  ChartBarIcon, 
  Cog6ToothIcon, 
  HomeIcon, 
  ListBulletIcon,
  UserGroupIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';
import { DashboardTab } from './dashboard-layout';
import { useMetrics, useSystemStatus, useTasks, useAgents } from '@/hooks/useApi';
import { useTaskUpdates, useAgentUpdates, useSystemMetricsUpdates } from '@/hooks/useSocket';
import { useEffect, useState } from 'react';

interface DashboardSidebarProps {
  activeTab: DashboardTab;
  onTabChange: (tab: DashboardTab) => void;
}

interface NavItem {
  id: DashboardTab;
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  badge?: number;
}

interface QuickStat {
  label: string;
  value: string;
  trend: 'up' | 'down' | 'neutral';
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  color: string;
}

interface ActivityItem {
  id: string;
  message: string;
  timestamp: string;
  type: 'task' | 'agent' | 'system';
  status: 'success' | 'warning' | 'error' | 'info';
}

export default function DashboardSidebar({ activeTab, onTabChange }: DashboardSidebarProps) {
  // API data fetching
  const { data: metrics } = useMetrics();
  const { data: systemStatus } = useSystemStatus();
  const { data: tasks } = useTasks();
  const { data: agents } = useAgents();

  // Real-time updates
  const { taskUpdates } = useTaskUpdates();
  const { agentUpdates } = useAgentUpdates();
  const { metrics: liveMetrics } = useSystemMetricsUpdates();

  // Local state for processed data
  const [activeTasks, setActiveTasks] = useState(0);
  const [onlineAgents, setOnlineAgents] = useState({ online: 0, total: 0 });
  const [successRate, setSuccessRate] = useState(0);
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);

  // Process active tasks count
  useEffect(() => {
    if (tasks) {
      const activeCount = tasks.filter(task => 
        task.status === 'in_progress' || task.status === 'pending'
      ).length;
      setActiveTasks(activeCount);
    }
  }, [tasks, taskUpdates]);

  // Process agent status
  useEffect(() => {
    if (agents) {
      const online = agents.filter(agent => 
        agent.status === 'idle' || agent.status === 'busy'
      ).length;
      setOnlineAgents({ online, total: agents.length });
    }
  }, [agents, agentUpdates]);

  // Calculate success rate
  useEffect(() => {
    if (metrics) {
      setSuccessRate(metrics.success_rate || 0);
    } else if (tasks && tasks.length > 0) {
      const completed = tasks.filter(task => task.status === 'completed').length;
      const total = tasks.filter(task => task.status !== 'pending').length;
      const rate = total > 0 ? (completed / total) * 100 : 0;
      setSuccessRate(Math.round(rate * 10) / 10);
    }
  }, [metrics, tasks, taskUpdates]);

  // Process recent activity from real-time updates
  useEffect(() => {
    const activities: ActivityItem[] = [];

    // Add task updates
    taskUpdates.slice(-5).forEach((update) => {
      const task = tasks?.find(t => t.id === update.task_id);
      if (task) {
        activities.push({
          id: `task-${update.id}`,
          message: `Task "${task.title || task.description}" ${update.status}`,
          timestamp: getRelativeTime(update.timestamp),
          type: 'task',
          status: update.status === 'completed' ? 'success' : 
                  update.status === 'failed' ? 'error' : 'info'
        });
      }
    });

    // Add agent updates
    agentUpdates.slice(-3).forEach((update) => {
      const agent = agents?.find(a => a.id === update.agent_id);
      if (agent && activities.length < 8) {
        const statusText = update.status === 'busy' ? 'started working' :
                          update.status === 'idle' ? 'became idle' :
                          update.status === 'offline' ? 'went offline' : 'came online';
        
        activities.push({
          id: `agent-${update.id}`,
          message: `Agent "${agent.name}" ${statusText}`,
          timestamp: getRelativeTime(update.timestamp),
          type: 'agent',
          status: update.status === 'error' ? 'error' : 'info'
        });
      }
    });

    // Sort by timestamp (most recent first)
    activities.sort((a, b) => {
      const timeA = parseRelativeTime(a.timestamp);
      const timeB = parseRelativeTime(b.timestamp);
      return timeA - timeB;
    });

    setRecentActivity(activities.slice(0, 6));
  }, [taskUpdates, agentUpdates, tasks, agents]);

  // Helper functions
  const getRelativeTime = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = now.getTime() - time.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`;
    return `${Math.floor(minutes / 1440)}d ago`;
  };

  const parseRelativeTime = (relativeTime: string): number => {
    if (relativeTime === 'Just now') return 0;
    const match = relativeTime.match(/(\d+)([mhd])/);
    if (!match) return 0;
    const [, num, unit] = match;
    const value = parseInt(num);
    switch (unit) {
      case 'm': return value;
      case 'h': return value * 60;
      case 'd': return value * 1440;
      default: return 0;
    }
  };

  const navItems: NavItem[] = [
    { id: 'overview', label: 'Overview', icon: HomeIcon },
    { id: 'analytics', label: 'Analytics', icon: ChartBarIcon },
    { id: 'tasks', label: 'Tasks', icon: ListBulletIcon, badge: activeTasks > 0 ? activeTasks : undefined },
    { id: 'agents', label: 'Agents', icon: UserGroupIcon },
    { id: 'settings', label: 'Settings', icon: Cog6ToothIcon },
  ];

  const quickStats: QuickStat[] = [
    {
      label: 'Active Tasks',
      value: activeTasks.toString(),
      trend: activeTasks > 5 ? 'up' : 'neutral',
      icon: ListBulletIcon,
      color: 'text-blue-400'
    },
    {
      label: 'Agents Online',
      value: `${onlineAgents.online}/${onlineAgents.total}`,
      trend: onlineAgents.online > onlineAgents.total * 0.8 ? 'up' : 'neutral',
      icon: UserGroupIcon,
      color: 'text-green-400'
    },
    {
      label: 'Success Rate',
      value: `${successRate}%`,
      trend: successRate > 90 ? 'up' : successRate < 70 ? 'down' : 'neutral',
      icon: ArrowTrendingUpIcon,
      color: 'text-purple-400'
    }
  ];

  const getStatusIcon = (status: ActivityItem['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="w-4 h-4 text-green-400" />;
      case 'warning':
        return <ExclamationTriangleIcon className="w-4 h-4 text-yellow-400" />;
      case 'error':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-400" />;
      default:
        return <ClockIcon className="w-4 h-4 text-blue-400" />;
    }
  };

  const getTrendIcon = (trend: QuickStat['trend']) => {
    if (trend === 'up') {
      return <ArrowTrendingUpIcon className="w-4 h-4 text-green-400" />;
    } else if (trend === 'down') {
      return <ArrowTrendingUpIcon className="w-4 h-4 text-red-400 transform rotate-180" />;
    }
    return null;
  };

  return (
    <div className="w-72 bg-gray-900 border-r border-gray-700 flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-xl font-bold text-white">Dashboard</h1>
        <p className="text-sm text-gray-400 mt-1">Analytics & Management</p>
        {liveMetrics && (
          <div className="flex items-center mt-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
            <span className="text-xs text-green-400">Live updates</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="px-4 py-6">
        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  isActive
                    ? 'bg-purple-900/30 text-purple-300 border border-purple-600/50'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5 mr-3" />
                <span className="flex-1 text-left">{item.label}</span>
                {item.badge && (
                  <span className="ml-2 bg-purple-600 text-white text-xs px-2 py-1 rounded-full">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Quick Stats */}
      <div className="px-4 py-4 border-t border-gray-700">
        <h3 className="text-sm font-medium text-gray-400 mb-3">Quick Stats</h3>
        <div className="space-y-3">
          {quickStats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-800/50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Icon className={`w-4 h-4 ${stat.color}`} />
                  <span className="text-xs text-gray-300">{stat.label}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <span className="text-sm font-medium text-white">{stat.value}</span>
                  {getTrendIcon(stat.trend)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="flex-1 px-4 py-4 border-t border-gray-700 overflow-hidden">
        <h3 className="text-sm font-medium text-gray-400 mb-3">Recent Activity</h3>
        <div className="space-y-3 overflow-y-auto">
          {recentActivity.length > 0 ? (
            recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-2 p-2 bg-gray-800/30 rounded-lg">
                <div className="flex-shrink-0 mt-0.5">
                  {getStatusIcon(activity.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-300 truncate">{activity.message}</p>
                  <p className="text-xs text-gray-500 mt-1">{activity.timestamp}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-4">
              <p className="text-xs text-gray-500">No recent activity</p>
            </div>
          )}
        </div>
      </div>

      {/* System Status Footer */}
      <div className="px-4 py-4 border-t border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              systemStatus?.status === 'healthy' ? 'bg-green-400' :
              systemStatus?.status === 'warning' ? 'bg-yellow-400' : 'bg-red-400'
            }`}></div>
            <span className="text-xs text-gray-400">
              System {systemStatus?.status || 'unknown'}
            </span>
          </div>
          <span className="text-xs text-gray-500">
            v{systemStatus?.version || '1.0.0'}
          </span>
        </div>
      </div>
    </div>
  );
} 