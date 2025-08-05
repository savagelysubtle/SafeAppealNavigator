import React, { useState } from 'react';
import { useAppContext } from '../../../contexts/AppContext';
import ToggleSwitch from '../../ui/ToggleSwitch';
import { Theme } from '../../../types';

interface UIPreferences {
  theme: Theme;
  language: string;
  timezone: string;
  dateFormat: string;
  animations: boolean;
  compactMode: boolean;
  autoSave: boolean;
  autoSaveInterval: number;
  showLineNumbers: boolean;
  fontSize: string;
  fontFamily: string;
  notifications: {
    desktop: boolean;
    sound: boolean;
    taskComplete: boolean;
    errors: boolean;
    updates: boolean;
  };
  accessibility: {
    highContrast: boolean;
    reducedMotion: boolean;
    screenReaderOptimized: boolean;
    keyboardShortcuts: boolean;
  };
}

const PreferencesTab: React.FC = () => {
  const { theme, toggleTheme, addAuditLogEntry } = useAppContext();
  const [preferences, setPreferences] = useState<UIPreferences>({
    theme: theme,
    language: 'en',
    timezone: 'America/New_York',
    dateFormat: 'MM/DD/YYYY',
    animations: true,
    compactMode: false,
    autoSave: true,
    autoSaveInterval: 60,
    showLineNumbers: true,
    fontSize: 'medium',
    fontFamily: 'default',
    notifications: {
      desktop: true,
      sound: true,
      taskComplete: true,
      errors: true,
      updates: false
    },
    accessibility: {
      highContrast: false,
      reducedMotion: false,
      screenReaderOptimized: false,
      keyboardShortcuts: true
    }
  });

  const handlePreferenceChange = (category: keyof UIPreferences, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [category]: value
    }));
  };

  const handleNotificationChange = (field: keyof UIPreferences['notifications'], value: boolean) => {
    setPreferences(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [field]: value
      }
    }));
  };

  const handleAccessibilityChange = (field: keyof UIPreferences['accessibility'], value: boolean) => {
    setPreferences(prev => ({
      ...prev,
      accessibility: {
        ...prev.accessibility,
        [field]: value
      }
    }));
  };

  const savePreferences = () => {
    addAuditLogEntry('PREFERENCES_SAVED', 'User preferences updated');
  };

  const resetToDefaults = () => {
    // Reset to default preferences
    addAuditLogEntry('PREFERENCES_RESET', 'Preferences reset to defaults');
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-semibold text-textPrimary">User Preferences</h2>

      {/* Appearance */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-medium text-textPrimary mb-4">Appearance</h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-textPrimary">Theme</p>
              <p className="text-xs text-textSecondary">Choose between light and dark mode</p>
            </div>
            <ToggleSwitch
              id="theme-toggle"
              checked={preferences.theme === Theme.Dark}
              onChange={() => {
                toggleTheme();
                handlePreferenceChange('theme', preferences.theme === Theme.Dark ? Theme.Light : Theme.Dark);
              }}
              label={preferences.theme === Theme.Dark ? 'Dark' : 'Light'}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-textSecondary mb-1">
              Font Size
            </label>
            <select
              value={preferences.fontSize}
              onChange={(e) => handlePreferenceChange('fontSize', e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
              <option value="extra-large">Extra Large</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-textSecondary mb-1">
              Font Family
            </label>
            <select
              value={preferences.fontFamily}
              onChange={(e) => handlePreferenceChange('fontFamily', e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="default">System Default</option>
              <option value="inter">Inter</option>
              <option value="roboto">Roboto</option>
              <option value="source-sans">Source Sans Pro</option>
              <option value="monospace">Monospace</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={preferences.animations}
                onChange={(e) => handlePreferenceChange('animations', e.target.checked)}
                className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
              />
              <span className="ml-2 text-sm text-textSecondary">Enable animations</span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={preferences.compactMode}
                onChange={(e) => handlePreferenceChange('compactMode', e.target.checked)}
                className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
              />
              <span className="ml-2 text-sm text-textSecondary">Compact mode</span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={preferences.showLineNumbers}
                onChange={(e) => handlePreferenceChange('showLineNumbers', e.target.checked)}
                className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
              />
              <span className="ml-2 text-sm text-textSecondary">Show line numbers in code editor</span>
            </label>
          </div>
        </div>
      </div>

      {/* Localization */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-medium text-textPrimary mb-4">Localization</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-textSecondary mb-1">
              Language
            </label>
            <select
              value={preferences.language}
              onChange={(e) => handlePreferenceChange('language', e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="de">Deutsch</option>
              <option value="ja">日本語</option>
              <option value="zh">中文</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-textSecondary mb-1">
              Timezone
            </label>
            <select
              value={preferences.timezone}
              onChange={(e) => handlePreferenceChange('timezone', e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="America/New_York">Eastern Time</option>
              <option value="America/Chicago">Central Time</option>
              <option value="America/Denver">Mountain Time</option>
              <option value="America/Los_Angeles">Pacific Time</option>
              <option value="Europe/London">GMT</option>
              <option value="Europe/Paris">CET</option>
              <option value="Asia/Tokyo">JST</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-textSecondary mb-1">
              Date Format
            </label>
            <select
              value={preferences.dateFormat}
              onChange={(e) => handlePreferenceChange('dateFormat', e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
              <option value="DD-MMM-YYYY">DD-MMM-YYYY</option>
            </select>
          </div>
        </div>
      </div>

      {/* Auto-save */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-medium text-textPrimary mb-4">Auto-save Settings</h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-textPrimary">Enable Auto-save</p>
              <p className="text-xs text-textSecondary">Automatically save your work</p>
            </div>
            <ToggleSwitch
              id="autosave-toggle"
              checked={preferences.autoSave}
              onChange={(checked) => handlePreferenceChange('autoSave', checked)}
              label={preferences.autoSave ? 'Enabled' : 'Disabled'}
            />
          </div>

          {preferences.autoSave && (
            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Auto-save Interval (seconds)
              </label>
              <input
                type="number"
                min="10"
                max="300"
                value={preferences.autoSaveInterval}
                onChange={(e) => handlePreferenceChange('autoSaveInterval', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          )}
        </div>
      </div>

      {/* Notifications */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-medium text-textPrimary mb-4">Notifications</h3>

        <div className="space-y-3">
          <label className="flex items-center justify-between">
            <span className="text-sm text-textSecondary">Desktop notifications</span>
            <input
              type="checkbox"
              checked={preferences.notifications.desktop}
              onChange={(e) => handleNotificationChange('desktop', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
          </label>

          <label className="flex items-center justify-between">
            <span className="text-sm text-textSecondary">Sound notifications</span>
            <input
              type="checkbox"
              checked={preferences.notifications.sound}
              onChange={(e) => handleNotificationChange('sound', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
          </label>

          <label className="flex items-center justify-between">
            <span className="text-sm text-textSecondary">Task completion alerts</span>
            <input
              type="checkbox"
              checked={preferences.notifications.taskComplete}
              onChange={(e) => handleNotificationChange('taskComplete', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
          </label>

          <label className="flex items-center justify-between">
            <span className="text-sm text-textSecondary">Error notifications</span>
            <input
              type="checkbox"
              checked={preferences.notifications.errors}
              onChange={(e) => handleNotificationChange('errors', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
          </label>

          <label className="flex items-center justify-between">
            <span className="text-sm text-textSecondary">Update notifications</span>
            <input
              type="checkbox"
              checked={preferences.notifications.updates}
              onChange={(e) => handleNotificationChange('updates', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
          </label>
        </div>
      </div>

      {/* Accessibility */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-medium text-textPrimary mb-4">Accessibility</h3>

        <div className="space-y-3">
          <label className="flex items-center justify-between">
            <span className="text-sm text-textSecondary">High contrast mode</span>
            <input
              type="checkbox"
              checked={preferences.accessibility.highContrast}
              onChange={(e) => handleAccessibilityChange('highContrast', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
          </label>

          <label className="flex items-center justify-between">
            <span className="text-sm text-textSecondary">Reduce motion</span>
            <input
              type="checkbox"
              checked={preferences.accessibility.reducedMotion}
              onChange={(e) => handleAccessibilityChange('reducedMotion', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
          </label>

          <label className="flex items-center justify-between">
            <span className="text-sm text-textSecondary">Screen reader optimization</span>
            <input
              type="checkbox"
              checked={preferences.accessibility.screenReaderOptimized}
              onChange={(e) => handleAccessibilityChange('screenReaderOptimized', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
          </label>

          <label className="flex items-center justify-between">
            <span className="text-sm text-textSecondary">Enable keyboard shortcuts</span>
            <input
              type="checkbox"
              checked={preferences.accessibility.keyboardShortcuts}
              onChange={(e) => handleAccessibilityChange('keyboardShortcuts', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
          </label>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between">
        <button
          onClick={resetToDefaults}
          className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
        >
          Reset to Defaults
        </button>
        <button
          onClick={savePreferences}
          className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
        >
          Save Preferences
        </button>
      </div>
    </div>
  );
};

export default PreferencesTab;