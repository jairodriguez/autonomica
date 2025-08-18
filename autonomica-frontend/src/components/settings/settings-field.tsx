'use client';

import { useState } from 'react';
import { SettingsField } from '@/types/settings';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

interface SettingsFieldProps {
  field: SettingsField;
  value: string | number | boolean | undefined;
  onChange: (value: string | number | boolean) => void;
  error?: string;
}

export default function SettingsFieldComponent({ field, value, onChange, error }: SettingsFieldProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);

  const validateField = (value: string | number | boolean): string | null => {
    if (field.required && (!value || value.toString().trim() === '')) {
      return `${field.label} is required`;
    }

    if (field.validation?.pattern && value) {
      const regex = new RegExp(field.validation.pattern);
      if (!regex.test(value.toString())) {
        return `${field.label} format is invalid`;
      }
    }

    if (field.validation?.minLength && value && value.toString().length < field.validation.minLength) {
      return `${field.label} must be at least ${field.validation.minLength} characters`;
    }

    if (field.validation?.maxLength && value && value.toString().length > field.validation.maxLength) {
      return `${field.label} must be no more than ${field.validation.maxLength} characters`;
    }

    if (field.validation?.custom) {
      return field.validation.custom(value);
    }

    return null;
  };

  const handleChange = (newValue: string | number | boolean) => {
    const validationError = validateField(newValue);
    setFieldError(validationError);
    onChange(newValue);
  };

  const renderField = () => {
    switch (field.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value?.toString() || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={field.placeholder}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        );

      case 'password':
        return (
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={value?.toString() || ''}
              onChange={(e) => handleChange(e.target.value)}
              placeholder={field.placeholder}
              className="w-full px-3 py-2 pr-10 bg-gray-700 border border-gray-600 rounded-md text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300"
            >
              {showPassword ? (
                <EyeSlashIcon className="w-5 h-5" />
              ) : (
                <EyeIcon className="w-5 h-5" />
              )}
            </button>
          </div>
        );

      case 'select':
        return (
          <select
            value={value?.toString() || field.defaultValue?.toString() || ''}
            onChange={(e) => handleChange(e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            {field.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'textarea':
        return (
          <textarea
            value={value?.toString() || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={field.placeholder}
            rows={4}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-vertical"
          />
        );

      case 'toggle':
        return (
          <button
            type="button"
            onClick={() => handleChange(!value)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-800 ${
              value ? 'bg-purple-600' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                value ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        );

      case 'timezone':
        return (
          <select
            value={value?.toString() || field.defaultValue?.toString() || 'UTC'}
            onChange={(e) => handleChange(e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="UTC">UTC</option>
            <option value="America/New_York">Eastern Time (ET)</option>
            <option value="America/Chicago">Central Time (CT)</option>
            <option value="America/Denver">Mountain Time (MT)</option>
            <option value="America/Los_Angeles">Pacific Time (PT)</option>
            <option value="Europe/London">London (GMT)</option>
            <option value="Europe/Paris">Paris (CET)</option>
            <option value="Asia/Tokyo">Tokyo (JST)</option>
            <option value="Asia/Shanghai">Shanghai (CST)</option>
            <option value="Australia/Sydney">Sydney (AEDT)</option>
          </select>
        );

      default:
        return (
          <input
            type="text"
            value={value?.toString() || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={field.placeholder}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        );
    }
  };

  const finalError = error || fieldError;

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-200">
        {field.label}
        {field.required && <span className="text-red-400 ml-1">*</span>}
      </label>
      
      {renderField()}
      
      {field.helpText && (
        <p className="text-sm text-gray-400">{field.helpText}</p>
      )}
      
      {finalError && (
        <p className="text-sm text-red-400">{finalError}</p>
      )}
    </div>
  );
}
