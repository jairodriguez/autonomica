import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import ChatContainerAI from '../ChatContainerAI'

// Mock the useChat hook
jest.mock('ai', () => ({
  useChat: () => ({
    messages: [],
    input: '',
    handleInputChange: jest.fn(),
    handleSubmit: jest.fn(),
    isLoading: false,
    error: null,
  }),
}))

// Mock the Clerk authentication
jest.mock('@clerk/nextjs', () => ({
  useAuth: () => ({
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

describe('ChatContainerAI', () => {
  const defaultProps = {
    agentContext: undefined,
  }

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<ChatContainerAI {...defaultProps} />)
    expect(screen.getByText(/Marketing AI Assistant/i)).toBeInTheDocument()
  })

  it('displays the correct title when no agent context is provided', () => {
    render(<ChatContainerAI {...defaultProps} />)
    expect(screen.getByText('Marketing AI Assistant')).toBeInTheDocument()
  })

  it('displays agent information when agent context is provided', () => {
    const agentContext = {
      id: 'test_agent_123',
      name: 'Strategy Specialist',
      type: 'STRATEGY',
      model: 'gpt-4',
      status: 'idle',
    }

    render(<ChatContainerAI agentContext={agentContext} />)
    expect(screen.getByText('Strategy Specialist')).toBeInTheDocument()
    expect(screen.getByText('STRATEGY')).toBeInTheDocument()
    expect(screen.getByText('gpt-4')).toBeInTheDocument()
  })

  it('shows chat input field', () => {
    render(<ChatContainerAI {...defaultProps} />)
    const input = screen.getByPlaceholderText(/Ask me anything about marketing/i)
    expect(input).toBeInTheDocument()
  })

  it('shows send button', () => {
    render(<ChatContainerAI {...defaultProps} />)
    const sendButton = screen.getByRole('button', { name: /send/i })
    expect(sendButton).toBeInTheDocument()
  })

  it('handles input changes', async () => {
    render(<ChatContainerAI {...defaultProps} />)
    const input = screen.getByPlaceholderText(/Ask me anything about marketing/i)
    
    fireEvent.change(input, { target: { value: 'Hello, how are you?' } })
    
    await waitFor(() => {
      expect(input).toHaveValue('Hello, how are you?')
    })
  })

  it('shows loading state when submitting', () => {
    // Mock the useChat hook to return loading state
    jest.doMock('ai', () => ({
      useChat: () => ({
        messages: [],
        input: '',
        handleInputChange: jest.fn(),
        handleSubmit: jest.fn(),
        isLoading: true,
        error: null,
      }),
    }))

    render(<ChatContainerAI {...defaultProps} />)
    expect(screen.getByText(/thinking/i)).toBeInTheDocument()
  })

  it('shows error state when there is an error', () => {
    // Mock the useChat hook to return error state
    jest.doMock('ai', () => ({
      useChat: () => ({
        messages: [],
        input: '',
        handleInputChange: jest.fn(),
        handleSubmit: jest.fn(),
        isLoading: false,
        error: 'Something went wrong',
      }),
    }))

    render(<ChatContainerAI {...defaultProps} />)
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
  })

  it('displays agent status correctly', () => {
    const agentContext = {
      id: 'test_agent_123',
      name: 'Strategy Specialist',
      type: 'STRATEGY',
      model: 'gpt-4',
      status: 'busy',
    }

    render(<ChatContainerAI agentContext={agentContext} />)
    expect(screen.getByText(/thinking/i)).toBeInTheDocument()
  })

  it('shows offline state when agent is offline', () => {
    const agentContext = {
      id: 'test_agent_123',
      name: 'Strategy Specialist',
      type: 'STRATEGY',
      model: 'gpt-4',
      status: 'offline',
    }

    render(<ChatContainerAI agentContext={agentContext} />)
    expect(screen.getByText(/offline/i)).toBeInTheDocument()
    
    // Chat input should be disabled
    const input = screen.getByPlaceholderText(/Ask me anything about marketing/i)
    expect(input).toBeDisabled()
  })

  it('generates correct avatar for agent', () => {
    const agentContext = {
      id: 'test_agent_123',
      name: 'Strategy Specialist',
      type: 'STRATEGY',
      model: 'gpt-4',
      status: 'idle',
    }

    render(<ChatContainerAI agentContext={agentContext} />)
    
    // Should show the first letter of the agent name
    expect(screen.getByText('S')).toBeInTheDocument()
  })

  it('handles form submission', async () => {
    const mockHandleSubmit = jest.fn()
    
    // Mock the useChat hook
    jest.doMock('ai', () => ({
      useChat: () => ({
        messages: [],
        input: '',
        handleInputChange: jest.fn(),
        handleSubmit: mockHandleSubmit,
        isLoading: false,
        error: null,
      }),
    }))

    render(<ChatContainerAI {...defaultProps} />)
    
    const input = screen.getByPlaceholderText(/Ask me anything about marketing/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(mockHandleSubmit).toHaveBeenCalled()
    })
  })

  it('maintains accessibility features', () => {
    render(<ChatContainerAI {...defaultProps} />)
    
    // Check for proper ARIA labels
    const input = screen.getByPlaceholderText(/Ask me anything about marketing/i)
    expect(input).toHaveAttribute('aria-label', 'Chat input')
    
    const sendButton = screen.getByRole('button', { name: /send/i })
    expect(sendButton).toHaveAttribute('aria-label', 'Send message')
  })

  it('handles keyboard navigation', async () => {
    render(<ChatContainerAI {...defaultProps} />)
    
    const input = screen.getByPlaceholderText(/Ask me anything about marketing/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    // Focus on input
    input.focus()
    expect(input).toHaveFocus()
    
    // Tab to send button
    fireEvent.keyDown(input, { key: 'Tab' })
    expect(sendButton).toHaveFocus()
  })

  it('displays placeholder text correctly', () => {
    render(<ChatContainerAI {...defaultProps} />)
    
    const input = screen.getByPlaceholderText(/Ask me anything about marketing/i)
    expect(input).toBeInTheDocument()
    
    // Check that placeholder is descriptive
    expect(input.placeholder).toContain('Ask me anything about marketing')
  })

  it('handles empty input gracefully', () => {
    render(<ChatContainerAI {...defaultProps} />)
    
    const input = screen.getByPlaceholderText(/Ask me anything about marketing/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    // Try to send empty message
    fireEvent.click(sendButton)
    
    // Button should still be enabled
    expect(sendButton).not.toBeDisabled()
  })

  it('shows proper loading indicators', () => {
    // Mock loading state
    jest.doMock('ai', () => ({
      useChat: () => ({
        messages: [],
        input: '',
        handleInputChange: jest.fn(),
        handleSubmit: jest.fn(),
        isLoading: true,
        error: null,
      }),
    }))

    render(<ChatContainerAI {...defaultProps} />)
    
    // Should show loading indicator
    expect(screen.getByText(/thinking/i)).toBeInTheDocument()
    
    // Input should be disabled during loading
    const input = screen.getByPlaceholderText(/Ask me anything about marketing/i)
    expect(input).toBeDisabled()
  })
})
