import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ClerkProvider } from '@clerk/nextjs'

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })

  return (
    <ClerkProvider publishableKey="test-key">
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </ClerkProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

// Re-export everything
export * from '@testing-library/react'

// Override render method
export { customRender as render }

// Test data factories
export const createMockUser = (overrides = {}) => ({
  id: 'user_123',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  imageUrl: 'https://example.com/avatar.jpg',
  createdAt: new Date('2024-01-01').toISOString(),
  updatedAt: new Date('2024-01-01').toISOString(),
  ...overrides,
})

export const createMockAgent = (overrides = {}) => ({
  id: 'agent_123',
  name: 'Test Agent',
  type: 'strategy',
  description: 'A test agent for testing purposes',
  status: 'idle',
  model: 'gpt-4',
  createdAt: new Date('2024-01-01').toISOString(),
  updatedAt: new Date('2024-01-01').toISOString(),
  ...overrides,
})

export const createMockChatMessage = (overrides = {}) => ({
  id: 'msg_123',
  content: 'Hello, world!',
  role: 'user' as const,
  timestamp: new Date().toISOString(),
  agentId: 'agent_123',
  userId: 'user_123',
  ...overrides,
})

export const createMockProject = (overrides = {}) => ({
  id: 'project_123',
  name: 'Test Project',
  description: 'A test project for testing purposes',
  status: 'active',
  createdAt: new Date('2024-01-01').toISOString(),
  updatedAt: new Date('2024-01-01').toISOString(),
  agents: [createMockAgent()],
  ...overrides,
})

export const createMockWorkflow = (overrides = {}) => ({
  id: 'workflow_123',
  name: 'Test Workflow',
  description: 'A test workflow for testing purposes',
  status: 'running',
  steps: [
    {
      id: 'step_1',
      name: 'Step 1',
      status: 'completed',
      agentId: 'agent_123',
    },
    {
      id: 'step_2',
      name: 'Step 2',
      status: 'running',
      agentId: 'agent_456',
    },
  ],
  createdAt: new Date('2024-01-01').toISOString(),
  updatedAt: new Date('2024-01-01').toISOString(),
  ...overrides,
})

// Mock API responses
export const createMockApiResponse = <T>(data: T, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  statusText: status === 200 ? 'OK' : 'Error',
  json: async (): Promise<T> => data,
  text: async (): Promise<string> => JSON.stringify(data),
  headers: new Headers({
    'Content-Type': 'application/json',
  }),
})

// Mock API error responses
export const createMockApiError = (status = 500, message = 'Internal Server Error') => ({
  ok: false,
  status,
  statusText: message,
  json: async () => ({ error: message, status }),
  text: async () => JSON.stringify({ error: message, status }),
  headers: new Headers({
    'Content-Type': 'application/json',
  }),
})

// Common test helpers
export const waitForElementToBeRemoved = (element: Element | null) => {
  return new Promise<void>((resolve) => {
    if (!element) {
      resolve()
      return
    }
    
    const observer = new MutationObserver(() => {
      if (!document.contains(element)) {
        observer.disconnect()
        resolve()
      }
    })
    
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    })
  })
}

export const mockIntersectionObserver = () => {
  const mockIntersectionObserver = jest.fn()
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  })
  window.IntersectionObserver = mockIntersectionObserver
}

export const mockResizeObserver = () => {
  const mockResizeObserver = jest.fn()
  mockResizeObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  })
  window.ResizeObserver = mockResizeObserver
}

export const mockMatchMedia = (matches = false) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  })
}

// Mock fetch with a simple implementation
export const mockFetch = (response: any, status = 200) => {
  global.fetch = jest.fn().mockImplementation(() =>
    Promise.resolve(createMockApiResponse(response, status))
  )
}

export const mockFetchError = (status = 500, message = 'Internal Server Error') => {
  global.fetch = jest.fn().mockImplementation(() =>
    Promise.resolve(createMockApiError(status, message))
  )
}

// Test environment setup
export const setupTestEnvironment = () => {
  mockIntersectionObserver()
  mockResizeObserver()
  mockMatchMedia()
  
  // Mock console methods to reduce noise in tests
  const originalError = console.error
  const originalWarn = console.warn
  
  beforeAll(() => {
    console.error = (...args: any[]) => {
      if (
        typeof args[0] === 'string' &&
        args[0].includes('Warning: ReactDOM.render is deprecated')
      ) {
        return
      }
      originalError.call(console, ...args)
    }
    
    console.warn = (...args: any[]) => {
      if (
        typeof args[0] === 'string' &&
        args[0].includes('Warning: ReactDOM.render is deprecated')
      ) {
        return
      }
      originalWarn.call(console, ...args)
    }
  })
  
  afterAll(() => {
    console.error = originalError
    console.warn = originalWarn
  })
}

// Export everything
export default customRender