'use client';

import React from 'react';
import { 
  AreaChart as RechartsAreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

export interface AreaDataPoint {
  name: string;
  value: number;
  [key: string]: string | number; // Allow additional data fields
}

export interface AreaChartProps {
  data: AreaDataPoint[];
  height?: number;
  color?: string;
  gradientId?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  dataKey?: string;
  xAxisKey?: string;
  isDarkTheme?: boolean;
  className?: string;
  stackId?: string;
  type?: 'monotone' | 'linear' | 'step';
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  label?: string;
}

export default function AreaChart({
  data,
  height = 300,
  color = '#8b5cf6', // Purple-500 to match theme
  gradientId = 'colorPurple',
  showGrid = true,
  showLegend = false,
  showTooltip = true,
  dataKey = 'value',
  xAxisKey = 'name',
  isDarkTheme = true, // Default to dark theme
  className = '',
  stackId,
  type = 'monotone'
}: AreaChartProps) {
  const gridColor = isDarkTheme ? '#374151' : '#e5e7eb'; // gray-700 : gray-200
  const textColor = isDarkTheme ? '#9ca3af' : '#6b7280'; // gray-400 : gray-500

  const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className={`rounded-lg border p-3 shadow-lg ${
          isDarkTheme 
            ? 'bg-gray-800 border-gray-600 text-white' 
            : 'bg-white border-gray-200 text-gray-900'
        }`}>
          <p className="text-sm font-medium">{`${label}`}</p>
          {payload.map((entry, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.name}: ${entry.value}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`w-full ${className}`}>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsAreaChart 
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.8}/>
              <stop offset="95%" stopColor={color} stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          {showGrid && (
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke={gridColor}
              opacity={0.3}
            />
          )}
          <XAxis 
            dataKey={xAxisKey}
            axisLine={false}
            tickLine={false}
            tick={{ fill: textColor, fontSize: 12 }}
          />
          <YAxis 
            axisLine={false}
            tickLine={false}
            tick={{ fill: textColor, fontSize: 12 }}
          />
          {showTooltip && <Tooltip content={<CustomTooltip />} />}
          {showLegend && (
            <Legend 
              wrapperStyle={{ color: textColor }}
            />
          )}
          <Area 
            type={type}
            dataKey={dataKey} 
            stackId={stackId}
            stroke={color}
            strokeWidth={2}
            fill={`url(#${gradientId})`}
            dot={{ fill: color, strokeWidth: 2, r: 3 }}
            activeDot={{ r: 5, stroke: color, strokeWidth: 2 }}
          />
        </RechartsAreaChart>
      </ResponsiveContainer>
    </div>
  );
} 