'use client';

import React from 'react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

export interface DonutDataPoint {
  name: string;
  value: number;
  color?: string;
  total?: number; // Added for tooltip calculation
  [key: string]: string | number | undefined; // Allow additional data fields
}

export interface DonutChartProps {
  data: DonutDataPoint[];
  height?: number;
  colors?: string[];
  showLegend?: boolean;
  showTooltip?: boolean;
  showValue?: boolean;
  innerRadius?: number;
  outerRadius?: number;
  isDarkTheme?: boolean;
  className?: string;
  centerText?: string;
  centerValue?: string | number;
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    payload: DonutDataPoint;
  }>;
}

interface LabelProps {
  cx?: number;
  cy?: number;
  midAngle?: number;
  innerRadius?: number;
  outerRadius?: number;
  percent?: number;
}

const DEFAULT_COLORS = [
  '#8b5cf6', // purple-500
  '#06b6d4', // cyan-500
  '#10b981', // emerald-500
  '#f59e0b', // amber-500
  '#ef4444', // red-500
  '#ec4899', // pink-500
  '#6366f1', // indigo-500
  '#84cc16'  // lime-500
];

const DonutChartComponent = ({
  data,
  height = 300,
  colors = DEFAULT_COLORS,
  showLegend = true,
  showTooltip = true,
  showValue = false,
  innerRadius = 60,
  outerRadius = 100,
  isDarkTheme = true, // Default to dark theme
  className = '',
  centerText,
  centerValue
}: DonutChartProps) => {
  const textColor = isDarkTheme ? '#9ca3af' : '#6b7280'; // gray-400 : gray-500

  const CustomTooltip = ({ active, payload }: TooltipProps) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className={`rounded-lg border p-3 shadow-lg ${
          isDarkTheme 
            ? 'bg-gray-800 border-gray-600 text-white' 
            : 'bg-white border-gray-200 text-gray-900'
        }`}>
          <p className="text-sm font-medium">{data.name}</p>
          <p className="text-sm" style={{ color: data.color }}>
            Value: {data.value}
          </p>
          {data.payload.total && (
            <p className="text-sm text-gray-500">
              {((data.value / data.payload.total) * 100).toFixed(1)}%
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  const CustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: LabelProps) => {
    if (!showValue || 
        cx === undefined || 
        cy === undefined || 
        midAngle === undefined || 
        innerRadius === undefined || 
        outerRadius === undefined || 
        percent === undefined) {
      return null;
    }
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill={textColor} 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize={12}
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  // Calculate total for percentage calculations
  const total = data.reduce((sum, entry) => sum + entry.value, 0);
  const dataWithTotal = data.map(item => ({ ...item, total }));

  return (
    <div className={`relative w-full ${className}`}>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={dataWithTotal}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={showValue ? CustomLabel : false}
            outerRadius={outerRadius}
            innerRadius={innerRadius}
            fill="#8884d8"
            dataKey="value"
          >
            {dataWithTotal.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.color || colors[index % colors.length]} 
              />
            ))}
          </Pie>
          {showTooltip && <Tooltip content={<CustomTooltip />} />}
          {showLegend && (
            <Legend 
              wrapperStyle={{ color: textColor }}
              iconType="circle"
            />
          )}
        </PieChart>
      </ResponsiveContainer>
      
      {/* Center Text */}
      {(centerText || centerValue) && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            {centerValue && (
              <div className={`text-2xl font-bold ${isDarkTheme ? 'text-white' : 'text-gray-900'}`}>
                {centerValue}
              </div>
            )}
            {centerText && (
              <div className={`text-sm ${isDarkTheme ? 'text-gray-400' : 'text-gray-500'}`}>
                {centerText}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const DonutChart = React.memo(DonutChartComponent);
export default DonutChart; 