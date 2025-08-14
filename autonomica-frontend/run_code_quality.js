#!/usr/bin/env node
/**
 * Frontend Code Quality Runner for Autonomica
 * 
 * This script runs comprehensive code quality checks including:
 * - ESLint linting
 * - Prettier formatting
 * - Stylelint CSS/SCSS linting
 * - TypeScript type checking
 * - Jest testing
 * - Bundle analysis
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class FrontendCodeQualityRunner {
  constructor() {
    this.projectRoot = process.cwd();
    this.startTime = Date.now();
    this.results = {
      eslint: { status: 'pending', output: '', errors: [] },
      prettier: { status: 'pending', output: '', errors: [] },
      stylelint: { status: 'pending', output: '', errors: [] },
      typescript: { status: 'pending', output: '', errors: [] },
      testing: { status: 'pending', output: '', errors: [] },
      bundle: { status: 'pending', output: '', errors: [] },
      overall: { status: 'pending', score: 0 }
    };
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

  runCommand(command, options = {}) {
    try {
      const result = execSync(command, {
        cwd: this.projectRoot,
        stdio: options.captureOutput ? 'pipe' : 'inherit',
        timeout: options.timeout || 300000, // 5 minutes
        ...options
      });
      
      if (options.captureOutput) {
        return { success: true, output: result.toString() };
      }
      return { success: true, output: '' };
    } catch (error) {
      if (options.captureOutput) {
        return { 
          success: false, 
          output: error.stdout?.toString() || '', 
          error: error.stderr?.toString() || error.message 
        };
      }
      return { success: false, output: '', error: error.message };
    }
  }

  checkDependencies() {
    this.log('Checking code quality tool dependencies...', 'info');
    
    const requiredTools = [
      { name: 'ESLint', command: 'npx eslint --version' },
      { name: 'Prettier', command: 'npx prettier --version' },
      { name: 'Stylelint', command: 'npx stylelint --version' },
      { name: 'TypeScript', command: 'npx tsc --version' },
      { name: 'Jest', command: 'npx jest --version' }
    ];
    
    let allAvailable = true;
    
    for (const tool of requiredTools) {
      try {
        const result = this.runCommand(tool.command, { captureOutput: true });
        if (result.success) {
          this.log(`  ✅ ${tool.name} available`, 'success');
        } else {
          this.log(`  ❌ ${tool.name} not working properly`, 'error');
          allAvailable = false;
        }
      } catch (error) {
        this.log(`  ❌ ${tool.name} not found`, 'error');
        allAvailable = false;
      }
    }
    
    if (!allAvailable) {
      this.log('Some tools are missing. Install with: npm install', 'warning');
      return false;
    }
    
    return true;
  }

  runESLint() {
    this.log('Running ESLint checks...', 'start');
    
    const result = this.runCommand('npx eslint . --ext .js,.jsx,.ts,.tsx --format=compact', { 
      captureOutput: true 
    });
    
    if (result.success) {
      this.log('  ✅ ESLint checks passed', 'success');
      this.results.eslint.status = 'passed';
    } else {
      this.log('  ❌ ESLint checks failed', 'error');
      this.results.eslint.status = 'failed';
      this.results.eslint.output = result.output;
      this.results.eslint.errors = result.output.split('\n').filter(line => line.trim());
    }
    
    return this.results.eslint.status === 'passed';
  }

  runPrettier() {
    this.log('Running Prettier formatting checks...', 'start');
    
    const result = this.runCommand('npx prettier --check "**/*.{js,jsx,ts,tsx,json,css,scss,md}"', { 
      captureOutput: true 
    });
    
    if (result.success) {
      this.log('  ✅ Prettier formatting checks passed', 'success');
      this.results.prettier.status = 'passed';
    } else {
      this.log('  ❌ Prettier formatting checks failed', 'error');
      this.results.prettier.status = 'failed';
      this.results.prettier.output = result.output;
      this.results.prettier.errors = result.output.split('\n').filter(line => line.trim());
    }
    
    return this.results.prettier.status === 'passed';
  }

  runStylelint() {
    this.log('Running Stylelint checks...', 'start');
    
    const result = this.runCommand('npx stylelint "**/*.{css,scss}" --formatter=compact', { 
      captureOutput: true 
    });
    
    if (result.success) {
      this.log('  ✅ Stylelint checks passed', 'success');
      this.results.stylelint.status = 'passed';
    } else {
      this.log('  ❌ Stylelint checks failed', 'error');
      this.results.stylelint.status = 'failed';
      this.results.stylelint.output = result.output;
      this.results.stylelint.errors = result.output.split('\n').filter(line => line.trim());
    }
    
    return this.results.stylelint.status === 'passed';
  }

  runTypeScript() {
    this.log('Running TypeScript type checking...', 'start');
    
    const result = this.runCommand('npx tsc --noEmit --project .', { 
      captureOutput: true 
    });
    
    if (result.success) {
      this.log('  ✅ TypeScript type checking passed', 'success');
      this.results.typescript.status = 'passed';
    } else {
      this.log('  ❌ TypeScript type checking failed', 'error');
      this.results.typescript.status = 'failed';
      this.results.typescript.output = result.output;
      this.results.typescript.errors = result.output.split('\n').filter(line => line.trim());
    }
    
    return this.results.typescript.status === 'passed';
  }

  runTesting() {
    this.log('Running Jest tests...', 'start');
    
    const result = this.runCommand('npm run test:ci', { 
      captureOutput: true 
    });
    
    if (result.success) {
      this.log('  ✅ Jest tests passed', 'success');
      this.results.testing.status = 'passed';
    } else {
      this.log('  ❌ Jest tests failed', 'error');
      this.results.testing.status = 'failed';
      this.results.testing.output = result.output;
      this.results.testing.errors = result.output.split('\n').filter(line => line.trim());
    }
    
    return this.results.testing.status === 'passed';
  }

  runBundleAnalysis() {
    this.log('Running bundle analysis...', 'start');
    
    // Check if build directory exists
    const buildDir = path.join(this.projectRoot, '.next');
    if (!fs.existsSync(buildDir)) {
      this.log('  ⚠️  Build directory not found, skipping bundle analysis', 'warning');
      this.results.bundle.status = 'skipped';
      return true;
    }
    
    // Check bundle size
    try {
      const bundleStats = fs.readFileSync(path.join(buildDir, 'build-manifest.json'), 'utf8');
      const manifest = JSON.parse(bundleStats);
      
      // Simple bundle size check
      const totalSize = Object.keys(manifest).length;
      this.log(`  📊 Bundle contains ${totalSize} files`, 'info');
      
      this.results.bundle.status = 'passed';
      this.results.bundle.output = `Bundle contains ${totalSize} files`;
    } catch (error) {
      this.log('  ⚠️  Could not analyze bundle, skipping', 'warning');
      this.results.bundle.status = 'skipped';
    }
    
    return true;
  }

  autoFixIssues() {
    this.log('Auto-fixing code quality issues...', 'start');
    
    // Fix ESLint issues
    this.log('  🔧 Fixing ESLint issues...', 'info');
    this.runCommand('npx eslint . --ext .js,.jsx,.ts,.tsx --fix');
    
    // Fix Prettier formatting
    this.log('  🎨 Fixing Prettier formatting...', 'info');
    this.runCommand('npx prettier --write "**/*.{js,jsx,ts,tsx,json,css,scss,md}"');
    
    // Fix Stylelint issues
    this.log('  🎨 Fixing Stylelint issues...', 'info');
    this.runCommand('npx stylelint "**/*.{css,scss}" --fix');
    
    this.log('  ✅ Auto-fix completed', 'success');
  }

  calculateScore() {
    const checks = Object.values(this.results).filter(result => 
      typeof result === 'object' && result.status !== 'pending'
    );
    
    const passed = checks.filter(result => result.status === 'passed').length;
    const total = checks.length;
    
    this.results.overall.score = total > 0 ? Math.round((passed / total) * 100) : 0;
    this.results.overall.status = this.results.overall.score === 100 ? 'excellent' : 
                                 this.results.overall.score >= 80 ? 'good' :
                                 this.results.overall.score >= 60 ? 'fair' : 'poor';
  }

  generateReport() {
    this.log('Generating code quality report...', 'info');
    
    const endTime = Date.now();
    const duration = (endTime - this.startTime) / 1000;
    
    console.log('\n' + '='.repeat(80));
    console.log('📊 FRONTEND CODE QUALITY REPORT');
    console.log('='.repeat(80));
    console.log(`⏱️  Total Duration: ${duration.toFixed(2)}s`);
    console.log(`📁 Project: ${path.basename(this.projectRoot)}`);
    console.log(`📅 Generated: ${new Date().toLocaleString()}`);
    console.log();
    
    // Overall Score
    console.log('📈 OVERALL SCORE');
    console.log('-'.repeat(40));
    const scoreEmoji = {
      excellent: '🎉',
      good: '✅',
      fair: '⚠️',
      poor: '❌'
    }[this.results.overall.status] || '❓';
    
    console.log(`${scoreEmoji} Score: ${this.results.overall.score}/100 (${this.results.overall.status})`);
    console.log();
    
    // Detailed Results
    console.log('🔍 DETAILED RESULTS');
    console.log('-'.repeat(40));
    
    const statusEmojis = {
      passed: '✅',
      failed: '❌',
      skipped: '⏭️',
      pending: '⏳'
    };
    
    for (const [checkName, result] of Object.entries(this.results)) {
      if (checkName === 'overall') continue;
      
      const statusEmoji = statusEmojis[result.status] || '❓';
      console.log(`${statusEmoji} ${checkName.charAt(0).toUpperCase() + checkName.slice(1)}: ${result.status}`);
      
      if (result.errors && result.errors.length > 0) {
        const errorCount = result.errors.length;
        console.log(`    • ${errorCount} issue${errorCount > 1 ? 's' : ''} found`);
        if (errorCount <= 3) {
          result.errors.forEach(error => console.log(`      - ${error}`));
        } else {
          result.errors.slice(0, 3).forEach(error => console.log(`      - ${error}`));
          console.log(`      ... and ${errorCount - 3} more issues`);
        }
      }
    }
    
    console.log();
    
    // Recommendations
    console.log('💡 RECOMMENDATIONS');
    console.log('-'.repeat(40));
    
    const failedChecks = Object.entries(this.results)
      .filter(([key, result]) => key !== 'overall' && result.status === 'failed')
      .map(([key]) => key);
    
    if (failedChecks.length > 0) {
      console.log('❌ Issues found that need attention:');
      failedChecks.forEach(check => {
        console.log(`  • ${check.charAt(0).toUpperCase() + check.slice(1)}: Fix issues shown above`);
      });
      
      console.log('\n🔧 To auto-fix formatting issues, run:');
      console.log('   npm run quality:fix');
      console.log('   or');
      console.log('   node run_code_quality.js --auto-fix');
    } else {
      console.log('🎉 All code quality checks passed! Your code is in excellent shape.');
    }
    
    console.log('\n📚 For more information:');
    console.log('  • ESLint: Check console output above for specific issues');
    console.log('  • Prettier: Run "npm run format:prettier" to format all files');
    console.log('  • Stylelint: Run "npm run lint:stylelint:fix" to fix CSS issues');
    console.log('  • TypeScript: Check tsconfig.json for configuration options');
    
    console.log('='.repeat(80));
  }

  async runAllChecks(autoFix = false) {
    this.log('🚀 Starting comprehensive frontend code quality analysis', 'start');
    console.log(`📁 Project: ${path.basename(this.projectRoot)}`);
    console.log(`⏰ Started: ${new Date().toLocaleString()}`);
    console.log();
    
    // Check dependencies
    if (!this.checkDependencies()) {
      this.log('❌ Dependency check failed', 'error');
      return false;
    }
    
    // Run all checks
    const checks = [
      { name: 'ESLint', func: () => this.runESLint() },
      { name: 'Prettier', func: () => this.runPrettier() },
      { name: 'Stylelint', func: () => this.runStylelint() },
      { name: 'TypeScript', func: () => this.runTypeScript() },
      { name: 'Testing', func: () => this.runTesting() },
      { name: 'Bundle Analysis', func: () => this.runBundleAnalysis() },
    ];
    
    let allPassed = true;
    
    for (const check of checks) {
      try {
        if (!check.func()) {
          allPassed = false;
        }
      } catch (error) {
        this.log(`❌ ${check.name} failed with error: ${error.message}`, 'error');
        allPassed = false;
      }
    }
    
    // Auto-fix if requested
    if (autoFix && !allPassed) {
      this.autoFixIssues();
    }
    
    // Calculate overall score
    this.calculateScore();
    
    // Generate report
    this.generateReport();
    
    return allPassed;
  }

  async runSpecificCheck(checkName) {
    this.log(`🚀 Running specific check: ${checkName}`, 'start');
    
    const checkMethods = {
      eslint: () => this.runESLint(),
      prettier: () => this.runPrettier(),
      stylelint: () => this.runStylelint(),
      typescript: () => this.runTypeScript(),
      testing: () => this.runTesting(),
      bundle: () => this.runBundleAnalysis(),
    };
    
    if (checkName in checkMethods) {
      const success = checkMethods[checkName]();
      this.calculateScore();
      this.generateReport();
      return success;
    } else {
      this.log(`❌ Unknown check: ${checkName}`, 'error');
      return false;
    }
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const runner = new FrontendCodeQualityRunner();
  
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Usage: node run_code_quality.js [options]

Options:
  --auto-fix           Automatically fix formatting issues
  --check <name>       Run only specific check (eslint, prettier, stylelint, typescript, testing, bundle)
  --help, -h           Show this help message

Examples:
  node run_code_quality.js                    # Run all quality checks
  node run_code_quality.js --auto-fix         # Run checks and auto-fix issues
  node run_code_quality.js --check eslint     # Run only ESLint checks
  node run_code_quality.js --check prettier   # Run only Prettier checks
    `);
    process.exit(0);
  }
  
  const autoFix = args.includes('--auto-fix');
  const checkIndex = args.indexOf('--check');
  const specificCheck = checkIndex !== -1 ? args[checkIndex + 1] : null;
  
  try {
    if (specificCheck) {
      const success = await runner.runSpecificCheck(specificCheck);
      process.exit(success ? 0 : 1);
    } else {
      const success = await runner.runAllChecks(autoFix);
      process.exit(success ? 0 : 1);
    }
  } catch (error) {
    console.error('❌ Unexpected error:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = FrontendCodeQualityRunner;