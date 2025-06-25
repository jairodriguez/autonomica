'use client';

import { useState } from 'react';
import ChatContainerAI from './chat-container-ai';
import type { Agent, Project } from './project-sidebar';
import { 
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  CogIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface ProjectMainPanelProps {
  selectedProject?: Project;
  selectedAgent?: Agent;
  onAgentAction?: (agentId: string, action: 'start' | 'pause' | 'stop') => void;
  className?: string;
}

const ProjectOverview = ({ project }: { project: Project }) => {
  const activeAgents = project.agents.filter(a => a.status === 'busy').length;
  const idleAgents = project.agents.filter(a => a.status === 'idle').length;
  const errorAgents = project.agents.filter(a => a.status === 'error').length;
  const offlineAgents = project.agents.filter(a => a.status === 'offline').length;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-100 mb-2">{project.name}</h1>
        <p className="text-gray-400">{project.description}</p>
      </div>

      {/* Agent Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-purple-900/30 border border-purple-600/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-purple-400">Active</p>
              <p className="text-2xl font-bold text-purple-200">{activeAgents}</p>
            </div>
            <ClockIcon className="w-8 h-8 text-purple-400" />
          </div>
        </div>
        <div className="bg-green-900/30 border border-green-600/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-400">Idle</p>
              <p className="text-2xl font-bold text-green-200">{idleAgents}</p>
            </div>
            <CheckCircleIcon className="w-8 h-8 text-green-400" />
          </div>
        </div>
        <div className="bg-red-900/30 border border-red-600/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-400">Error</p>
              <p className="text-2xl font-bold text-red-200">{errorAgents}</p>
            </div>
            <ExclamationTriangleIcon className="w-8 h-8 text-red-400" />
          </div>
        </div>
        <div className="bg-gray-700/30 border border-gray-600/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Offline</p>
              <p className="text-2xl font-bold text-gray-200">{offlineAgents}</p>
            </div>
            <StopIcon className="w-8 h-8 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-100 mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {project.agents.slice(0, 5).map((agent) => (
            <div key={agent.id} className="flex items-center space-x-3 p-3 bg-gray-700/50 rounded-lg">
              <div className={`w-3 h-3 rounded-full ${
                agent.status === 'busy' ? 'bg-purple-400' :
                agent.status === 'idle' ? 'bg-green-400' :
                agent.status === 'error' ? 'bg-red-400' : 'bg-gray-500'
              }`} />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-100">{agent.name}</p>
                <p className="text-xs text-gray-400">
                  {agent.currentTask || `Last active: ${agent.lastActive}`}
                </p>
              </div>
              <div className="text-xs text-gray-500">
                {agent.tasksCompleted} tasks completed
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const AgentDetail = ({ 
  agent, 
  onAction 
}: { 
  agent: Agent; 
  onAction?: (agentId: string, action: 'start' | 'pause' | 'stop') => void;
}) => {
  const [activeTab, setActiveTab] = useState<'chat' | 'stats' | 'config'>('chat');

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'busy': return 'text-purple-300 bg-purple-900/30';
      case 'idle': return 'text-green-300 bg-green-900/30';
      case 'error': return 'text-red-300 bg-red-900/30';
      case 'offline': return 'text-gray-300 bg-gray-700/30';
      default: return 'text-gray-300 bg-gray-700/30';
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Agent Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-100">{agent.name}</h1>
            <p className="text-gray-400">{agent.type}</p>
          </div>
          <div className="flex items-center space-x-3">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(agent.status)}`}>
              {agent.status}
            </span>
            {onAction && (
              <div className="flex space-x-2">
                {agent.status === 'idle' && (
                  <button
                    onClick={() => onAction(agent.id, 'start')}
                    className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                    title="Start Agent"
                  >
                    <PlayIcon className="w-5 h-5" />
                  </button>
                )}
                {agent.status === 'busy' && (
                  <button
                    onClick={() => onAction(agent.id, 'pause')}
                    className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg"
                    title="Pause Agent"
                  >
                    <PauseIcon className="w-5 h-5" />
                  </button>
                )}
                <button
                  onClick={() => onAction(agent.id, 'stop')}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                  title="Stop Agent"
                >
                  <StopIcon className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Current Task */}
        {agent.currentTask && (
          <div className="p-3 bg-purple-900/30 border border-purple-600/30 rounded-lg">
            <p className="text-sm font-medium text-purple-200">Current Task</p>
            <p className="text-sm text-purple-300">{agent.currentTask}</p>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-700">
        <nav className="flex space-x-8 px-6">
          <button
            onClick={() => setActiveTab('chat')}
            className={`py-3 border-b-2 font-medium text-sm ${
              activeTab === 'chat'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
            }`}
          >
            <ChatBubbleLeftRightIcon className="w-4 h-4 inline mr-2" />
            Chat
          </button>
          <button
            onClick={() => setActiveTab('stats')}
            className={`py-3 border-b-2 font-medium text-sm ${
              activeTab === 'stats'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
            }`}
          >
            <ChartBarIcon className="w-4 h-4 inline mr-2" />
            Stats
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`py-3 border-b-2 font-medium text-sm ${
              activeTab === 'config'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
            }`}
          >
            <CogIcon className="w-4 h-4 inline mr-2" />
            Config
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' && (
          <div className="h-full">
            <ChatContainerAI 
              className="h-full"
              agentContext={agent}
              onFinish={(message) => {
                console.log('Agent message completed:', message);
              }}
              onError={(error) => {
                console.error('Agent chat error:', error);
              }}
            />
          </div>
        )}
        
        {activeTab === 'stats' && (
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-100 mb-3">Performance</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-400">Tasks Completed</span>
                    <span className="text-sm font-medium text-gray-200">{agent.tasksCompleted}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-400">Last Active</span>
                    <span className="text-sm font-medium text-gray-200">{agent.lastActive}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-400">Model</span>
                    <span className="text-sm font-medium text-gray-200">{agent.model}</span>
                  </div>
                </div>
              </div>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-100 mb-3">Usage</h3>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-400">98.5%</div>
                  <div className="text-sm text-gray-400">Uptime</div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'config' && (
          <div className="p-6">
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-100 mb-3">Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300">Agent Type</label>
                  <input 
                    type="text" 
                    value={agent.type} 
                    readOnly
                    className="mt-1 block w-full rounded-md border-gray-600 bg-gray-700 text-gray-200 shadow-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300">Model</label>
                  <input 
                    type="text" 
                    value={agent.model} 
                    readOnly
                    className="mt-1 block w-full rounded-md border-gray-600 bg-gray-700 text-gray-200 shadow-sm"
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const WelcomeView = () => {
  return (
    <div className="flex items-center justify-center h-full p-6">
      <div className="text-center max-w-md">
        <div className="mb-6">
          <div className="w-16 h-16 bg-purple-900/30 border border-purple-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <ChatBubbleLeftRightIcon className="w-8 h-8 text-purple-400" />
          </div>
          <h2 className="text-2xl font-bold text-gray-100 mb-2">Welcome to Autonomica</h2>
          <p className="text-gray-400">
            Select a project or agent from the sidebar to start managing your AI workforce.
          </p>
        </div>
        
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-400 space-y-2">
            <div className="flex justify-between">
              <span>Total Projects:</span>
              <span className="font-medium">3</span>
            </div>
            <div className="flex justify-between">
              <span>Total Agents:</span>
              <span className="font-medium">9</span>
            </div>
            <div className="flex justify-between">
              <span>Active Now:</span>
              <span className="font-medium text-purple-400">2</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function ProjectMainPanel({
  selectedProject,
  selectedAgent,
  onAgentAction,
  className = ''
}: ProjectMainPanelProps) {
  if (selectedAgent) {
    return (
      <div className={className}>
        <AgentDetail 
          agent={selectedAgent} 
          onAction={onAgentAction}
        />
      </div>
    );
  }
  
  if (selectedProject) {
    return (
      <div className={className}>
        <ProjectOverview 
          project={selectedProject}
        />
      </div>
    );
  }
  
  return <div className={className}><WelcomeView /></div>;
} 