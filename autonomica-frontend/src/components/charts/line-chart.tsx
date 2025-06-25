'use client';

import React from 'react';
import { 
  LineChart as RechartsLineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Brush
} from 'recharts';

export interface DataPoint {
  name: string;
  value: number;
  [key: string]: string | number; // Allow additional data fields
}

export interface LineChartProps {
  data: DataPoint[];
  height?: number;
  color?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  showBrush?: boolean;
  dataKey?: string;
  xAxisKey?: string;
  isDarkTheme?: boolean;
  className?: string;
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

const LineChartComponent = ({
  data,
  height = 300,
  color = '#8b5cf6', // Purple-500 to match theme
  showGrid = true,
  showLegend = false,
  showTooltip = true,
  showBrush = false,
  dataKey = 'value',
  xAxisKey = 'name',
  isDarkTheme = true, // Default to dark theme
  className = ''
}: LineChartProps) => {
  const gridColor = isDarkTheme ? '#374151' : '#e5e7eb'; // gray-700 : gray-200
  const textColor = isDarkTheme ? '#9ca3af' : '#6b7280'; // gray-400 : gray-500
  const brushFillColor = isDarkTheme ? 'rgba(139, 92, 246, 0.1)' : 'rgba(139, 92, 246, 0.2)';

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
        <RechartsLineChart 
          data={data}
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
          <Line 
            type="monotone" 
            dataKey={dataKey} 
            stroke={color}
            strokeWidth={2}
            dot={{ fill: color, strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: color, strokeWidth: 2 }}
          />
          {showBrush && (
            <Brush
              dataKey={xAxisKey}
              height={30}
              stroke={color}
              fill={brushFillColor}
              tickFormatter={(tick) => (typeof tick === 'string' ? tick.substring(0, 3) : tick)}
            />
          )}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
};

const LineChart = React.memo(LineChartComponent);
export default LineChart; 