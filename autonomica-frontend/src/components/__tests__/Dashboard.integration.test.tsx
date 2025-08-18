import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import Dashboard from '../Dashboard'
import { DashboardProvider } from '@/contexts/DashboardContext'
import { AgentProvider } from '@/contexts/AgentContext'
import { UserProvider } from '@/contexts/UserContext'

// Mock external dependencies
jest.mock('@/lib/api', () => ({
  fetchApi: jest.fn(),
}))

jest.mock('@clerk/nextjs', () => ({
  useAuth: () => ({
    isSignedIn: true,
    userId: 'test_user_123',
  }),
  useUser: () => ({
    isSignedIn: true,
    userId: 'test_user_123',
    user: {
      id: 'test_user_123',
      emailAddresses: [{ emailAddress: 'test@example.com' }],
      firstName: 'Test',
      lastName: 'User',
      imageUrl: 'https://example.com/avatar.jpg',
    },
  }),
}))

// Mock API responses
const mockApi = require('@/lib/api')

const mockAgents = [
  {
    id: 'agent_1',
    name: 'Strategy Specialist',
    type: 'STRATEGY',
    model: 'gpt-4',
    status: 'idle',
    is_active: true,
  },
  {
    id: 'agent_2',
    name: 'Content Creator',
    type: 'CONTENT',
    model: 'gpt-4',
    status: 'busy',
    is_active: true,
  },
  {
    id: 'agent_3',
    name: 'Analytics Expert',
    type: 'ANALYTICS',
    model: 'gpt-4',
    status: 'offline',
    is_active: false,
  },
]

const mockProjects = [
  {
    id: 'project_1',
    name: 'Marketing Campaign 2025',
    status: 'active',
    progress: 75,
    agents: ['agent_1', 'agent_2'],
  },
  {
    id: 'project_2',
    name: 'SEO Optimization',
    status: 'planning',
    progress: 25,
    agents: ['agent_3'],
  },
]

const mockAnalytics = {
  total_agents: 3,
  active_agents: 2,
  total_projects: 2,
  completed_tasks: 15,
  pending_tasks: 8,
}

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <UserProvider>
    <AgentProvider>
      <DashboardProvider>
        {children}
      </DashboardProvider>
    </AgentProvider>
  </UserProvider>
)

