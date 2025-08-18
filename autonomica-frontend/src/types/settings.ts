export interface Settings {
  apiKeys: {
    openai: string;
    semrush: string;
    twitter: string;
    facebook: string;
    googleSearchConsole: string;
    linkedin?: string;
    instagram?: string;
  };
  posting: {
    frequency: {
      twitter: 'daily' | 'weekly' | 'custom';
      facebook: 'daily' | 'weekly' | 'custom';
      linkedin: 'daily' | 'weekly' | 'custom';
      instagram: 'daily' | 'weekly' | 'custom';
    };
    customSchedule: {
      twitter: string[]; // Cron expressions
      facebook: string[];
      linkedin: string[];
      instagram: string[];
    };
    bestTimes: boolean; // Use algorithm for best times
    timezone: string;
  };
  brandVoice: {
    tone: string;
    style: string;
    guidelines: string;
    examples: string[];
    industry: string;
    targetAudience: string;
  };
  features: {
    autoApprove: boolean;
    enableRepurposing: boolean;
    enableAnalytics: boolean;
    enableAITraining: boolean;
    enableNotifications: boolean;
  };
  appearance: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    dateFormat: string;
    timeFormat: '12h' | '24h';
  };
  notifications: {
    email: boolean;
    push: boolean;
    slack: boolean;
    webhook: string;
    frequency: 'immediate' | 'daily' | 'weekly';
  };
  security: {
    twoFactorAuth: boolean;
    sessionTimeout: number; // minutes
    passwordPolicy: 'weak' | 'medium' | 'strong';
    ipWhitelist: string[];
  };
}

export interface SettingsSection {
  id: string;
  title: string;
  description: string;
  icon: string;
  fields: SettingsField[];
}

export interface SettingsField {
  id: string;
  label: string;
  type: 'text' | 'password' | 'select' | 'textarea' | 'toggle' | 'multiselect' | 'timezone' | 'cron';
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  validation?: {
    pattern?: string;
    minLength?: number;
    maxLength?: number;
    custom?: (value: string | number | boolean) => string | null;
  };
  helpText?: string;
  defaultValue?: string | number | boolean;
}

export interface SettingsValidationError {
  field: string;
  message: string;
}

export interface SettingsSaveResult {
  success: boolean;
  message: string;
  errors?: SettingsValidationError[];
}
