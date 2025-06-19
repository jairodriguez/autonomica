'use client';

import { useState, useEffect } from 'react';
import ProjectSidebar, { type Agent, type Project } from './project-sidebar';
import ProjectMainPanel from './project-main-panel';

// Mock data - in a real app, this would come from your API
const generateMockProjects = (): Project[] => [
  {
    id: 'marketing-campaign',
    name: 'Marketing Campaign Q1',
    description: 'Comprehensive marketing campaign for Q1 2024 product launch',
    agents: [
      {
        id: 'ceo-1',
        name: 'CEO Agent',
        type: 'CEO',
        status: 'busy',
        model: 'gpt-4o',
        lastActive: '2 minutes ago',
        tasksCompleted: 24,
        currentTask: 'Reviewing marketing strategy document'
      },
      {
        id: 'marketing-1',
        name: 'Marketing Strategist',
        type: 'Marketing',
        status: 'idle',
        model: 'claude-3-5-sonnet',
        lastActive: '5 minutes ago',
        tasksCompleted: 18
      },
      {
        id: 'content-1',
        name: 'Content Creator',
        type: 'Content',
        status: 'busy',
        model: 'gpt-4o-mini',
        lastActive: '1 minute ago',
        tasksCompleted: 32,
        currentTask: 'Writing blog post about AI trends'
      },
      {
        id: 'seo-1',
        name: 'SEO Specialist',
        type: 'SEO',
        status: 'idle',
        model: 'claude-3-haiku',
        lastActive: '10 minutes ago',
        tasksCompleted: 15
      }
    ]
  },
  {
    id: 'product-research',
    name: 'Product Research',
    description: 'Market research and competitive analysis for new product features',
    agents: [
      {
        id: 'research-1',
        name: 'Research Analyst',
        type: 'Research',
        status: 'busy',
        model: 'gpt-4o',
        lastActive: '30 seconds ago',
        tasksCompleted: 8,
        currentTask: 'Analyzing competitor pricing strategies'
      },
      {
        id: 'data-1',
        name: 'Data Analyst',
        type: 'Analytics',
        status: 'idle',
        model: 'claude-3-5-sonnet',
        lastActive: '15 minutes ago',
        tasksCompleted: 12
      },
      {
        id: 'ux-1',
        name: 'UX Researcher',
        type: 'UX',
        status: 'error',
        model: 'gpt-4o-mini',
        lastActive: '2 hours ago',
        tasksCompleted: 5
      }
    ]
  },
  {
    id: 'social-media',
    name: 'Social Media Management',
    description: 'Daily social media content creation and engagement management',
    agents: [
      {
        id: 'social-1',
        name: 'Social Media Manager',
        type: 'Social',
        status: 'idle',
        model: 'gpt-4o-mini',
        lastActive: '1 hour ago',
        tasksCompleted: 45
      },
      {
        id: 'community-1',
        name: 'Community Manager',
        type: 'Community',
        status: 'offline',
        model: 'claude-3-haiku',
        lastActive: '1 day ago',
        tasksCompleted: 22
      }
    ]
  }
];

interface ProjectLayoutProps {
  className?: string;
}

export default function ProjectLayout({ className = '' }: ProjectLayoutProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>();
  const [selectedAgentId, setSelectedAgentId] = useState<string>();
  
  // Simulate real-time updates
  useEffect(() => {
    setProjects(generateMockProjects());
    
    // Simulate agent status updates
    const interval = setInterval(() => {
      setProjects(prevProjects => 
        prevProjects.map(project => ({
          ...project,
          agents: project.agents.map(agent => {
            // Randomly update agent status (simulate real work)
            const shouldUpdate = Math.random() < 0.1; // 10% chance per update
            if (!shouldUpdate) return agent;
            
            const statuses: Agent['status'][] = ['idle', 'busy', 'error', 'offline'];
            const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
            
            return {
              ...agent,
              status: randomStatus,
              lastActive: randomStatus === 'busy' ? 'now' : agent.lastActive,
              currentTask: randomStatus === 'busy' ? 
                `Working on task ${Math.floor(Math.random() * 100)}` : 
                undefined
            };
          })
        }))
      );
    }, 3000); // Update every 3 seconds
    
    return () => clearInterval(interval);
  }, []);

  const selectedProject = projects.find(p => p.id === selectedProjectId);
  const selectedAgent = selectedProject?.agents.find(a => a.id === selectedAgentId);

  const handleProjectSelect = (projectId: string) => {
    setSelectedProjectId(projectId);
    setSelectedAgentId(undefined); // Clear agent selection when project changes
  };

  const handleAgentSelect = (projectId: string, agentId: string) => {
    setSelectedProjectId(projectId);
    setSelectedAgentId(agentId);
  };

  const handleAgentAction = (agentId: string, action: 'start' | 'pause' | 'stop') => {
    setProjects(prevProjects => 
      prevProjects.map(project => ({
        ...project,
        agents: project.agents.map(agent => 
          agent.id === agentId ? {
            ...agent,
            status: action === 'start' ? 'busy' : 
                   action === 'pause' ? 'idle' : 'offline',
            currentTask: action === 'start' ? 'Starting new task...' : undefined,
            lastActive: 'now'
          } : agent
        )
      }))
    );
  };

  return (
    <div className={`flex h-screen bg-gray-900 ${className}`}>
      {/* Sidebar */}
      <ProjectSidebar
        projects={projects}
        selectedProjectId={selectedProjectId}
        selectedAgentId={selectedAgentId}
        onProjectSelect={handleProjectSelect}
        onAgentSelect={handleAgentSelect}
        className="relative border-r border-gray-700"
      />
      
      {/* Main Content Area */}
      <ProjectMainPanel
        selectedProject={selectedProject}
        selectedAgent={selectedAgent}
        onAgentAction={handleAgentAction}
        className="flex-1 bg-gray-800"
      />
    </div>
  );
} 