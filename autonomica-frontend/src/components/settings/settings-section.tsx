'use client';

import { useState } from 'react';
import { SettingsSection as SettingsSectionType, Settings } from '@/types/settings';
import SettingsFieldComponent from './settings-field';

interface SettingsSectionProps {
  section: SettingsSectionType;
  settings: Partial<Settings>;
  onSettingChange: (sectionId: string, fieldId: string, value: string | number | boolean) => void;
  errors?: Record<string, string>;
}

export default function SettingsSection({ section, settings, onSettingChange, errors }: SettingsSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const getNestedValue = (obj: Record<string, unknown>, path: string): string | number | boolean | undefined => {
    return path.split('.').reduce((current, key) => {
      if (current && typeof current === 'object' && key in current) {
        return (current as Record<string, unknown>)[key];
      }
      return undefined;
    }, obj as unknown) as string | number | boolean | undefined;
  };

  const handleFieldChange = (fieldId: string, value: string | number | boolean) => {
    onSettingChange(section.id, fieldId, value);
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
      {/* Section Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 text-left hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-inset"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">{section.icon}</span>
            <div>
              <h3 className="text-lg font-semibold text-white">{section.title}</h3>
              <p className="text-sm text-gray-400">{section.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-400">
              {isExpanded ? 'Collapse' : 'Expand'}
            </span>
            <svg
              className={`w-5 h-5 text-gray-400 transform transition-transform ${
                isExpanded ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </button>

      {/* Section Content */}
      {isExpanded && (
        <div className="px-6 pb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {section.fields.map((field) => {
              const fieldId = field.id.includes('.') ? field.id : `${section.id}.${field.id}`;
              const currentValue = getNestedValue(settings as Record<string, unknown>, fieldId) ?? field.defaultValue;
              const fieldError = errors?.[fieldId];

              return (
                <div key={field.id} className="space-y-3">
                  <SettingsFieldComponent
                    field={field}
                    value={currentValue}
                    onChange={(value) => handleFieldChange(fieldId, value)}
                    error={fieldError}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
