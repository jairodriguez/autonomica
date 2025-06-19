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
  projects: Project[];
  onAgentAction?: (agentId: string, action: 'start' | 'pause' | 'stop') => void;
}

const ProjectOverview = ({ project }: { project: Project }) => {
  const activeAgents = project.agents.filter(a => a.status === 'busy').length;
  const idleAgents = project.agents.filter(a => a.status === 'idle').length;
  const errorAgents = project.agents.filter(a => a.status === 'error').length;
  const offlineAgents = project.agents.filter(a => a.status === 'offline').length;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{project.name}</h1>
        <p className="text-gray-600">{project.description}</p>
      </div>

      {/* Agent Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-600">Active</p>
              <p className="text-2xl font-bold text-blue-900">{activeAgents}</p>
            </div>
            <ClockIcon className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-600">Idle</p>
              <p className="text-2xl font-bold text-green-900">{idleAgents}</p>
            </div>
            <CheckCircleIcon className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-red-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-600">Error</p>
              <p className="text-2xl font-bold text-red-900">{errorAgents}</p>
            </div>
            <ExclamationTriangleIcon className="w-8 h-8 text-red-500" />
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Offline</p>
              <p className="text-2xl font-bold text-gray-900">{offlineAgents}</p>
            </div>
            <StopIcon className="w-8 h-8 text-gray-500" />
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg border p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {project.agents.slice(0, 5).map((agent) => (
            <div key={agent.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className={`w-3 h-3 rounded-full ${
                agent.status === 'busy' ? 'bg-blue-500' :
                agent.status === 'idle' ? 'bg-green-500' :
                agent.status === 'error' ? 'bg-red-500' : 'bg-gray-400'
              }`} />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{agent.name}</p>
                <p className="text-xs text-gray-500">
                  {agent.currentTask || `Last active: ${agent.lastActive}`}
                </p>
              </div>
              <div className="text-xs text-gray-400">
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
      case 'busy': return 'text-blue-600 bg-blue-50';
      case 'idle': return 'text-green-600 bg-green-50';
      case 'error': return 'text-red-600 bg-red-50';
      case 'offline': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Agent Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{agent.name}</h1>
            <p className="text-gray-600">{agent.type}</p>
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
          <div className="p-3 bg-blue-50 rounded-lg">
            <p className="text-sm font-medium text-blue-900">Current Task</p>
            <p className="text-sm text-blue-700">{agent.currentTask}</p>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          <button
            onClick={() => setActiveTab('chat')}
            className={`py-3 border-b-2 font-medium text-sm ${
              activeTab === 'chat'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <ChatBubbleLeftRightIcon className="w-4 h-4 inline mr-2" />
            Chat
          </button>
          <button
            onClick={() => setActiveTab('stats')}
            className={`py-3 border-b-2 font-medium text-sm ${
              activeTab === 'stats'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <ChartBarIcon className="w-4 h-4 inline mr-2" />
            Stats
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`py-3 border-b-2 font-medium text-sm ${
              activeTab === 'config'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
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
              <div className="bg-white rounded-lg border p-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Performance</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Tasks Completed</span>
                    <span className="text-sm font-medium">{agent.tasksCompleted}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Last Active</span>
                    <span className="text-sm font-medium">{agent.lastActive}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Model</span>
                    <span className="text-sm font-medium">{agent.model}</span>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg border p-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Usage</h3>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">98.5%</div>
                  <div className="text-sm text-gray-500">Uptime</div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'config' && (
          <div className="p-6">
            <div className="bg-white rounded-lg border p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Agent Type</label>
                  <input 
                    type="text" 
                    value={agent.type} 
                    readOnly
                    className="mt-1 block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Model</label>
                  <input 
                    type="text" 
                    value={agent.model} 
                    readOnly
                    className="mt-1 block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm"
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

const WelcomeView = ({ projects }: { projects: Project[] }) => {
  const totalAgents = projects.reduce((acc, p) => acc + p.agents.length, 0);
  const activeAgents = projects.reduce((acc, p) => 
    acc + p.agents.filter(a => a.status === 'busy').length, 0
  );

  return (
    <div className="flex items-center justify-center h-full p-6">
      <div className="text-center max-w-md">
        <div className="mb-6">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <ChatBubbleLeftRightIcon className="w-8 h-8 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Autonomica</h2>
          <p className="text-gray-600">
            Select a project or agent from the sidebar to start managing your AI workforce.
          </p>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-500 space-y-2">
            <div className="flex justify-between">
              <span>Total Projects:</span>
              <span className="font-medium">{projects.length}</span>
            </div>
            <div className="flex justify-between">
              <span>Total Agents:</span>
              <span className="font-medium">{totalAgents}</span>
            </div>
            <div className="flex justify-between">
              <span>Active Now:</span>
              <span className="font-medium text-blue-600">{activeAgents}</span>
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
  projects,
  onAgentAction
}: ProjectMainPanelProps) {
  if (selectedAgent) {
    return (
      <AgentDetail 
        agent={selectedAgent} 
        onAction={onAgentAction}
      />
    );
  }
  
  if (selectedProject) {
    return (
      <ProjectOverview 
        project={selectedProject}
      />
    );
  }
  
  return <WelcomeView projects={projects} />;
} 