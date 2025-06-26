'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { io, Socket } from 'socket.io-client';

// Socket connection hook
export function useSocket(url?: string) {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDisabled, setIsDisabled] = useState(false);

  const socketUrl = url || process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'http://localhost:8000';

  useEffect(() => {
    // Skip socket connection if explicitly disabled
    if (process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_DISABLE_WEBSOCKETS === 'true') {
      console.log('[Socket] WebSockets disabled in development mode');
      setIsDisabled(true);
      return;
    }

    try {
      socketRef.current = io(socketUrl, {
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 3, // Reduced attempts
        reconnectionDelay: 1000,
        timeout: 5000, // Reduced timeout
      });

      const socket = socketRef.current;

      socket.on('connect', () => {
        console.log('[Socket] Connected to server');
        setIsConnected(true);
        setError(null);
        setIsDisabled(false);
      });

      socket.on('disconnect', (reason) => {
        console.warn('[Socket] Disconnected:', reason);
        setIsConnected(false);
      });

      socket.on('connect_error', (error) => {
        console.warn('[Socket] Connection error (falling back to polling):', error.message);
        // Don't set error for connection failures in development
        if (process.env.NODE_ENV !== 'development') {
          setError(error.message);
        }
        setIsConnected(false);
      });

      socket.on('reconnect_failed', () => {
        console.warn('[Socket] Failed to reconnect - disabling websockets');
        setIsDisabled(true);
        setIsConnected(false);
      });

    } catch (err) {
      console.warn('[Socket] Failed to initialize:', err);
      setIsDisabled(true);
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
        setIsConnected(false);
      }
    };
  }, [socketUrl]);

  const emit = useCallback((event: string, data?: unknown) => {
    if (isDisabled) return;
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    } else {
      console.warn('[Socket] Cannot emit - not connected');
    }
  }, [isDisabled]);

  const on = useCallback((event: string, callback: (data: unknown) => void) => {
    if (isDisabled) return () => {};
    if (socketRef.current) {
      socketRef.current.on(event, callback);
      return () => socketRef.current?.off(event, callback);
    }
    return () => {};
  }, [isDisabled]);

  const off = useCallback((event: string, callback?: (data: unknown) => void) => {
    if (isDisabled) return;
    if (socketRef.current) {
      if (callback) {
        socketRef.current.off(event, callback);
      } else {
        socketRef.current.off(event);
      }
    }
  }, [isDisabled]);

  return {
    socket: socketRef.current,
    isConnected: isConnected && !isDisabled,
    error: isDisabled ? null : error,
    emit,
    on,
    off,
  };
}

// Hook for real-time task updates
export function useTaskUpdates() {
  const { on, off, isConnected } = useSocket();
  const [taskUpdates, setTaskUpdates] = useState<TaskUpdate[]>([]);

  useEffect(() => {
    const handleTaskUpdate = (data: unknown) => {
      const update = data as TaskUpdate;
      console.log('[Socket] Task update received:', update);
      setTaskUpdates(prev => [...prev.slice(-49), update]); // Keep last 50 updates
    };

    const cleanup = on('task_update', handleTaskUpdate);
    return cleanup;
  }, [on, off]);

  return { taskUpdates, isConnected };
}

// Hook for real-time agent status updates
export function useAgentUpdates() {
  const { on, off, isConnected } = useSocket();
  const [agentUpdates, setAgentUpdates] = useState<AgentUpdate[]>([]);

  useEffect(() => {
    const handleAgentUpdate = (data: unknown) => {
      const update = data as AgentUpdate;
      console.log('[Socket] Agent update received:', update);
      setAgentUpdates(prev => [...prev.slice(-49), update]); // Keep last 50 updates
    };

    const cleanup = on('agent_update', handleAgentUpdate);
    return cleanup;
  }, [on, off]);

  return { agentUpdates, isConnected };
}

// Hook for real-time system metrics
export function useSystemMetricsUpdates() {
  const { on, off, isConnected } = useSocket();
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);

  useEffect(() => {
    const handleMetricsUpdate = (data: unknown) => {
      const update = data as SystemMetrics;
      console.log('[Socket] Metrics update received:', update);
      setMetrics(update);
    };

    const cleanup = on('system_metrics', handleMetricsUpdate);
    return cleanup;
  }, [on, off]);

  return { metrics, isConnected };
}

// Hook for real-time chat/messaging
export function useChatSocket(roomId?: string) {
  const { emit, on, off, isConnected } = useSocket();
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  useEffect(() => {
    if (roomId && isConnected) {
      emit('join_room', { roomId });
    }

    return () => {
      if (roomId && isConnected) {
        emit('leave_room', { roomId });
      }
    };
  }, [roomId, isConnected, emit]);

  useEffect(() => {
    const handleMessage = (data: unknown) => {
      const message = data as ChatMessage;
      console.log('[Socket] Chat message received:', message);
      setMessages(prev => [...prev, message]);
    };

    const cleanup = on('chat_message', handleMessage);
    return cleanup;
  }, [on, off]);

  const sendMessage = useCallback((content: string, type: 'user' | 'agent' = 'user') => {
    if (!roomId) {
      console.warn('[Socket] Cannot send message - no room ID');
      return;
    }

    const message: Omit<ChatMessage, 'id' | 'timestamp'> = {
      content,
      sender: type,
      roomId,
    };

    emit('send_message', message);
  }, [roomId, emit]);

  return {
    messages,
    sendMessage,
    isConnected,
  };
}

// Types for real-time updates
export interface TaskUpdate {
  id: string;
  task_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  timestamp: string;
}

export interface AgentUpdate {
  id: string;
  agent_id: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  current_task?: string;
  performance_metrics?: {
    tasks_completed: number;
    avg_completion_time: number;
    success_rate: number;
  };
  timestamp: string;
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  active_tasks: number;
  active_agents: number;
  requests_per_minute: number;
  token_usage: number;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  roomId: string;
  timestamp: string;
} 