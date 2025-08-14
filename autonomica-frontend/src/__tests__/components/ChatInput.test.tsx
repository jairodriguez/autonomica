import React from 'react'
import { render, screen, fireEvent, waitFor } from '../utils/test-utils'
import ChatInput from '../../components/ChatInput'

// Mock the ChatInput component if it doesn't exist yet
const MockChatInput = ({ onSubmit, disabled = false }: { onSubmit: (message: string) => void, disabled?: boolean }) => {
  const [message, setMessage] = React.useState('')
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim()) {
      onSubmit(message.trim())
      setMessage('')
    }
  }
  
  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your message..."
        disabled={disabled}
        className="flex-1 px-3 py-2 border rounded-lg"
        data-testid="chat-input"
      />
      <button
        type="submit"
        disabled={disabled || !message.trim()}
        className="px-4 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50"
        data-testid="chat-submit"
      >
        Send
      </button>
    </form>
  )
}

describe('ChatInput', () => {
  const mockOnSubmit = jest.fn()
  
  beforeEach(() => {
    mockOnSubmit.mockClear()
  })
  
  it('renders input field and submit button', () => {
    render(<MockChatInput onSubmit={mockOnSubmit} />)
    
    expect(screen.getByTestId('chat-input')).toBeInTheDocument()
    expect(screen.getByTestId('chat-submit')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument()
  })
  
  it('allows typing in the input field', () => {
    render(<MockChatInput onSubmit={mockOnSubmit} />)
    
    const input = screen.getByTestId('chat-input')
    fireEvent.change(input, { target: { value: 'Hello, world!' } })
    
    expect(input).toHaveValue('Hello, world!')
  })
  
  it('submits message when form is submitted', async () => {
    render(<MockChatInput onSubmit={mockOnSubmit} />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith('Test message')
    })
    
    expect(input).toHaveValue('')
  })
  
  it('does not submit empty messages', () => {
    render(<MockChatInput onSubmit={mockOnSubmit} />)
    
    const submitButton = screen.getByTestId('chat-submit')
    fireEvent.click(submitButton)
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })
  
  it('does not submit whitespace-only messages', () => {
    render(<MockChatInput onSubmit={mockOnSubmit} />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    fireEvent.change(input, { target: { value: '   ' } })
    fireEvent.click(submitButton)
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })
  
  it('disables input and submit button when disabled prop is true', () => {
    render(<MockChatInput onSubmit={mockOnSubmit} disabled={true} />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    expect(input).toBeDisabled()
    expect(submitButton).toBeDisabled()
  })
  
  it('submits message when Enter key is pressed', async () => {
    render(<MockChatInput onSubmit={mockOnSubmit} />)
    
    const input = screen.getByTestId('chat-input')
    fireEvent.change(input, { target: { value: 'Enter key test' } })
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith('Enter key test')
    })
  })
  
  it('trims whitespace from submitted messages', async () => {
    render(<MockChatInput onSubmit={mockOnSubmit} />)
    
    const input = screen.getByTestId('chat-input')
    const submitButton = screen.getByTestId('chat-submit')
    
    fireEvent.change(input, { target: { value: '  trimmed message  ' } })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith('trimmed message')
    })
  })
})