'use client';

import React, { useState, useRef, useEffect } from 'react';
import ChatMessages from './chat-messages';
import ChatInput from './chat-input';
import { useChat } from '@/lib/use-chat';
import { Message } from '@/types/chat';
import type { Agent } from './project-sidebar';
import { API_URLS } from '@/lib/config';

interface ChatContainerAIProps {
  initialMessages?: Message[];
  onFinish?: (message: Message) => void;
  onError?: (error: Error) => void;
  className?: string;
  api?: string;
  agentContext?: Agent;
}

export default function ChatContainerAI({ 
  initialMessages = [],
  onFinish,
  onError,
  className = "",
  api = API_URLS.CHAT,
  agentContext
}: ChatContainerAIProps) {
  const { messages, isLoading, error, append } = useChat({
    api,
    initialMessages: initialMessages.length > 0 ? initialMessages : [
      {
        id: '1',
        role: 'system',
        content: `You are a helpful AI marketing assistant${agentContext ? ` named ${agentContext.name} (${agentContext.type} - ${agentContext.model})` : ''}. You help users with marketing strategy, content creation, SEO analysis, and campaign planning.`,
        timestamp: new Date()
      }
    ],
    onFinish,
    onError
  });

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;
    
    // Send the message using the useChat hook
    await append({
      role: 'user',
      content: content.trim()
    });
  };

  // Determine display info based on agent context
  const displayName = agentContext ? agentContext.name : 'Marketing AI Assistant';
  const displayStatus = agentContext ? 
    (isLoading ? 'Thinking...' : 
     agentContext.status === 'busy' ? 'Working...' :
     agentContext.status === 'idle' ? 'Ready to help' :
     agentContext.status === 'error' ? 'Error state' : 'Offline') :
    (isLoading ? 'Thinking...' : 'Ready to help');
  
  const avatarColor = agentContext?.status === 'busy' ? 'bg-blue-600' :
                     agentContext?.status === 'idle' ? 'bg-green-600' :
                     agentContext?.status === 'error' ? 'bg-red-600' :
                     agentContext?.status === 'offline' ? 'bg-gray-600' : 'bg-blue-600';

  const placeholder = agentContext ? 
    `Chat with ${agentContext.name}...` : 
    'Ask your AI marketing team anything...';

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow-sm border ${className}`}>
      <div className="flex-1 flex flex-col min-h-0">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className={`w-8 h-8 ${avatarColor} rounded-full flex items-center justify-center relative`}>
              <span className="text-white text-sm font-medium">
                {agentContext ? agentContext.name[0].toUpperCase() : 'AI'}
              </span>
              {agentContext?.status === 'busy' && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-400 rounded-full animate-pulse" />
              )}
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-900">{displayName}</h3>
              <p className="text-xs text-gray-500">{displayStatus}</p>
              {agentContext && (
                <p className="text-xs text-gray-400">{agentContext.type} • {agentContext.model}</p>
              )}
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
          placeholder={placeholder}
          disabled={!!error || agentContext?.status === 'offline'}
        />
      </div>
    </div>
  );
} 