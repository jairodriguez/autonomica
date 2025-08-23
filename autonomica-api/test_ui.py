#!/usr/bin/env python3
"""
Test script for the Autonomica CMS User Interface
This script tests the frontend components without needing the full FastAPI server
"""

import os
import sys
import json
from pathlib import Path

def test_static_files():
    """Test that static files exist and are accessible"""
    print("Testing static files...")
    
    static_dir = Path("app/static")
    if not static_dir.exists():
        print("❌ Static directory not found")
        return False
    
    # Check HTML file
    index_html = static_dir / "index.html"
    if not index_html.exists():
        print("❌ index.html not found")
        return False
    
    # Check JavaScript file
    js_dir = static_dir / "js"
    app_js = js_dir / "app.js"
    if not app_js.exists():
        print("❌ app.js not found")
        return False
    
    print("✅ Static files found")
    return True

def test_html_structure():
    """Test HTML file structure and content"""
    print("\nTesting HTML structure...")
    
    index_html = Path("app/static/index.html")
    if not index_html.exists():
        print("❌ index.html not found")
        return False
    
    try:
        with open(index_html, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for essential elements
        required_elements = [
            '<title>Autonomica Content Management System</title>',
            'id="sidebar"',
            'id="main-content"',
            'id="dashboard"',
            'id="content-generation"',
            'id="content-repurpose"',
            'id="content-management"',
            'id="workflow"',
            'id="analytics"',
            'src="js/app.js"'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing HTML elements: {missing_elements}")
            return False
        
        print("✅ HTML structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error reading HTML file: {e}")
        return False

def test_javascript_structure():
    """Test JavaScript file structure and content"""
    print("\nTesting JavaScript structure...")
    
    app_js = Path("app/static/js/app.js")
    if not app_js.exists():
        print("❌ app.js not found")
        return False
    
    try:
        with open(app_js, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for essential JavaScript components
        required_components = [
            'class AutonomicaCMS',
            'constructor()',
            'init()',
            'setupEventListeners()',
            'navigateToPage(',
            'handleContentGeneration()',
            'handleContentRepurpose()',
            'loadDashboardData()',
            'loadContentManagementData()',
            'loadWorkflowData()',
            'loadAnalyticsData()'
        ]
        
        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ Missing JavaScript components: {missing_components}")
            return False
        
        print("✅ JavaScript structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error reading JavaScript file: {e}")
        return False

def test_api_routes():
    """Test API routes file structure"""
    print("\nTesting API routes...")
    
    routes_file = Path("app/api/routes/content_management.py")
    if not routes_file.exists():
        print("❌ API routes file not found")
        return False
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for essential API endpoints (more flexible matching)
        required_endpoints = [
            '@router.get("/"',  # Root endpoint
            '@router.post("/generate"',  # Content generation
            '@router.post("/repurpose"',  # Content repurposing
            '@router.post("/{content_id}/langchain-repurpose"',  # LangChain repurposing
            '@router.put("/{content_id}/update"',  # Content updates
            '@router.post("/{content_id}/submit-review"',  # Submit for review
            '@router.post("/{content_id}/review"',  # Review content
            '@router.post("/{content_id}/publish"',  # Publish content
            '@router.get("/{content_id}"',  # Get content
            '@router.get("/{content_id}/versions"',  # Get versions
            '@router.post("/{content_id}/rollback/{version_id}"',  # Rollback
            '@router.post("/{content_id}/archive"',  # Archive content
            '@router.post("/search"',  # Search content
            '@router.get("/dashboard/stats"',  # Dashboard stats
            '@router.get("/health"'  # Health check
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"❌ Missing API endpoints: {missing_endpoints}")
            return False
        
        print("✅ API routes are correct")
        return True
        
    except Exception as e:
        print(f"❌ Error reading API routes file: {e}")
        return False

def test_directory_structure():
    """Test overall directory structure"""
    print("\nTesting directory structure...")
    
    required_dirs = [
        "app/static",
        "app/static/js",
        "app/api/routes"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    
    print("✅ Directory structure is correct")
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Autonomica CMS User Interface\n")
    
    tests = [
        test_directory_structure,
        test_static_files,
        test_html_structure,
        test_javascript_structure,
        test_api_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The user interface is ready.")
        print("\nTo run the interface:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Open http://localhost:8000/api/content/ in your browser")
        print("3. The interface should load with dashboard, content generation, and workflow management")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
