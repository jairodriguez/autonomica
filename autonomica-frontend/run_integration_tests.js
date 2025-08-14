#!/usr/bin/env node
/**
 * Frontend Integration Test Runner for Autonomica
 * 
 * This script runs integration tests with proper environment setup,
 * Mock Service Worker configuration, and reporting.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class IntegrationTestRunner {
  constructor() {
    this.testResults = {
      passed: 0,
      failed: 0,
      total: 0,
      duration: 0
    };
    this.startTime = Date.now();
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = {
      info: 'ℹ️',
      success: '✅',
      error: '❌',
      warning: '⚠️',
      start: '🚀'
    }[type] || 'ℹ️';
    
    console.log(`${prefix} [${timestamp}] ${message}`);
  }

  checkDependencies() {
    this.log('Checking dependencies...', 'info');
    
    try {
      // Check if Jest is available
      execSync('npx jest --version', { stdio: 'pipe' });
      this.log('Jest is available', 'success');
    } catch (error) {
      this.log('Jest not found. Installing...', 'warning');
      try {
        execSync('npm install --save-dev jest', { stdio: 'pipe' });
        this.log('Jest installed successfully', 'success');
      } catch (installError) {
        this.log('Failed to install Jest', 'error');
        return false;
      }
    }

    try {
      // Check if MSW is available
      execSync('npx msw --version', { stdio: 'pipe' });
      this.log('MSW is available', 'success');
    } catch (error) {
      this.log('MSW not found. Installing...', 'warning');
      try {
        execSync('npm install --save-dev msw', { stdio: 'pipe' });
        this.log('MSW installed successfully', 'success');
      } catch (installError) {
        this.log('Failed to install MSW', 'error');
        return false;
      }
    }

    return true;
  }

  setupTestEnvironment() {
    this.log('Setting up test environment...', 'info');
    
    // Set test environment variables
    process.env.NODE_ENV = 'test';
    process.env.TESTING = 'true';
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = 'test-key';
    
    this.log('Environment variables set', 'success');
    
    // Create test configuration
    const testConfig = {
      testEnvironment: 'jsdom',
      setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
      testMatch: [
        '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
        '<rootDir>/src/**/*.{test,spec}.{js,jsx,ts,tsx}'
      ],
      collectCoverageFrom: [
        'src/**/*.{js,jsx,ts,tsx}',
        '!src/**/*.d.ts',
        '!src/**/*.stories.{js,jsx,ts,tsx}',
        '!src/**/*.test.{js,jsx,ts,tsx}',
        '!src/**/index.{js,jsx,ts,tsx}'
      ],
      coverageThreshold: {
        global: {
          branches: 60,
          functions: 60,
          lines: 60,
          statements: 60
        }
      },
      moduleNameMapping: {
        '^@/(.*)$': '<rootDir>/src/$1'
      },
      transform: {
        '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }]
      },
      transformIgnorePatterns: [
        '/node_modules/',
        '^.+\\.module\\.(css|sass|scss)$'
      ]
    };
    
    // Write test configuration to file
    const configPath = path.join(__dirname, 'jest.integration.config.js');
    const configContent = `module.exports = ${JSON.stringify(testConfig, null, 2)};`;
    
    try {
      fs.writeFileSync(configPath, configContent);
      this.log('Integration test configuration created', 'success');
    } catch (error) {
      this.log('Failed to create test configuration', 'error');
      return false;
    }
    
    return true;
  }

  runIntegrationTests() {
    this.log('Running integration tests...', 'start');
    
    try {
      const testCommand = 'npx jest --config jest.integration.config.js --testPathPattern=integration --coverage --verbose';
      this.log(`Executing: ${testCommand}`, 'info');
      
      const result = execSync(testCommand, { 
        stdio: 'inherit',
        cwd: __dirname 
      });
      
      this.log('Integration tests completed successfully', 'success');
      return true;
    } catch (error) {
      this.log('Integration tests failed', 'error');
      return false;
    }
  }

  runSpecificIntegrationTests(testPattern = '') {
    this.log(`Running specific integration tests: ${testPattern || 'all'}`, 'info');
    
    try {
      let testCommand = 'npx jest --config jest.integration.config.js --testPathPattern=integration';
      
      if (testPattern) {
        testCommand += ` --testNamePattern="${testPattern}"`;
      }
      
      testCommand += ' --coverage --verbose';
      
      this.log(`Executing: ${testCommand}`, 'info');
      
      const result = execSync(testCommand, { 
        stdio: 'inherit',
        cwd: __dirname 
      });
      
      this.log('Specific integration tests completed successfully', 'success');
      return true;
    } catch (error) {
      this.log('Specific integration tests failed', 'error');
      return false;
    }
  }

  generateTestReport() {
    this.log('Generating test report...', 'info');
    
    const endTime = Date.now();
    const duration = (endTime - this.startTime) / 1000;
    
    console.log('\n📊 Integration Test Report');
    console.log('=' .repeat(50));
    console.log(`⏱️  Total Duration: ${duration.toFixed(2)}s`);
    console.log(`✅ Tests Passed: ${this.testResults.passed}`);
    console.log(`❌ Tests Failed: ${this.testResults.failed}`);
    console.log(`📊 Total Tests: ${this.testResults.total}`);
    
    // Check for coverage reports
    const coverageDir = path.join(__dirname, 'coverage');
    if (fs.existsSync(coverageDir)) {
      console.log('\n📁 Coverage Reports:');
      console.log(`  - HTML: ${path.join(coverageDir, 'lcov-report', 'index.html')}`);
      console.log(`  - LCOV: ${path.join(coverageDir, 'lcov.info')}`);
      console.log(`  - JSON: ${path.join(coverageDir, 'coverage-final.json')}`);
    }
    
    // Check for test results
    const testResultsDir = path.join(__dirname, 'test-results');
    if (fs.existsSync(testResultsDir)) {
      console.log('\n📁 Test Results:');
      const files = fs.readdirSync(testResultsDir);
      files.forEach(file => {
        console.log(`  - ${file}`);
      });
    }
  }

  cleanup() {
    this.log('Cleaning up test environment...', 'info');
    
    try {
      // Remove temporary test configuration
      const configPath = path.join(__dirname, 'jest.integration.config.js');
      if (fs.existsSync(configPath)) {
        fs.unlinkSync(configPath);
        this.log('Test configuration cleaned up', 'success');
      }
      
      // Clean up environment variables
      delete process.env.NODE_ENV;
      delete process.env.TESTING;
      delete process.env.NEXT_PUBLIC_API_URL;
      delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
      
    } catch (error) {
      this.log('Cleanup failed', 'warning');
    }
  }

  async run() {
    this.log('🚀 Autonomica Frontend Integration Test Runner', 'start');
    console.log('=' .repeat(60));
    
    try {
      // Check dependencies
      if (!this.checkDependencies()) {
        this.log('Dependency check failed', 'error');
        return false;
      }
      
      // Setup test environment
      if (!this.setupTestEnvironment()) {
        this.log('Test environment setup failed', 'error');
        return false;
      }
      
      // Run integration tests
      const success = this.runIntegrationTests();
      
      // Generate report
      this.generateTestReport();
      
      return success;
      
    } catch (error) {
      this.log(`Unexpected error: ${error.message}`, 'error');
      return false;
    } finally {
      this.cleanup();
    }
  }

  async runSpecific(pattern) {
    this.log(`🚀 Running specific integration tests: ${pattern}`, 'start');
    
    try {
      // Setup test environment
      if (!this.setupTestEnvironment()) {
        return false;
      }
      
      // Run specific tests
      const success = this.runSpecificIntegrationTests(pattern);
      
      // Generate report
      this.generateTestReport();
      
      return success;
      
    } catch (error) {
      this.log(`Unexpected error: ${error.message}`, 'error');
      return false;
    } finally {
      this.cleanup();
    }
  }
}

// CLI interface
if (require.main === module) {
  const runner = new IntegrationTestRunner();
  
  const args = process.argv.slice(2);
  const pattern = args[0];
  
  if (pattern && pattern !== '--help') {
    runner.runSpecific(pattern).then(success => {
      process.exit(success ? 0 : 1);
    });
  } else if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Usage: node run_integration_tests.js [pattern] [options]

Options:
  pattern           Run tests matching the specified pattern
  --help, -h       Show this help message

Examples:
  node run_integration_tests.js                    # Run all integration tests
  node run_integration_tests.js "chat"            # Run tests with "chat" in name
  node run_integration_tests.js "authentication"  # Run authentication tests
    `);
    process.exit(0);
  } else {
    runner.run().then(success => {
      process.exit(success ? 0 : 1);
    });
  }
}

module.exports = IntegrationTestRunner;