'use client';

import { 
  ListBulletIcon, 
  FunnelIcon,
  MagnifyingGlassIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PlayIcon
} from '@heroicons/react/24/outline';
import { useTasks, useAgents } from '@/hooks/useApi';
import { useTaskUpdates } from '@/hooks/useSocket';
import { useState, useMemo } from 'react';

type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed';
type FilterStatus = 'all' | TaskStatus;

export default function TasksTab() {
  const { data: tasks, error: tasksError, isLoading: tasksLoading } = useTasks();
  const { data: agents } = useAgents();
  const { taskUpdates } = useTaskUpdates();

  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'created_at' | 'priority' | 'status'>('created_at');

  // Filter and sort tasks
  const filteredTasks = useMemo(() => {
    if (!tasks) return [];

    let filtered = tasks;

    // Filter by status
    if (filterStatus !== 'all') {
      filtered = filtered.filter(task => task.status === filterStatus);
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(task => 
        (task.title?.toLowerCase().includes(query)) ||
        task.description.toLowerCase().includes(query)
      );
    }

    // Sort tasks
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'priority':
          const priorityOrder = { 'high': 3, 'medium': 2, 'low': 1 };
          return (priorityOrder[b.priority as keyof typeof priorityOrder] || 1) - 
                 (priorityOrder[a.priority as keyof typeof priorityOrder] || 1);
        case 'status':
          return a.status.localeCompare(b.status);
        case 'created_at':
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

    return filtered;
  }, [tasks, filterStatus, searchQuery, sortBy]);

  // Task status counts
  const statusCounts = useMemo(() => {
    if (!tasks) return { pending: 0, in_progress: 0, completed: 0, failed: 0, total: 0 };
    
    return tasks.reduce((counts, task) => {
      counts[task.status as TaskStatus]++;
      counts.total++;
      return counts;
    }, { pending: 0, in_progress: 0, completed: 0, failed: 0, total: 0 });
  }, [tasks]);

  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="w-4 h-4 text-gray-400" />;
      case 'in_progress':
        return <PlayIcon className="w-4 h-4 text-blue-400" />;
      case 'completed':
        return <CheckCircleIcon className="w-4 h-4 text-green-400" />;
      case 'failed':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-400" />;
      default:
        return <ClockIcon className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'text-red-400';
      case 'medium':
        return 'text-yellow-400';
      case 'low':
        return 'text-green-400';
      default:
        return 'text-gray-400';
    }
  };

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

  if (tasksLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
          <span className="ml-3 text-gray-400">Loading tasks...</span>
        </div>
      </div>
    );
  }

  if (tasksError) {
    return (
      <div className="p-6">
        <div className="bg-red-900/30 border border-red-600/30 rounded-lg p-6">
          <h3 className="text-red-400 font-medium mb-2">Error Loading Tasks</h3>
          <p className="text-red-300 text-sm">
            Unable to load tasks. Please check your connection and try again.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Task Management</h1>
        <p className="text-gray-400">Monitor and manage all AI agent tasks</p>
        {taskUpdates.length > 0 && (
          <div className="flex items-center mt-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
            <span className="text-sm text-green-400">Real-time updates active</span>
          </div>
        )}
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Total</p>
              <p className="text-2xl font-bold text-white">{statusCounts.total}</p>
            </div>
            <ListBulletIcon className="w-8 h-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-blue-900/30 border border-blue-600/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-400">In Progress</p>
              <p className="text-2xl font-bold text-blue-200">{statusCounts.in_progress}</p>
            </div>
            <PlayIcon className="w-8 h-8 text-blue-400" />
          </div>
        </div>
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Pending</p>
              <p className="text-2xl font-bold text-gray-200">{statusCounts.pending}</p>
            </div>
            <ClockIcon className="w-8 h-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-green-900/30 border border-green-600/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-400">Completed</p>
              <p className="text-2xl font-bold text-green-200">{statusCounts.completed}</p>
            </div>
            <CheckCircleIcon className="w-8 h-8 text-green-400" />
          </div>
        </div>
        <div className="bg-red-900/30 border border-red-600/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-400">Failed</p>
              <p className="text-2xl font-bold text-red-200">{statusCounts.failed}</p>
            </div>
            <ExclamationTriangleIcon className="w-8 h-8 text-red-400" />
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        {/* Search */}
        <div className="flex-1">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Status Filter */}
        <div className="flex items-center space-x-2">
          <FunnelIcon className="w-5 h-5 text-gray-400" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {/* Sort */}
        <div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'created_at' | 'priority' | 'status')}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="created_at">Sort by Date</option>
            <option value="priority">Sort by Priority</option>
            <option value="status">Sort by Status</option>
          </select>
        </div>
      </div>

      {/* Tasks List */}
      <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
        {filteredTasks.length > 0 ? (
          <div className="divide-y divide-gray-700">
            {filteredTasks.map((task) => {
              const agent = agents?.find(a => a.id === task.agent_id);
              return (
                <div key={task.id} className="p-6 hover:bg-gray-800/50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start space-x-3">
                        {getStatusIcon(task.status as TaskStatus)}
                        <div className="flex-1">
                          <h3 className="text-lg font-medium text-white truncate">
                            {task.title || task.description}
                          </h3>
                          {task.title && (
                            <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                              {task.description}
                            </p>
                          )}
                          <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                            <span>Created {getRelativeTime(task.created_at)}</span>
                            {agent && <span>Assigned to {agent.name}</span>}
                            <span className={`font-medium ${getPriorityColor(task.priority)}`}>
                              {task.priority} priority
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3 ml-4">
                      <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(task.status as TaskStatus)}`}>
                        {task.status.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-12 text-center">
            <ListBulletIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">No tasks found</h3>
            <p className="text-gray-500">
              {searchQuery || filterStatus !== 'all' 
                ? 'Try adjusting your filters or search query' 
                : 'No tasks have been created yet'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
} 