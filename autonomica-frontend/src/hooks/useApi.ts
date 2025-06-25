import useSWR, { SWRResponse, SWRConfiguration } from 'swr';
import { api } from '@/lib/axios';

// Generic API hook using SWR
export function useApi<T>(
  url: string | null, 
  options?: SWRConfiguration
): SWRResponse<T> & { isLoading: boolean } {
  const fetcher = (url: string) => api.get<T>(url);
  
  const response = useSWR<T>(url, fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: true,
    ...options,
  });

  return {
    ...response,
    isLoading: !response.error && !response.data,
  };
}

// Specialized hooks for different data types
export function useTasks() {
  return useApi<Task[]>('/api/tasks');
}

export function useAgents() {
  return useApi<Agent[]>('/api/agents');
}

export function useProjects() {
  return useApi<Project[]>('/api/projects');
}

export function useMetrics() {
  return useApi<DashboardMetrics>('/api/metrics', {
    refreshInterval: 5000, // Refresh every 5 seconds
  });
}

export function useSystemStatus() {
  return useApi<SystemStatus>('/api/system/status', {
    refreshInterval: 10000, // Refresh every 10 seconds
  });
}

// Hook for task details with dependencies
export function useTask(taskId: string | null) {
  return useApi<TaskDetail>(taskId ? `/api/tasks/${taskId}` : null);
}

// Hook for agent details
export function useAgent(agentId: string | null) {
  return useApi<AgentDetail>(agentId ? `/api/agents/${agentId}` : null);
}

// Hook for project details
export function useProject(projectId: string | null) {
  return useApi<ProjectDetail>(projectId ? `/api/projects/${projectId}` : null);
}

// Types for API responses
export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high';
  agent_id?: string;
  project_id?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskDetail extends Task {
  dependencies: Task[];
  subtasks: Task[];
  logs: TaskLog[];
}

export interface TaskLog {
  id: string;
  message: string;
  level: 'info' | 'warning' | 'error';
  timestamp: string;
}

export interface Agent {
  id: string;
  name: string;
  type: string;
  model: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  current_task?: string;
  capabilities: string[];
  created_at: string;
}

export interface AgentDetail extends Agent {
  performance_metrics: {
    tasks_completed: number;
    avg_completion_time: number;
    success_rate: number;
  };
  recent_tasks: Task[];
}

export interface Project {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'paused' | 'completed';
  agent_count: number;
  task_count: number;
  created_at: string;
}

export interface ProjectDetail extends Project {
  agents: Agent[];
  tasks: Task[];
  settings: ProjectSettings;
}

export interface ProjectSettings {
  auto_scaling: boolean;
  max_agents: number;
  priority_queue: boolean;
}

export interface DashboardMetrics {
  total_tasks: number;
  active_tasks: number;
  completed_today: number;
  active_agents: number;
  total_agents: number;
  cpu_usage: number;
  memory_usage: number;
  token_cost_today: number;
  success_rate: number;
}

export interface SystemStatus {
  status: 'healthy' | 'warning' | 'error';
  uptime: number;
  version: string;
  last_health_check: string;
  services: {
    api: 'online' | 'offline';
    database: 'online' | 'offline';
    message_queue: 'online' | 'offline';
    websocket: 'online' | 'offline';
  };
} 