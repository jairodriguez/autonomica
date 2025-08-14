import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import { render as customRender } from '../utils/test-utils'

// Mock the ChatContainer component if it doesn't exist yet
const MockChatContainer = () => {
  const [messages, setMessages] = React.useState<Array<{id: string, content: string, role: string}>>([])
  const [inputValue, setInputValue] = React.useState('')
  const [isLoading, setIsLoading] = React.useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim()) return

    const newMessage = {
      id: Date.now().toString(),
      content: inputValue,
      role: 'user'
    }

    setMessages(prev => [...prev, newMessage])
    setInputValue('')
    setIsLoading(true)

    // Simulate API call
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [...messages, newMessage] })
      })

      if (response.ok) {
        const aiResponse = await response.json()
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          content: aiResponse.content,
          role: 'assistant'
        }])
      }
    } catch (error) {
      console.error('Chat error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div data-testid="chat-container">
      <div data-testid="messages-container">
        {messages.map(message => (
          <div key={message.id} data-testid={`message-${message.role}`}>
            <span data-testid="message-role">{message.role}</span>
            <span data-testid="message-content">{message.content}</span>
          </div>
        ))}
      </div>
      
      {isLoading && <div data-testid="loading-indicator">AI is thinking...</div>}
      
      <form onSubmit={handleSubmit} data-testid="chat-form">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type your message..."
          data-testid="chat-input"
          disabled={isLoading}
        />
        <button 
          type="submit" 
          disabled={isLoading || !inputValue.trim()}
          data-testid="chat-submit"
        >
          Send
        </button>
      </form>
    </div>
  )
}

