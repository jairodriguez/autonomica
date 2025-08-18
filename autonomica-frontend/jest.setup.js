import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: {},
      asPath: '/',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn().mockResolvedValue(undefined),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
      isFallback: false,
    }
  },
}))

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  usePathname() {
    return '/'
  },
}))

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = 'test_key'

// Mock fetch globally
global.fetch = jest.fn()

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

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock window.scrollTo
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: jest.fn(),
})

// Mock console methods in tests
const originalError = console.error
const originalWarn = console.warn

beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return
    }
    originalError.call(console, ...args)
  }
  
  console.warn = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: componentWillReceiveProps has been renamed')
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

// Global test utilities
global.testUtils = {
  // Wait for element to be present
  waitForElement: (selector, timeout = 5000) => {
    return new Promise((resolve, reject) => {
      const startTime = Date.now()
      
      const checkElement = () => {
        const element = document.querySelector(selector)
        if (element) {
          resolve(element)
          return
        }
        
        if (Date.now() - startTime > timeout) {
          reject(new Error(`Element ${selector} not found within ${timeout}ms`))
          return
        }
        
        setTimeout(checkElement, 100)
      }
      
      checkElement()
    })
  },
  
  // Mock API responses
  mockApiResponse: (url, response, status = 200) => {
    global.fetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: status < 400,
        status,
        json: () => Promise.resolve(response),
        text: () => Promise.resolve(JSON.stringify(response)),
      })
    )
  },
  
  // Create test user
  createTestUser: (overrides = {}) => ({
    id: 'test_user_123',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    imageUrl: 'https://example.com/avatar.jpg',
    ...overrides,
  }),
}

// Setup test environment
beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks()
  
  // Reset fetch mock
  global.fetch.mockClear()
  
  // Clear localStorage and sessionStorage
  localStorage.clear()
  sessionStorage.clear()
  
  // Reset document body
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
})

// Cleanup after each test
afterEach(() => {
  // Clean up any timers
  jest.clearAllTimers()
  
  // Clean up any intervals
  jest.clearAllTimers()
  
  // Reset all mocks
  jest.resetAllMocks()
})
