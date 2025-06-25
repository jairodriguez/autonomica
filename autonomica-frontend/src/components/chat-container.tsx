'use client';

import React, { useState } from 'react';
import ChatMessages from './chat-messages';
import ChatInput from './chat-input';
import { Message } from '@/types/chat';
import { generateId } from '@/lib/utils';

interface ChatContainerProps {
  initialMessages?: Message[];
  onSendMessage?: (message: string) => Promise<void>;
  isLoading?: boolean;
  className?: string;
}

export default function ChatContainer({ 
  initialMessages = [], 
  onSendMessage,
  isLoading = false,
  className = ""
}: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  
  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    // Call the provided handler if available
    if (onSendMessage) {
      try {
        await onSendMessage(content);
      } catch (error) {
        console.error('Error sending message:', error);
        
        // Add error message
        const errorMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your message. Please try again.',
          timestamp: new Date(),
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }
    } else {
      // Default demo response if no handler provided
      setTimeout(() => {
        const assistantMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: `I received your message: "${content}". This is a demo response. Connect to your backend API to get real AI responses!`,
          timestamp: new Date(),
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      }, 1000);
    }
  };
  
  // Helper function to add messages programmatically (can be exposed via ref)
  // const addMessage = (message: Message) => {
  //   setMessages(prev => [...prev, message]);
  // };
  
  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow-sm border ${className}`}>
      <div className="flex-1 flex flex-col min-h-0">
        <ChatMessages 
          messages={messages} 
          isLoading={isLoading}
        />
        <ChatInput 
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          placeholder="Ask your AI marketing team anything..."
        />
      </div>
    </div>
  );
}

// Export addMessage for external use
export { ChatContainer }; 