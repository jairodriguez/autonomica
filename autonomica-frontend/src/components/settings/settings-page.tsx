'use client';

import { useState, useEffect } from 'react';
import { Settings, SettingsSaveResult } from '@/types/settings';
import { SETTINGS_SECTIONS } from '@/lib/settings-config';
import { secureStorageUtils, secureStorage } from '@/lib/secure-storage';
import SettingsSection from './settings-section';
import { CheckIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

export default function SettingsPage() {
  const [settings, setSettings] = useState<Partial<Settings>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saveResult, setSaveResult] = useState<SettingsSaveResult | null>(null);

  // Load settings from secure storage and API
  useEffect(() => {
    const loadSettings = async () => {
      try {
        // Load default settings from configuration
        const defaultSettings: Partial<Settings> = {};
        
        SETTINGS_SECTIONS.forEach(section => {
          section.fields.forEach(field => {
            if (field.defaultValue !== undefined) {
              const fieldId = field.id.includes('.') ? field.id : `${section.id}.${field.id}`;
              setNestedValue(defaultSettings, fieldId, field.defaultValue);
            }
          });
        });

        // Load saved settings from secure storage
        const savedSettings = secureStorageUtils.getSettings();
        
        // Try to load settings from API
        let apiSettings = {};
        try {
          const response = await fetch('/api/settings');
          if (response.ok) {
            const result = await response.json();
            if (result.success) {
              apiSettings = result.data || {};
            }
          }
        } catch (error) {
          console.warn('Failed to load settings from API, using local storage only:', error);
        }
        
        // Merge settings: API > Secure Storage > Defaults
        const mergedSettings = { ...defaultSettings, ...savedSettings, ...apiSettings };
        setSettings(mergedSettings);
      } catch (error) {
        console.error('Failed to load settings:', error);
        // Fallback to default settings only
        const defaultSettings: Partial<Settings> = {};
        SETTINGS_SECTIONS.forEach(section => {
          section.fields.forEach(field => {
            if (field.defaultValue !== undefined) {
              const fieldId = field.id.includes('.') ? field.id : `${section.id}.${field.id}`;
              setNestedValue(defaultSettings, fieldId, field.defaultValue);
            }
          });
        });
        setSettings(defaultSettings);
      } finally {
        setIsLoading(false);
      }
    };

    loadSettings();
  }, []);

  const setNestedValue = (obj: Record<string, unknown>, path: string, value: string | number | boolean) => {
    const keys = path.split('.');
    const lastKey = keys.pop()!;
    const target = keys.reduce((current, key) => {
      if (!current[key] || typeof current[key] !== 'object') {
        current[key] = {};
      }
      return current[key] as Record<string, unknown>;
    }, obj as Record<string, unknown>);
    target[lastKey] = value;
  };

  const handleSettingChange = (sectionId: string, fieldId: string, value: string | number | boolean) => {
    setSettings(prev => {
      const newSettings = { ...prev };
      setNestedValue(newSettings as Record<string, unknown>, fieldId, value);
      return newSettings;
    });

    // Clear error for this field
    if (errors[fieldId]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[fieldId];
        return newErrors;
      });
    }
  };

  const validateSettings = (): Record<string, string> => {
    const newErrors: Record<string, string> = {};

    SETTINGS_SECTIONS.forEach(section => {
      section.fields.forEach(field => {
        if (field.required) {
          const fieldId = field.id.includes('.') ? field.id : `${section.id}.${field.id}`;
          const value = getNestedValue(settings as Record<string, unknown>, fieldId);
          
          if (!value || value.toString().trim() === '') {
            newErrors[fieldId] = `${field.label} is required`;
          }
        }

        // Additional validation for specific fields
        if (field.validation) {
          const fieldId = field.id.includes('.') ? field.id : `${section.id}.${field.id}`;
          const value = getNestedValue(settings as Record<string, unknown>, fieldId);
          
          if (value && field.validation.pattern) {
            const regex = new RegExp(field.validation.pattern);
            if (!regex.test(value.toString())) {
              newErrors[fieldId] = `${field.label} format is invalid`;
            }
          }

          if (value && field.validation.custom) {
            const customError = field.validation.custom(value);
            if (customError) {
              newErrors[fieldId] = customError;
            }
          }
        }
      });
    });

    return newErrors;
  };

  const getNestedValue = (obj: Record<string, unknown>, path: string): string | number | boolean | undefined => {
    return path.split('.').reduce((current, key) => {
      if (current && typeof current === 'object' && key in current) {
        return (current as Record<string, unknown>)[key];
      }
      return undefined;
    }, obj as unknown) as string | number | boolean | undefined;
  };

  const handleSave = async () => {
    const validationErrors = validateSettings();
    
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      setSaveResult({
        success: false,
        message: 'Please fix the validation errors before saving.',
        errors: Object.entries(validationErrors).map(([field, message]) => ({
          field,
          message
        }))
      });
      return;
    }

    setIsSaving(true);
    setErrors({});

    try {
      // Save settings to secure storage
      secureStorageUtils.storeSettings(settings as Record<string, unknown>);

      // Save settings to API
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        setSaveResult({
          success: true,
          message: 'Settings saved successfully!'
        });
      } else {
        throw new Error(result.message || 'Failed to save settings');
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSaveResult(null), 3000);

    } catch (error) {
      console.error('Failed to save settings:', error);
      setSaveResult({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to save settings. Please try again.'
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all settings to defaults? This action cannot be undone.')) {
      const defaultSettings: Partial<Settings> = {};
      
      SETTINGS_SECTIONS.forEach(section => {
        section.fields.forEach(field => {
          if (field.defaultValue !== undefined) {
            const fieldId = field.id.includes('.') ? field.id : `${section.id}.${field.id}`;
            setNestedValue(defaultSettings as Record<string, unknown>, fieldId, field.defaultValue);
          }
        });
      });

      setSettings(defaultSettings);
      setErrors({});
      setSaveResult(null);
      
      // Clear saved settings from storage
      try {
        secureStorage.clearSecureItems();
        localStorage.clear();
      } catch (error) {
        console.warn('Failed to clear storage:', error);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-gray-400">Configure your dashboard and system preferences</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={handleReset}
            className="px-4 py-2 text-sm font-medium text-gray-300 bg-gray-700 border border-gray-600 rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-800"
          >
            Reset to Defaults
          </button>
          
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>

      {/* Save Result Message */}
      {saveResult && (
        <div className={`p-4 rounded-md border ${
          saveResult.success 
            ? 'bg-green-900/20 border-green-700 text-green-300' 
            : 'bg-red-900/20 border-red-700 text-red-300'
        }`}>
          <div className="flex items-center space-x-2">
            {saveResult.success ? (
              <CheckIcon className="w-5 h-5 text-green-400" />
            ) : (
              <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
            )}
            <span>{saveResult.message}</span>
          </div>
        </div>
      )}

      {/* Settings Sections */}
      <div className="space-y-6">
        {SETTINGS_SECTIONS.map((section) => (
          <SettingsSection
            key={section.id}
            section={section}
            settings={settings}
            onSettingChange={handleSettingChange}
            errors={errors}
          />
        ))}
      </div>
    </div>
  );
}
