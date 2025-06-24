'use client';

import { 
  ChartBarIcon, 
  ClockIcon, 
  CheckCircleIcon, 
  UserGroupIcon,
  CpuChipIcon,
  BanknotesIcon
} from '@heroicons/react/24/outline';
import { MetricCard, LineChart, AreaChart, DonutChart } from '@/components';
import { useMetrics, useSystemStatus, useTasks, useAgents } from '@/hooks/useApi';
import { useTaskUpdates, useAgentUpdates, useSystemMetricsUpdates } from '@/hooks/useSocket';
import { useEffect, useState } from 'react';

interface RecentTask {
  id: string;
  title: string;
  status: 'completed' | 'in_progress' | 'failed' | 'pending';
  agent: string;
  duration: string;
  timestamp: string;
}

interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: string | number;
}

export default function OverviewTab() {
  // API data fetching
  const { data: metrics, error: metricsError, isLoading: metricsLoading } = useMetrics();
  const { error: systemError, isLoading: systemLoading } = useSystemStatus();
  const { data: tasks, error: tasksError } = useTasks();
  const { data: agents, error: agentsError } = useAgents();

  // Real-time updates
  const { taskUpdates } = useTaskUpdates();
  const { agentUpdates } = useAgentUpdates();
  const { metrics: liveMetrics } = useSystemMetricsUpdates();

  // Local state for processed data
  const [taskPerformanceData, setTaskPerformanceData] = useState<ChartDataPoint[]>([]);
  const [agentActivityData, setAgentActivityData] = useState<ChartDataPoint[]>([]);
  const [systemMetricsData, setSystemMetricsData] = useState<ChartDataPoint[]>([]);
  const [recentTasks, setRecentTasks] = useState<RecentTask[]>([]);

  // Process task performance data for the last 7 days
  useEffect(() => {
    if (tasks) {
      const last7Days = Array.from({ length: 7 }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (6 - i));
        return date.toLocaleDateString('en-US', { weekday: 'short' });
      });

      const taskCounts = last7Days.map(day => {
        // In a real implementation, you'd filter tasks by date
        // For now, we'll generate sample data based on total tasks
        const count = Math.floor(Math.random() * 30) + 10;
        return { name: day, value: count };
      });

      setTaskPerformanceData(taskCounts);
    }
  }, [tasks]);

  // Process agent activity data
  useEffect(() => {
    if (agents) {
      const activityData = agents
        .filter(agent => agent.status !== 'offline')
        .map(agent => ({
          name: agent.name,
          value: Math.floor(Math.random() * 40) + 10 // Sample task count per agent
        }))
        .slice(0, 5); // Top 5 agents

      setAgentActivityData(activityData);
    }
  }, [agents, agentUpdates]);

  // Process system metrics data for the last 24 hours
  useEffect(() => {
    const hours = Array.from({ length: 7 }, (_, i) => {
      const hour = (new Date().getHours() - (6 - i) * 4) % 24;
      return `${hour.toString().padStart(2, '0')}:00`;
    });

    const baseMetrics = liveMetrics || {
      cpu_usage: 65,
      memory_usage: 72,
      active_tasks: 0,
      active_agents: 0,
      requests_per_minute: 0,
      token_usage: 0,
      timestamp: new Date().toISOString()
    };

    const metricsData = hours.map(hour => ({
      name: hour,
      value: Math.floor(baseMetrics.cpu_usage + (Math.random() - 0.5) * 20)
    }));

    setSystemMetricsData(metricsData);
  }, [liveMetrics]);

  // Process recent tasks
  useEffect(() => {
    if (tasks) {
      const recent = tasks
        .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
        .slice(0, 5)
        .map(task => ({
          id: task.id,
          title: task.title || task.description,
          status: task.status as RecentTask['status'],
          agent: agents?.find(agent => agent.id === task.agent_id)?.name || 'Unknown Agent',
          duration: calculateDuration(task.created_at, task.updated_at),
          timestamp: getRelativeTime(task.updated_at)
        }));

      setRecentTasks(recent);
    }
  }, [tasks, agents, taskUpdates]);

  // Helper functions
  const calculateDuration = (start: string, end: string) => {
    const diff = new Date(end).getTime() - new Date(start).getTime();
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  const getRelativeTime = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = now.getTime() - time.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes} minutes ago`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)} hours ago`;
    return `${Math.floor(minutes / 1440)} days ago`;
  };

  const getStatusColor = (status: RecentTask['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'pending':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // Handle loading states
  if (metricsLoading || systemLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
          <span className="ml-3 text-gray-400">Loading dashboard data...</span>
        </div>
      </div>
    );
  }

  // Handle error states
  if (metricsError || systemError || tasksError || agentsError) {
    return (
      <div className="p-6">
        <div className="bg-red-900/30 border border-red-600/30 rounded-lg p-6">
          <h3 className="text-red-400 font-medium mb-2">Dashboard Error</h3>
          <p className="text-red-300 text-sm">
            Unable to load dashboard data. Please check your connection and try again.
          </p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Dashboard Overview</h1>
        <p className="text-gray-400">Monitor your AI marketing team performance and system metrics</p>
        {liveMetrics && (
          <div className="flex items-center mt-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
            <span className="text-sm text-green-400">Live data updates active</span>
          </div>
        )}
      </div>

      {/* KPI Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <MetricCard
          title="Total Tasks"
          value={metrics?.total_tasks?.toString() || "0"}
          change={12}
          trend="up"
          icon={ChartBarIcon}
          color="#3b82f6"
        />
        <MetricCard
          title="Active Tasks"
          value={metrics?.active_tasks?.toString() || liveMetrics?.active_tasks?.toString() || "0"}
          change="3"
          trend="up"
          icon={ClockIcon}
          color="#f59e0b"
        />
        <MetricCard
          title="Completed Today"
          value={metrics?.completed_today?.toString() || "0"}
          change={24}
          trend="up"
          icon={CheckCircleIcon}
          color="#10b981"
        />
        <MetricCard
          title="Active Agents"
          value={`${metrics?.active_agents || liveMetrics?.active_agents || 0}/${metrics?.total_agents || 0}`}
          change={`${Math.round(((metrics?.active_agents || 0) / (metrics?.total_agents || 1)) * 100)}%`}
          trend="neutral"
          icon={UserGroupIcon}
          color="#8b5cf6"
          subtitle="uptime"
        />
        <MetricCard
          title="CPU Usage"
          value={`${Math.round(liveMetrics?.cpu_usage || metrics?.cpu_usage || 0)}%`}
          change={-5}
          trend="down"
          icon={CpuChipIcon}
          color="#6366f1"
        />
        <MetricCard
          title="Token Cost"
          value={`$${(metrics?.token_cost_today || 0).toFixed(2)}`}
          change={8}
          trend="up"
          icon={BanknotesIcon}
          color="#eab308"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Task Performance Chart */}
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Task Performance (7 days)</h3>
          <LineChart 
            data={taskPerformanceData}
            height={250}
            color="#8b5cf6"
            showGrid={true}
          />
        </div>

        {/* Agent Activity Chart */}
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Agent Activity Distribution</h3>
          <DonutChart 
            data={agentActivityData}
            height={250}
            showLegend={true}
            centerText="Active Agents"
            centerValue={agentActivityData.length.toString()}
          />
        </div>
      </div>

      {/* System Metrics and Recent Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Resource Usage */}
        <div className="lg:col-span-2 bg-gray-900 border border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">System Resource Usage (24h)</h3>
          <AreaChart 
            data={systemMetricsData}
            height={200}
            color="#6366f1"
            showGrid={true}
          />
        </div>

        {/* Recent Tasks */}
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Recent Tasks</h3>
          <div className="space-y-3">
            {recentTasks.length > 0 ? (
              recentTasks.map((task) => (
                <div key={task.id} className="bg-gray-800 border border-gray-700 rounded p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {task.title}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {task.agent} • {task.duration}
                      </p>
                    </div>
                    <span className={`ml-2 px-2 py-1 text-xs rounded border ${getStatusColor(task.status)}`}>
                      {task.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{task.timestamp}</p>
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-400 text-sm">No recent tasks</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 