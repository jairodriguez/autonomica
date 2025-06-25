'use client';

import React from 'react';
import { 
  BarChart as RechartsBarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

export interface BarDataPoint {
  name: string;
  value: number;
  [key: string]: string | number; // Allow additional data fields
}

export interface BarChartProps {
  data: BarDataPoint[];
  height?: number;
  color?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  dataKey?: string;
  xAxisKey?: string;
  isDarkTheme?: boolean;
  className?: string;
  layout?: 'horizontal' | 'vertical';
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

export default function BarChart({
  data,
  height = 300,
  color = '#8b5cf6', // Purple-500 to match theme
  showGrid = true,
  showLegend = false,
  showTooltip = true,
  dataKey = 'value',
  xAxisKey = 'name',
  isDarkTheme = true, // Default to dark theme
  className = '',
  layout = 'vertical'
}: BarChartProps) {
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
        <RechartsBarChart 
          data={data}
          layout={layout}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          {showGrid && (
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke={gridColor}
              opacity={0.3}
            />
          )}
          <XAxis 
            type={layout === 'vertical' ? 'category' : 'number'}
            dataKey={layout === 'vertical' ? xAxisKey : undefined}
            axisLine={false}
            tickLine={false}
            tick={{ fill: textColor, fontSize: 12 }}
          />
          <YAxis 
            type={layout === 'vertical' ? 'number' : 'category'}
            dataKey={layout === 'horizontal' ? xAxisKey : undefined}
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
          <Bar 
            dataKey={dataKey} 
            fill={color}
            radius={[2, 2, 0, 0]}
          />
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
} 