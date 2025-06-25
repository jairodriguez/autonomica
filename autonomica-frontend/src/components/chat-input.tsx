'use client';

import React, { useState, KeyboardEvent } from 'react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  disabled?: boolean;
}

export default function ChatInput({ 
  onSendMessage, 
  isLoading = false, 
  placeholder = "Type your message...",
  disabled = false 
}: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isLoading && !disabled) {
      onSendMessage(trimmedMessage);
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex space-x-3">
        <div className="flex-1">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            rows={3}
            className={cn(
              "w-full resize-none rounded-lg border border-gray-300 p-3",
              "focus:border-blue-500 focus:ring-1 focus:ring-blue-500",
              "disabled:bg-gray-50 disabled:cursor-not-allowed",
              "placeholder-gray-500"
            )}
          />
        </div>
        <button
          onClick={handleSubmit}
          disabled={!message.trim() || isLoading || disabled}
          className={cn(
            "px-4 py-2 rounded-lg font-medium",
            "bg-blue-600 text-white",
            "hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500",
            "disabled:bg-gray-300 disabled:cursor-not-allowed",
            "transition-colors duration-200"
          )}
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            'Send'
          )}
        </button>
      </div>
    </div>
  );
} 