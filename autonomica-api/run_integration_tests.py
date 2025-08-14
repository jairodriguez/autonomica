#!/usr/bin/env python3
"""
Integration Test Runner for Autonomica API

This script runs integration tests with proper environment setup,
database initialization, and cleanup.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import time
import signal
from pathlib import Path

def setup_test_environment():
    """Setup test environment variables and temporary directories."""
    print("🔧 Setting up test environment...")
    
    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="autonomica_test_")
    os.environ["TEST_DIR"] = test_dir
    
    # Set test environment variables
    test_env = {
        "TESTING": "true",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "DEBUG",
        "REDIS_URL": "redis://localhost:6379/1",
        "DATABASE_URL": f"sqlite:///{test_dir}/test.db",
        "OPENAI_API_KEY": "test-integration-key",
        "CLERK_SECRET_KEY": "test-integration-key",
        "AI_PROVIDER": "mock",
        "PYTHONPATH": str(Path(__file__).parent)
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
        print(f"  {key}={value}")
    
    return test_dir

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    try:
        import pytest
        print(f"  ✅ pytest {pytest.__version__}")
    except ImportError:
        print("  ❌ pytest not found")
        return False
    
    try:
        import redis
        print(f"  ✅ redis {redis.__version__}")
    except ImportError:
        print("  ❌ redis not found")
        return False
    
    try:
        import fastapi
        print(f"  ✅ fastapi {fastapi.__version__}")
    except ImportError:
        print("  ❌ fastapi not found")
        return False
    
    return True

def start_redis_server():
    """Start Redis server for testing if not already running."""
    print("🚀 Starting Redis server...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=1)
        r.ping()
        print("  ✅ Redis server already running")
        return True
    except:
        print("  ⚠️  Redis server not running")
        print("  💡 Please start Redis server manually or use Docker:")
        print("     docker run -d -p 6379:6379 redis:7-alpine")
        return False

def run_integration_tests():
    """Run the integration test suite."""
    print("🧪 Running integration tests...")
    
    # Test configuration
    test_args = [
        "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov_integration",
        "--cov-report=xml:coverage_integration.xml",
        "--durations=10",
        "-m", "integration"
    ]
    
    print(f"  Running: {' '.join(test_args)}")
    
    try:
        result = subprocess.run(test_args, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"  ❌ Error running tests: {e}")
        return False

def run_worker_integration_tests():
    """Run worker pod integration tests."""
    print("🏭 Running worker integration tests...")
    
    worker_test_dir = Path(__file__).parent.parent / "autonomica-worker" / "tests" / "integration"
    
    if not worker_test_dir.exists():
        print("  ⚠️  Worker test directory not found")
        return True
    
    test_args = [
        "pytest",
        str(worker_test_dir),
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov_worker_integration",
        "--cov-report=xml:coverage_worker_integration.xml",
        "--durations=10",
        "-m", "integration"
    ]
    
    print(f"  Running: {' '.join(test_args)}")
    
    try:
        result = subprocess.run(test_args, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"  ❌ Error running worker tests: {e}")
        return False

def cleanup_test_environment(test_dir):
    """Clean up test environment and temporary files."""
    print("🧹 Cleaning up test environment...")
    
    try:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"  ✅ Removed test directory: {test_dir}")
    except Exception as e:
        print(f"  ⚠️  Error cleaning up test directory: {e}")
    
    # Clean up environment variables
    test_env_vars = [
        "TESTING", "ENVIRONMENT", "LOG_LEVEL", "REDIS_URL",
        "DATABASE_URL", "OPENAI_API_KEY", "CLERK_SECRET_KEY",
        "AI_PROVIDER", "TEST_DIR"
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]

def generate_test_report():
    """Generate a summary test report."""
    print("\n📊 Integration Test Report")
    print("=" * 50)
    
    # Check for coverage reports
    coverage_files = [
        "htmlcov_integration",
        "coverage_integration.xml",
        "htmlcov_worker_integration",
        "coverage_worker_integration.xml"
    ]
    
    for file_path in coverage_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (not found)")
    
    print("\n📁 Test Results Location:")
    print("  - HTML Coverage: htmlcov_integration/")
    print("  - XML Coverage: coverage_integration.xml")
    print("  - Worker Coverage: htmlcov_worker_integration/")

def main():
    """Main integration test runner."""
    print("🚀 Autonomica Integration Test Runner")
    print("=" * 50)
    
    test_dir = None
    
    try:
        # Check dependencies
        if not check_dependencies():
            print("❌ Missing required dependencies")
            sys.exit(1)
        
        # Setup test environment
        test_dir = setup_test_environment()
        
        # Check Redis server
        if not start_redis_server():
            print("⚠️  Continuing without Redis server...")
        
        # Run API integration tests
        api_success = run_integration_tests()
        
        # Run worker integration tests
        worker_success = run_worker_integration_tests()
        
        # Generate report
        generate_test_report()
        
        # Determine overall success
        if api_success and worker_success:
            print("\n🎉 All integration tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some integration tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Integration tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        if test_dir:
            cleanup_test_environment(test_dir)

if __name__ == "__main__":
    main()