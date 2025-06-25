'use client';

import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Message } from '@/types/chat';
import { formatTimestamp, cn } from '@/lib/utils';

interface ChatMessagesProps {
  messages: Message[];
  isLoading?: boolean;
}

export default function ChatMessages({ messages, isLoading = false }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500">
            <div className="text-6xl mb-4">🤖</div>
            <h3 className="text-lg font-medium mb-2">Welcome to Autonomica</h3>
            <p>Start a conversation with your AI marketing team!</p>
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex",
                message.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={cn(
                  "max-w-3xl rounded-lg p-3",
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                )}
              >
                <div className="flex items-start space-x-2">
                  <div className="flex-1">
                    {message.role === 'user' ? (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    ) : (
                                                                    <div className="prose prose-sm max-w-none">
                         <ReactMarkdown
                           components={{
                             p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                             ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                             ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
                             li: ({ children }) => <li className="mb-1">{children}</li>,
                             code: ({ children }) => (
                               <code className="bg-gray-200 text-gray-800 px-1 py-0.5 rounded text-sm">
                                 {children}
                               </code>
                             ),
                             pre: ({ children }) => (
                               <pre className="bg-gray-200 text-gray-800 p-2 rounded text-sm overflow-x-auto">
                                 {children}
                               </pre>
                             ),
                           }}
                         >
                           {message.content}
                         </ReactMarkdown>
                       </div>
                    )}
                  </div>
                </div>
                <div className="mt-1 text-xs opacity-70">
                  {formatTimestamp(message.timestamp)}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                  <span className="text-sm text-gray-500">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
} 