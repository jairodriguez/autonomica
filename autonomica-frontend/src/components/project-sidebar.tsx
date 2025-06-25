'use client';

import { useState } from 'react';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { 
  FolderIcon, 
  FolderOpenIcon, 
  UserIcon, 
  ClockIcon 
} from '@heroicons/react/24/solid';

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  model: string;
  lastActive: string;
  tasksCompleted: number;
  currentTask?: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  agents: Agent[];
  isExpanded?: boolean;
}

interface ProjectSidebarProps {
  projects: Project[];
  selectedProjectId?: string;
  selectedAgentId?: string;
  onProjectSelect: (projectId: string) => void;
  onAgentSelect: (projectId: string, agentId: string) => void;
  className?: string;
}

const StatusIcon = ({ status }: { status: Agent['status'] }) => {
  const baseClasses = "w-3 h-3";
  
  switch (status) {
    case 'busy':
      return (
        <div className={`${baseClasses} relative`}>
          <ClockIcon className="w-3 h-3 text-purple-400 animate-spin" />
        </div>
      );
    case 'idle':
      return <div className={`${baseClasses} bg-green-400 rounded-full`} />;
    case 'error':
      return <div className={`${baseClasses} bg-red-400 rounded-full`} />;
    case 'offline':
      return <div className={`${baseClasses} bg-gray-500 rounded-full`} />;
    default:
      return <div className={`${baseClasses} bg-gray-500 rounded-full`} />;
  }
};

const AgentItem = ({ 
  agent, 
  projectId, 
  isSelected, 
  onSelect 
}: { 
  agent: Agent; 
  projectId: string; 
  isSelected: boolean; 
  onSelect: (projectId: string, agentId: string) => void; 
}) => {
  return (
    <div
      onClick={() => onSelect(projectId, agent.id)}
      className={`
        flex items-center space-x-3 px-3 py-2 ml-6 rounded-lg cursor-pointer transition-colors
        ${isSelected 
          ? 'bg-purple-900/30 border border-purple-600/50' 
          : 'hover:bg-gray-700/50'
        }
      `}
    >
      <UserIcon className="w-4 h-4 text-gray-400" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-100 truncate">
            {agent.name}
          </span>
          <StatusIcon status={agent.status} />
        </div>
        <div className="text-xs text-gray-400 truncate">
          {agent.type} • {agent.model}
        </div>
        {agent.currentTask && (
          <div className="text-xs text-purple-400 truncate mt-1">
            {agent.currentTask}
          </div>
        )}
      </div>
    </div>
  );
};

export default function ProjectSidebar({
  projects,
  selectedProjectId,
  selectedAgentId,
  onProjectSelect,
  onAgentSelect,
  className = ''
}: ProjectSidebarProps) {
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());

  const toggleProject = (projectId: string) => {
    const newExpanded = new Set(expandedProjects);
    if (newExpanded.has(projectId)) {
      newExpanded.delete(projectId);
    } else {
      newExpanded.add(projectId);
    }
    setExpandedProjects(newExpanded);
  };

  const handleProjectClick = (projectId: string) => {
    onProjectSelect(projectId);
    toggleProject(projectId);
  };

  return (
    <div className={`w-72 bg-gray-900 border-r border-gray-700 overflow-y-auto ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-gray-100">Projects</h2>
        <p className="text-sm text-gray-400">Manage your AI agent workforce</p>
      </div>

      {/* Projects List */}
      <div className="p-2">
        {projects.map((project) => {
          const isExpanded = expandedProjects.has(project.id);
          const isSelected = selectedProjectId === project.id;
          const activeAgents = project.agents.filter(a => a.status === 'busy').length;
          const totalAgents = project.agents.length;

          return (
            <div key={project.id} className="mb-2">
              {/* Project Header */}
              <div
                onClick={() => handleProjectClick(project.id)}
                className={`
                  flex items-center space-x-2 px-3 py-2 rounded-lg cursor-pointer transition-colors
                  ${isSelected 
                    ? 'bg-purple-900/30 border border-purple-600/50' 
                    : 'hover:bg-gray-800/50'
                  }
                `}
              >
                <div className="flex items-center space-x-2 flex-1">
                  {isExpanded ? (
                    <ChevronDownIcon className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronRightIcon className="w-4 h-4 text-gray-400" />
                  )}
                  {isExpanded ? (
                    <FolderOpenIcon className="w-5 h-5 text-purple-400" />
                  ) : (
                    <FolderIcon className="w-5 h-5 text-gray-400" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-100 truncate">
                      {project.name}
                    </div>
                    <div className="text-xs text-gray-400 truncate">
                      {activeAgents}/{totalAgents} agents active
                    </div>
                  </div>
                </div>
              </div>

              {/* Agents List */}
              {isExpanded && (
                <div className="mt-2 space-y-1">
                  {project.agents.map((agent) => (
                    <AgentItem
                      key={agent.id}
                      agent={agent}
                      projectId={project.id}
                      isSelected={selectedAgentId === agent.id}
                      onSelect={onAgentSelect}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Stats */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gray-800 border-t border-gray-700">
        <div className="text-xs text-gray-400">
          <div className="flex justify-between">
            <span>Total Projects:</span>
            <span>{projects.length}</span>
          </div>
          <div className="flex justify-between">
            <span>Active Agents:</span>
            <span>
              {projects.reduce((acc, p) => 
                acc + p.agents.filter(a => a.status === 'busy').length, 0
              )}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
} 