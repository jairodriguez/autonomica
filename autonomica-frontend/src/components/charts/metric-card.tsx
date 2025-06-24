'use client';

import React from 'react';
import { 
  ArrowUpIcon, 
  ArrowDownIcon, 
  MinusIcon 
} from '@heroicons/react/24/outline';

export interface MetricCardProps {
  title: string;
  value: string | number;
  change?: string | number;
  trend?: 'up' | 'down' | 'neutral';
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  color?: string;
  isDarkTheme?: boolean;
  className?: string;
  subtitle?: string;
  isLoading?: boolean;
}

export default function MetricCard({
  title,
  value,
  change,
  trend = 'neutral',
  icon: Icon,
  color = '#8b5cf6', // purple-500
  isDarkTheme = true,
  className = '',
  subtitle,
  isLoading = false
}: MetricCardProps) {
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-500';
      case 'down':
        return 'text-red-500';
      default:
        return isDarkTheme ? 'text-gray-400' : 'text-gray-500';
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return ArrowUpIcon;
      case 'down':
        return ArrowDownIcon;
      default:
        return MinusIcon;
    }
  };

  const TrendIcon = getTrendIcon();

  if (isLoading) {
    return (
      <div className={`rounded-lg border p-6 ${
        isDarkTheme 
          ? 'bg-gray-800 border-gray-700' 
          : 'bg-white border-gray-200'
      } ${className}`}>
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-4">
            <div className="h-4 bg-gray-600 rounded w-24"></div>
            <div className="h-8 w-8 bg-gray-600 rounded"></div>
          </div>
          <div className="h-8 bg-gray-600 rounded w-20 mb-2"></div>
          <div className="h-4 bg-gray-600 rounded w-16"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border p-6 transition-all duration-200 hover:shadow-lg ${
      isDarkTheme 
        ? 'bg-gray-800 border-gray-700 hover:bg-gray-750' 
        : 'bg-white border-gray-200 hover:bg-gray-50'
    } ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-sm font-medium ${
          isDarkTheme ? 'text-gray-400' : 'text-gray-600'
        }`}>
          {title}
        </h3>
        {Icon && (
          <div 
            className="p-2 rounded-lg"
            style={{ backgroundColor: `${color}20` }}
          >
            <Icon 
              className="w-5 h-5" 
              style={{ color }}
            />
          </div>
        )}
      </div>

      {/* Value */}
      <div className="mb-2">
        <div className={`text-3xl font-bold ${
          isDarkTheme ? 'text-white' : 'text-gray-900'
        }`}>
          {value}
        </div>
        {subtitle && (
          <div className={`text-sm ${
            isDarkTheme ? 'text-gray-500' : 'text-gray-600'
          }`}>
            {subtitle}
          </div>
        )}
      </div>

      {/* Change/Trend */}
      {change !== undefined && (
        <div className="flex items-center">
          <TrendIcon className={`w-4 h-4 mr-1 ${getTrendColor()}`} />
          <span className={`text-sm font-medium ${getTrendColor()}`}>
            {typeof change === 'number' && change > 0 && trend !== 'down' ? '+' : ''}
            {change}
            {typeof change === 'number' ? '%' : ''}
          </span>
          <span className={`text-sm ml-1 ${
            isDarkTheme ? 'text-gray-500' : 'text-gray-600'
          }`}>
            vs last period
          </span>
        </div>
      )}
    </div>
  );
} 