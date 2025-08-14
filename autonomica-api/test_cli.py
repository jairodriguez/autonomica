#!/usr/bin/env python3
"""
Test script for the Content CLI
"""

import sys
import os
import tempfile
import subprocess

# Add the app/ai directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'ai'))

def test_cli_help():
    """Test CLI help command"""
    print("Testing CLI help...")
    
    try:
        result = subprocess.run(
            ['python3', 'app/ai/content_cli.py', '--help'],
            capture_output=True,
            text=True,
            cwd='/workspace/autonomica-api'
        )
        
        if result.returncode == 0:
            print("✓ CLI help command works")
            return True
        else:
            print(f"✗ CLI help command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing CLI help: {e}")
        return False

def test_list_types():
    """Test listing content types"""
    print("\nTesting list types command...")
    
    try:
        result = subprocess.run(
            ['python3', 'app/ai/content_cli.py', 'types'],
            capture_output=True,
            text=True,
            cwd='/workspace/autonomica-api'
        )
        
        if result.returncode == 0:
            print("✓ List types command works")
            # Check if output contains expected content
            if "blog_post" in result.stdout and "tweet" in result.stdout:
                print("✓ Output contains expected content types")
                return True
            else:
                print("✗ Output missing expected content types")
                return False
        else:
            print(f"✗ List types command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing list types: {e}")
        return False

def test_list_strategies():
    """Test listing repurposing strategies"""
    print("\nTesting list strategies command...")
    
    try:
        result = subprocess.run(
            ['python3', 'app/ai/content_cli.py', 'strategies'],
            capture_output=True,
            text=True,
            cwd='/workspace/autonomica-api'
        )
        
        if result.returncode == 0:
            print("✓ List strategies command works")
            # Check if output contains expected content
            if "blog_to_tweet" in result.stdout:
                print("✓ Output contains expected strategies")
                return True
            else:
                print("✗ Output missing expected strategies")
                return False
        else:
            print(f"✗ List strategies command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing list strategies: {e}")
        return False

def test_generate_content():
    """Test content generation"""
    print("\nTesting content generation...")
    
    try:
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            output_file = f.name
        
        result = subprocess.run([
            'python3', 'app/ai/content_cli.py', 'generate',
            '--type', 'blog_post',
            '--prompt', 'Write a short paragraph about AI content generation',
            '--format', 'plain_text',
            '--output', output_file
        ], capture_output=True, text=True, cwd='/workspace/autonomica-api')
        
        if result.returncode == 0:
            print("✓ Content generation command works")
            
            # Check if output file was created and contains content
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    content = f.read()
                if content.strip():
                    print("✓ Output file created with content")
                    os.unlink(output_file)  # Clean up
                    return True
                else:
                    print("✗ Output file is empty")
                    os.unlink(output_file)  # Clean up
                    return False
            else:
                print("✗ Output file not created")
                return False
        else:
            print(f"✗ Content generation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing content generation: {e}")
        return False

def test_quality_check():
    """Test quality checking"""
    print("\nTesting quality check...")
    
    try:
        # Create a temporary file with test content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test blog post about AI content generation. It contains several sentences to test the quality checker.")
            test_file = f.name
        
        result = subprocess.run([
            'python3', 'app/ai/content_cli.py', 'quality',
            '--content', test_file,
            '--type', 'blog_post'
        ], capture_output=True, text=True, cwd='/workspace/autonomica-api')
        
        # Clean up test file
        os.unlink(test_file)
        
        if result.returncode == 0:
            print("✓ Quality check command works")
            # Check if output contains quality information
            if "Quality Report" in result.stdout and "Overall Score" in result.stdout:
                print("✓ Output contains quality report")
                return True
            else:
                print("✗ Output missing quality report")
                return False
        else:
            print(f"✗ Quality check failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing quality check: {e}")
        return False

def test_version_management():
    """Test version management"""
    print("\nTesting version management...")
    
    try:
        # Create a temporary file with test content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test content for version management.")
            test_file = f.name
        
        # Test creating content
        result = subprocess.run([
            'python3', 'app/ai/content_cli.py', 'version',
            '--action', 'create',
            '--content', test_file,
            '--type', 'blog_post'
        ], capture_output=True, text=True, cwd='/workspace/autonomica-api')
        
        # Clean up test file
        os.unlink(test_file)
        
        if result.returncode == 0:
            print("✓ Version create command works")
            # Check if output contains content ID
            if "Created new content:" in result.stdout:
                print("✓ Content creation successful")
                return True
            else:
                print("✗ Content creation output unexpected")
                return False
        else:
            print(f"✗ Version create failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing version management: {e}")
        return False

def main():
    """Run all CLI tests"""
    print("🧪 Testing Content CLI\n")
    
    tests = [
        test_cli_help,
        test_list_types,
        test_list_strategies,
        test_generate_content,
        test_quality_check,
        test_version_management
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All CLI tests passed! The user interface is working correctly.")
        return 0
    else:
        print("❌ Some CLI tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())