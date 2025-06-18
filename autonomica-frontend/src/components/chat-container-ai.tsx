'use client';

import React from 'react';
import ChatMessages from './chat-messages';
import ChatInput from './chat-input';
import { useChat } from '@/lib/use-chat';
import { Message } from '@/types/chat';

interface ChatContainerAIProps {
  initialMessages?: Message[];
  onFinish?: (message: Message) => void;
  onError?: (error: Error) => void;
  className?: string;
  api?: string;
}

export default function ChatContainerAI({ 
  initialMessages = [], 
  onFinish,
  onError,
  className = "",
  api = '/api/chat'
}: ChatContainerAIProps) {
  const { 
    messages, 
    sendMessage, 
    isLoading, 
    error 
  } = useChat({
    api,
    initialMessages,
    onFinish,
    onError,
  });

  const handleSendMessage = async (content: string) => {
    try {
      await sendMessage(content);
    } catch (err) {
      console.error('Error sending message:', err);
    }
  };

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow-sm border ${className}`}>
      <div className="flex-1 flex flex-col min-h-0">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">AI</span>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-900">Marketing AI Assistant</h3>
              <p className="text-xs text-gray-500">
                {isLoading ? 'Thinking...' : 'Ready to help'}
              </p>
            </div>
          </div>
          
          {error && (
            <div className="flex items-center space-x-2 text-red-600 text-sm">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span>Connection error</span>
            </div>
          )}
        </div>

        {/* Messages */}
        <ChatMessages 
          messages={messages} 
          isLoading={isLoading}
        />
        
        {/* Input */}
        <ChatInput 
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          placeholder="Ask your AI marketing team anything..."
          disabled={!!error}
        />
      </div>
    </div>
  );
} 