// Mock Service Worker setup
const server = setupServer(
  rest.post('/api/chat', (req, res, ctx) => {
    return res(
      ctx.json({
        content: 'This is a test AI response',
        role: 'assistant',
        timestamp: new Date().toISOString()
      })
    )
  }),
  
  rest.get('/api/agents', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 'agent_1',
          name: 'Strategy Agent',
          type: 'strategy',
          status: 'idle'
        },
        {
          id: 'agent_2',
          name: 'Content Agent',
          type: 'content',
          status: 'busy'
        }
      ])
    )
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('Chat Integration Tests', () => {
  test('renders chat interface with input and submit button', () => {
    customRender(<MockChatContainer />)
    
    expect(screen.getByTestId('chat-container')).toBeInTheDocument()
    expect(screen.getByTestId('chat-input')).toBeInTheDocument()
    expect(screen.getByTestId('chat-submit')).toBeInTheDocument()
    expect(screen.getByTestId('messages-container')).toBeInTheDocument()
  })

  test('allows user to type and submit messages', async () => {
    const user = userEvent.setup()
    customRender(<MockChatContainer />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    // Type a message
    await user.type(input, 'Hello, AI!')
    expect(input).toHaveValue('Hello, AI!')
    
    // Submit the message
    await user.click(submitButton)
    
    // Wait for the message to appear
    await waitFor(() => {
      expect(screen.getByTestId('message-user')).toBeInTheDocument()
    })
    
    expect(screen.getByTestId('message-content')).toHaveTextContent('Hello, AI!')
  })

  test('displays user messages immediately after submission', async () => {
    const user = userEvent.setup()
    customRender(<MockChatContainer />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    await user.type(input, 'Test message')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByTestId('message-user')).toBeInTheDocument()
    })
    
    const userMessage = screen.getByTestId('message-user')
    expect(userMessage).toHaveTextContent('Test message')
  })

  test('shows loading indicator while AI is processing', async () => {
    const user = userEvent.setup()
    
    // Mock slow API response
    server.use(
      rest.post('/api/chat', async (req, res, ctx) => {
        await new Promise(resolve => setTimeout(resolve, 100))
        return res(ctx.json({ content: 'Delayed response', role: 'assistant' }))
      })
    )
    
    customRender(<MockChatContainer />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    await user.type(input, 'Test message')
    await user.click(submitButton)
    
    // Should show loading indicator
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument()
    
    // Wait for response
    await waitFor(() => {
      expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument()
    })
  })

  test('displays AI response after processing', async () => {
    const user = userEvent.setup()
    customRender(<MockChatContainer />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    await user.type(input, 'Hello, AI!')
    await user.click(submitButton)
    
    // Wait for AI response
    await waitFor(() => {
      expect(screen.getByTestId('message-assistant')).toBeInTheDocument()
    })
    
    const aiMessage = screen.getByTestId('message-assistant')
    expect(aiMessage).toHaveTextContent('This is a test AI response')
  })

  test('maintains conversation history', async () => {
    const user = userEvent.setup()
    customRender(<MockChatContainer />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    // Send first message
    await user.type(input, 'First message')
    await user.click(submitButton)
    
    // Wait for first response
    await waitFor(() => {
      expect(screen.getByTestId('message-assistant')).toBeInTheDocument()
    })
    
    // Send second message
    await user.clear(input)
    await user.type(input, 'Second message')
    await user.click(submitButton)
    
    // Wait for second response
    await waitFor(() => {
      const messages = screen.getAllByTestId('message-user')
      expect(messages).toHaveLength(2)
    })
    
    // Verify conversation history
    const userMessages = screen.getAllByTestId('message-user')
    expect(userMessages[0]).toHaveTextContent('First message')
    expect(userMessages[1]).toHaveTextContent('Second message')
  })

  test('disables input and submit button while processing', async () => {
    const user = userEvent.setup()
    
    // Mock slow API response
    server.use(
      rest.post('/api/chat', async (req, res, ctx) => {
        await new Promise(resolve => setTimeout(resolve, 200))
        return res(ctx.json({ content: 'Slow response', role: 'assistant' }))
      })
    )
    
    customRender(<MockChatContainer />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    await user.type(input, 'Test message')
    await user.click(submitButton)
    
    // Should be disabled while processing
    expect(input).toBeDisabled()
    expect(submitButton).toBeDisabled()
    
    // Wait for completion
    await waitFor(() => {
      expect(input).not.toBeDisabled()
      expect(submitButton).not.toBeDisabled()
    })
  })

  test('handles API errors gracefully', async () => {
    const user = userEvent.setup()
    
    // Mock API error
    server.use(
      rest.post('/api/chat', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Internal server error' }))
      })
    )
    
    customRender(<MockChatContainer />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    await user.type(input, 'Test message')
    await user.click(submitButton)
    
    // Should handle error without crashing
    await waitFor(() => {
      expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument()
    })
    
    // Input should be re-enabled
    expect(input).not.toBeDisabled()
    expect(submitButton).not.toBeDisabled()
  })

  test('prevents empty message submission', async () => {
    const user = userEvent.setup()
    customRender(<MockChatContainer />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    // Try to submit empty message
    await user.click(submitButton)
    
    // Should not submit and no messages should appear
    expect(screen.queryByTestId('message-user')).not.toBeInTheDocument()
    
    // Try to submit whitespace-only message
    await user.type(input, '   ')
    await user.click(submitButton)
    
    // Should not submit whitespace-only messages
    expect(screen.queryByTestId('message-user')).not.toBeInTheDocument()
  })

  test('supports Enter key submission', async () => {
    const user = userEvent.setup()
    customRender(<MockChatContainer />)
    
    const input = screen.getByTestId('chat-input')
    
    await user.type(input, 'Enter key test')
    await user.keyboard('{Enter}')
    
    await waitFor(() => {
      expect(screen.getByTestId('message-user')).toBeInTheDocument()
    })
    
    expect(screen.getByTestId('message-content')).toHaveTextContent('Enter key test')
  })

  test('clears input after message submission', async () => {
    const user = userEvent.setup()
    customRender(<MockChatContainer />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    await user.type(input, 'Test message')
    await user.click(submitButton)
    
    // Wait for message to be processed
    await waitFor(() => {
      expect(screen.getByTestId('message-user')).toBeInTheDocument()
    })
    
    // Input should be cleared
    expect(input).toHaveValue('')
  })
})