describe('Dashboard Integration Tests', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks()
    
    // Setup default API responses
    mockApi.fetchApi.mockImplementation((endpoint: string) => {
      if (endpoint.includes('/agents')) {
        return Promise.resolve(mockAgents)
      }
      if (endpoint.includes('/projects')) {
        return Promise.resolve(mockProjects)
      }
      if (endpoint.includes('/analytics')) {
        return Promise.resolve(mockAnalytics)
      }
      return Promise.resolve({})
    })
  })

  describe('Component Integration', () => {
    it('renders all dashboard components and integrates them properly', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      // Wait for components to load
      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      // Check that all main sections are rendered
      expect(screen.getByText('Overview')).toBeInTheDocument()
      expect(screen.getByText('Active Agents')).toBeInTheDocument()
      expect(screen.getByText('Recent Projects')).toBeInTheDocument()
      expect(screen.getByText('Quick Actions')).toBeInTheDocument()
    })

    it('displays agent status and integrates with agent management', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Strategy Specialist')).toBeInTheDocument()
        expect(screen.getByText('Content Creator')).toBeInTheDocument()
        expect(screen.getByText('Analytics Expert')).toBeInTheDocument()
      })

      // Check agent status indicators
      expect(screen.getByText('idle')).toBeInTheDocument()
      expect(screen.getByText('busy')).toBeInTheDocument()
      expect(screen.getByText('offline')).toBeInTheDocument()

      // Test agent interaction
      const strategyAgent = screen.getByText('Strategy Specialist').closest('div')
      if (strategyAgent) {
        fireEvent.click(strategyAgent)
        // Should open agent details or trigger some action
      }
    })

    it('integrates project management with agent allocation', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Marketing Campaign 2025')).toBeInTheDocument()
        expect(screen.getByText('SEO Optimization')).toBeInTheDocument()
      })

      // Check project progress
      expect(screen.getByText('75%')).toBeInTheDocument()
      expect(screen.getByText('25%')).toBeInTheDocument()

      // Test project interaction
      const marketingProject = screen.getByText('Marketing Campaign 2025').closest('div')
      if (marketingProject) {
        fireEvent.click(marketingProject)
        // Should show project details with assigned agents
      }
    })

    it('integrates analytics with real-time data updates', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument() // Total agents
        expect(screen.getByText('2')).toBeInTheDocument() // Active agents
        expect(screen.getByText('2')).toBeInTheDocument() // Total projects
      })

      // Check that analytics are displayed correctly
      expect(screen.getByText('Total Agents')).toBeInTheDocument()
      expect(screen.getByText('Active Agents')).toBeInTheDocument()
      expect(screen.getByText('Total Projects')).toBeInTheDocument()
      expect(screen.getByText('Completed Tasks')).toBeInTheDocument()
      expect(screen.getByText('Pending Tasks')).toBeInTheDocument()
    })
  })

  describe('User Interaction Integration', () => {
    it('integrates quick actions with other dashboard components', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Quick Actions')).toBeInTheDocument()
      })

      // Test quick action buttons
      const createProjectButton = screen.getByText('Create Project')
      const addAgentButton = screen.getByText('Add Agent')
      const runAnalysisButton = screen.getByText('Run Analysis')

      expect(createProjectButton).toBeInTheDocument()
      expect(addAgentButton).toBeInTheDocument()
      expect(runAnalysisButton).toBeInTheDocument()

      // Test button interactions
      fireEvent.click(createProjectButton)
      // Should open project creation modal or navigate to project creation page

      fireEvent.click(addAgentButton)
      // Should open agent creation modal or navigate to agent creation page

      fireEvent.click(runAnalysisButton)
      // Should trigger analysis workflow
    })

    it('integrates search and filtering across components', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Search agents, projects.../i)).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/Search agents, projects.../i)
      
      // Test search functionality
      fireEvent.change(searchInput, { target: { value: 'Strategy' } })
      
      // Should filter agents and projects based on search
      await waitFor(() => {
        expect(screen.getByText('Strategy Specialist')).toBeInTheDocument()
        // Should hide or highlight other items
      })

      // Clear search
      fireEvent.change(searchInput, { target: { value: '' } })
      
      // Should show all items again
      await waitFor(() => {
        expect(screen.getByText('Content Creator')).toBeInTheDocument()
        expect(screen.getByText('Analytics Expert')).toBeInTheDocument()
      })
    })

    it('integrates notification system with user actions', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Notifications')).toBeInTheDocument()
      })

      // Test notification interactions
      const notificationButton = screen.getByText('Notifications')
      fireEvent.click(notificationButton)

      // Should show notification panel or dropdown
      // Check for notification items
      expect(screen.getByText(/No new notifications/i)).toBeInTheDocument()
    })
  })

  describe('Data Flow Integration', () => {
    it('maintains data consistency across component updates', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Strategy Specialist')).toBeInTheDocument()
      })

      // Simulate agent status update
      const updatedAgents = mockAgents.map(agent => 
        agent.id === 'agent_1' 
          ? { ...agent, status: 'busy' }
          : agent
      )

      mockApi.fetchApi.mockImplementation((endpoint: string) => {
        if (endpoint.includes('/agents')) {
          return Promise.resolve(updatedAgents)
        }
        return Promise.resolve({})
      })

      // Trigger refresh or wait for auto-update
      const refreshButton = screen.getByText('Refresh')
      if (refreshButton) {
        fireEvent.click(refreshButton)
      }

      // Check that the status update is reflected
      await waitFor(() => {
        expect(screen.getByText('busy')).toBeInTheDocument()
      })
    })

    it('handles error states and integrates error handling', async () => {
      // Mock API error
      mockApi.fetchApi.mockRejectedValue(new Error('API Error'))

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      // Should show error state
      await waitFor(() => {
        expect(screen.getByText(/Error loading dashboard/i)).toBeInTheDocument()
      })

      // Should show retry button
      const retryButton = screen.getByText('Retry')
      expect(retryButton).toBeInTheDocument()

      // Mock successful response for retry
      mockApi.fetchApi.mockResolvedValue(mockAgents)

      // Click retry
      fireEvent.click(retryButton)

      // Should load data successfully
      await waitFor(() => {
        expect(screen.getByText('Strategy Specialist')).toBeInTheDocument()
      })
    })

    it('integrates loading states across components', async () => {
      // Mock slow API response
      mockApi.fetchApi.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(mockAgents), 100))
      )

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      // Should show loading state
      expect(screen.getByText(/Loading.../i)).toBeInTheDocument()

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Strategy Specialist')).toBeInTheDocument()
      })

      // Loading state should be gone
      expect(screen.queryByText(/Loading.../i)).not.toBeInTheDocument()
    })
  })

  describe('Responsive Design Integration', () => {
    it('integrates responsive behavior across all components', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      })

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      // Check that mobile-specific elements are rendered
      const mobileMenuButton = screen.getByLabelText('Open menu')
      expect(mobileMenuButton).toBeInTheDocument()

      // Test mobile menu interaction
      fireEvent.click(mobileMenuButton)

      // Should show mobile menu
      expect(screen.getByText('Menu')).toBeInTheDocument()

      // Test mobile menu close
      const closeButton = screen.getByLabelText('Close menu')
      fireEvent.click(closeButton)

      // Menu should be hidden
      expect(screen.queryByText('Menu')).not.toBeInTheDocument()
    })

    it('integrates touch interactions for mobile devices', () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      // Test touch events
      const dashboardElement = screen.getByText('Dashboard').closest('div')
      if (dashboardElement) {
        // Simulate touch events
        fireEvent.touchStart(dashboardElement)
        fireEvent.touchEnd(dashboardElement)
        
        // Should handle touch interactions appropriately
      }
    })
  })

  describe('Accessibility Integration', () => {
    it('maintains accessibility across all integrated components', () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      // Check for proper ARIA labels
      expect(screen.getByLabelText('Dashboard navigation')).toBeInTheDocument()
      expect(screen.getByLabelText('Search dashboard')).toBeInTheDocument()

      // Check for proper heading structure
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)

      // Check for proper button roles
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)

      // Check for proper navigation
      const navigation = screen.getByRole('navigation')
      expect(navigation).toBeInTheDocument()
    })

    it('integrates keyboard navigation across components', () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      // Test tab navigation
      const firstFocusableElement = screen.getByText('Dashboard')
      firstFocusableElement.focus()

      // Tab through interactive elements
      fireEvent.keyDown(document.activeElement!, { key: 'Tab' })
      
      // Should move focus to next element
      expect(document.activeElement).not.toBe(firstFocusableElement)
    })
  })
})
