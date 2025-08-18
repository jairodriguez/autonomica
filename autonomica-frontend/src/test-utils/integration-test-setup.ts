/**
 * Integration test setup utilities for frontend components
 */
import React from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { DashboardProvider } from '@/contexts/DashboardContext'
import { AgentProvider } from '@/contexts/AgentContext'
import { UserProvider } from '@/contexts/UserContext'
import { ProjectProvider } from '@/contexts/ProjectContext'
import { NotificationProvider } from '@/contexts/NotificationContext'

// Mock data for integration tests
export const mockTestData = {
  agents: [
    {
      id: 'agent_1',
      name: 'Strategy Specialist',
      type: 'STRATEGY',
      model: 'gpt-4',
      status: 'idle',
      is_active: true,
      description: 'Specializes in marketing strategy',
      user_id: 'test_user_123',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 'agent_2',
      name: 'Content Creator',
      type: 'CONTENT',
      model: 'gpt-4',
      status: 'busy',
      is_active: true,
      description: 'Creates marketing content',
      user_id: 'test_user_123',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 'agent_3',
      name: 'Analytics Expert',
      type: 'ANALYTICS',
      model: 'gpt-4',
      status: 'offline',
      is_active: false,
      description: 'Analyzes marketing data',
      user_id: 'test_user_123',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
  ],
  projects: [
    {
      id: 'project_1',
      name: 'Marketing Campaign 2025',
      description: 'Comprehensive marketing campaign for Q1 2025',
      status: 'active',
      progress: 75,
      agents: ['agent_1', 'agent_2'],
      user_id: 'test_user_123',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-15T00:00:00Z',
    },
    {
      id: 'project_2',
      name: 'SEO Optimization',
      description: 'Website SEO optimization project',
      status: 'planning',
      progress: 25,
      agents: ['agent_3'],
      user_id: 'test_user_123',
      created_at: '2025-01-10T00:00:00Z',
      updated_at: '2025-01-12T00:00:00Z',
    },
  ],
  analytics: {
    total_agents: 3,
    active_agents: 2,
    total_projects: 2,
    completed_tasks: 15,
    pending_tasks: 8,
    total_revenue: 25000,
    monthly_growth: 12.5,
  },
  user: {
    id: 'test_user_123',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    imageUrl: 'https://example.com/avatar.jpg',
    role: 'admin',
    isVerified: true,
  },
  notifications: [
    {
      id: 'notif_1',
      title: 'Agent Status Update',
      message: 'Strategy Specialist is now available',
      type: 'info',
      timestamp: '2025-01-15T10:00:00Z',
      read: false,
    },
    {
      id: 'notif_2',
      title: 'Project Completed',
      message: 'Marketing Campaign 2025 has been completed',
      type: 'success',
      timestamp: '2025-01-14T15:30:00Z',
      read: true,
    },
  ],
}

// Custom render function with all providers
export function renderWithProviders(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <UserProvider>
        <AgentProvider>
          <ProjectProvider>
            <NotificationProvider>
              <DashboardProvider>
                {children}
              </DashboardProvider>
            </NotificationProvider>
          </ProjectProvider>
        </AgentProvider>
      </UserProvider>
    )
  }

  return render(ui, { wrapper: Wrapper, ...options })
}

// Mock API responses for integration tests
export const mockApiResponses = {
  agents: () => Promise.resolve(mockTestData.agents),
  projects: () => Promise.resolve(mockTestData.projects),
  analytics: () => Promise.resolve(mockTestData.analytics),
  user: () => Promise.resolve(mockTestData.user),
  notifications: () => Promise.resolve(mockTestData.notifications),
  error: (message: string = 'API Error') => Promise.reject(new Error(message)),
  delayed: (data: any, delay: number = 100) => 
    new Promise(resolve => setTimeout(() => resolve(data), delay)),
}

// Test utilities for common operations
export const testUtils = {
  // Wait for element with timeout
  waitForElement: async (selector: string, timeout: number = 5000) => {
    const startTime = Date.now()
    
    while (Date.now() - startTime < timeout) {
      const element = document.querySelector(selector)
      if (element) return element
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    
    throw new Error(`Element ${selector} not found within ${timeout}ms`)
  },

  // Mock user interactions
  mockUserInteraction: {
    click: (element: Element) => {
      fireEvent.click(element)
    },
    type: (input: HTMLInputElement, text: string) => {
      fireEvent.change(input, { target: { value: text } })
    },
    submit: (form: HTMLFormElement) => {
      fireEvent.submit(form)
    },
    keyPress: (element: Element, key: string) => {
      fireEvent.keyPress(element, { key })
    },
  },

  // Mock browser APIs
  mockBrowserAPIs: {
    localStorage: {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    },
    sessionStorage: {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    },
    fetch: jest.fn(),
    matchMedia: jest.fn(() => ({
      matches: false,
      addListener: jest.fn(),
      removeListener: jest.fn(),
    })),
  },

  // Mock external services
  mockExternalServices: {
    clerk: {
      useAuth: () => ({
        isSignedIn: true,
        userId: 'test_user_123',
        signOut: jest.fn(),
      }),
      useUser: () => ({
        isSignedIn: true,
        userId: 'test_user_123',
        user: mockTestData.user,
      }),
    },
    api: {
      fetchApi: jest.fn(),
      postApi: jest.fn(),
      putApi: jest.fn(),
      deleteApi: jest.fn(),
    },
  },
}

// Setup function for integration tests
export function setupIntegrationTest() {
  // Mock all external dependencies
  jest.mock('@/lib/api', () => ({
    fetchApi: jest.fn(),
    postApi: jest.fn(),
    putApi: jest.fn(),
    deleteApi: jest.fn(),
  }))

  jest.mock('@clerk/nextjs', () => ({
    useAuth: () => testUtils.mockExternalServices.clerk.useAuth(),
    useUser: () => testUtils.mockExternalServices.clerk.useUser(),
  }))

  // Setup global mocks
  global.fetch = jest.fn()
  global.localStorage = testUtils.mockBrowserAPIs.localStorage
  global.sessionStorage = testUtils.mockBrowserAPIs.sessionStorage

  // Mock IntersectionObserver
  global.IntersectionObserver = class IntersectionObserver {
    constructor() {}
    disconnect() {}
    observe() {}
    unobserve() {}
  }

  // Mock ResizeObserver
  global.ResizeObserver = class ResizeObserver {
    constructor() {}
    disconnect() {}
    observe() {}
    unobserve() {}
  }

  // Mock window.matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: testUtils.mockBrowserAPIs.matchMedia,
  })

  // Mock window.scrollTo
  Object.defineProperty(window, 'scrollTo', {
    writable: true,
    value: jest.fn(),
  })
}

// Cleanup function for integration tests
export function cleanupIntegrationTest() {
  // Clear all mocks
  jest.clearAllMocks()
  jest.resetAllMocks()
  
  // Clear DOM
  document.body.innerHTML = ''
  
  // Reset window location
  delete window.location
  window.location = {
    href: 'http://localhost:3000',
    origin: 'http://localhost:3000',
    protocol: 'http:',
    host: 'localhost:3000',
    hostname: 'localhost',
    port: '3000',
    pathname: '/',
    search: '',
    hash: '',
    reload: jest.fn(),
    replace: jest.fn(),
    assign: jest.fn(),
  }
}

// Export fireEvent for convenience
export { fireEvent, waitFor, screen } from '@testing-library/react'
