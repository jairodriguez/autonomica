'use client';

import { useState } from 'react';
import SettingsPage from '@/components/settings/settings-page';
import { secureStorageUtils, secureStorage } from '@/lib/secure-storage';

export default function TestSettingsPage() {
  const [testResults, setTestResults] = useState<string[]>([]);

  const runTests = async () => {
    const results: string[] = [];
    
    try {
      // Test 1: Secure Storage
      results.push('🧪 Testing Secure Storage...');
      secureStorageUtils.storeApiKey('test-service', 'test-key-123');
      const retrievedKey = secureStorageUtils.getApiKey('test-service');
      if (retrievedKey === 'test-key-123') {
        results.push('✅ Secure storage test passed');
      } else {
        results.push('❌ Secure storage test failed');
      }

      // Test 2: Settings API
      results.push('🧪 Testing Settings API...');
      const testSettings = {
        apiKeys: { openai: 'sk-test-123' },
        posting: { bestTimes: true }
      };
      
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testSettings),
      });
      
      if (response.ok) {
        results.push('✅ Settings API POST test passed');
      } else {
        results.push('❌ Settings API POST test failed');
      }

      // Test 3: Settings Retrieval
      const getResponse = await fetch('/api/settings');
      if (getResponse.ok) {
        const data = await getResponse.json();
        if (data.success) {
          results.push('✅ Settings API GET test passed');
        } else {
          results.push('❌ Settings API GET test failed');
        }
      } else {
        results.push('❌ Settings API GET test failed');
      }

      // Test 4: Clear Test Data
      secureStorageUtils.removeApiKey('test-service');
      const clearedKey = secureStorageUtils.getApiKey('test-service');
      if (!clearedKey) {
        results.push('✅ Secure storage cleanup test passed');
      } else {
        results.push('❌ Secure storage cleanup test failed');
      }

    } catch (error) {
      results.push(`❌ Test error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    setTestResults(results);
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Test Controls */}
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-2xl font-bold text-white mb-4">Settings System Test Page</h1>
        <button
          onClick={runTests}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Run Tests
        </button>
        
        {testResults.length > 0 && (
          <div className="mt-4 p-4 bg-gray-800 rounded-md">
            <h3 className="text-lg font-semibold text-white mb-2">Test Results:</h3>
            <div className="space-y-1">
              {testResults.map((result, index) => (
                <div key={index} className="text-sm font-mono">
                  {result}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Settings Page */}
      <div className="p-6">
        <SettingsPage />
      </div>
    </div>
  );
}
