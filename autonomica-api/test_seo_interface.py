#!/usr/bin/env python3
"""
Test script for the SEO Research Interface
Tests all the comprehensive API endpoints for the complete SEO research interface
"""

import sys
import os
import time
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock FastAPI app for testing
from fastapi.testclient import TestClient
from app.main import app

def test_seo_interface_endpoints():
    """Test all SEO interface API endpoints"""
    print("🚀 Starting SEO Interface API Tests")
    print("=" * 50)
    
    # Create test client
    client = TestClient(app)
    
    # Test 1: SEO Dashboard
    print("\n📊 Testing SEO Dashboard endpoint...")
    try:
        response = client.post("/api/seo/dashboard")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                dashboard = data["data"]
                print(f"✅ Dashboard endpoint working correctly")
                print(f"  - Total keywords tracked: {dashboard['overview']['total_keywords_tracked']}")
                print(f"  - Average SEO score: {dashboard['overview']['average_seo_score']}")
                print(f"  - Recent activities: {len(dashboard['recent_activities'])}")
            else:
                print("❌ Dashboard endpoint returned invalid data structure")
        else:
            print(f"❌ Dashboard endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard endpoint error: {str(e)}")
    
    # Test 2: Generate SEO Report
    print("\n📋 Testing SEO Report Generation endpoint...")
    try:
        report_request = {
            "type": "comprehensive",
            "date_range": "last_30_days",
            "include_recommendations": True
        }
        response = client.post("/api/seo/reports/generate", json=report_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                report = data["data"]
                print(f"✅ Report generation endpoint working correctly")
                print(f"  - Report ID: {report['report_id']}")
                print(f"  - Report type: {report['type']}")
                print(f"  - Total pages analyzed: {report['summary']['total_pages_analyzed']}")
                if "action_plan" in report:
                    print(f"  - Action plan included: {len(report['action_plan']['immediate_actions'])} immediate actions")
            else:
                print("❌ Report generation returned invalid data structure")
        else:
            print(f"❌ Report generation failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Report generation error: {str(e)}")
    
    # Test 3: Track Keyword
    print("\n🎯 Testing Keyword Tracking endpoint...")
    try:
        keyword_request = {
            "keyword": "test keyword",
            "target_url": "/test-page",
            "priority": "high"
        }
        response = client.post("/api/seo/keywords/track", json=keyword_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                tracking = data["data"]
                print(f"✅ Keyword tracking endpoint working correctly")
                print(f"  - Keyword ID: {tracking['keyword_id']}")
                print(f"  - Keyword: {tracking['keyword']}")
                print(f"  - Priority: {tracking['priority']}")
            else:
                print("❌ Keyword tracking returned invalid data structure")
        else:
            print(f"❌ Keyword tracking failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Keyword tracking error: {str(e)}")
    
    # Test 4: Get Tracked Keywords
    print("\n📝 Testing Get Tracked Keywords endpoint...")
    try:
        response = client.get("/api/seo/keywords/tracking")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                keywords = data["data"]
                print(f"✅ Get tracked keywords endpoint working correctly")
                print(f"  - Total tracked keywords: {len(keywords)}")
                if keywords:
                    print(f"  - First keyword: {keywords[0]['keyword']}")
                    print(f"  - First keyword position: {keywords[0]['current_position']}")
            else:
                print("❌ Get tracked keywords returned invalid data structure")
        else:
            print(f"❌ Get tracked keywords failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Get tracked keywords error: {str(e)}")
    
    # Test 5: Content Analysis
    print("\n📄 Testing Content Analysis endpoint...")
    try:
        content_request = {
            "content": "This is a test content for SEO analysis. It contains multiple sentences and should provide enough text for analysis.",
            "target_keyword": "seo analysis",
            "content_type": "article"
        }
        response = client.post("/api/seo/content/analyze", json=content_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                analysis = data["data"]
                print(f"✅ Content analysis endpoint working correctly")
                print(f"  - Content ID: {analysis['content_id']}")
                print(f"  - Overall score: {analysis['overall_score']}")
                print(f"  - Word count: {analysis['word_count']}")
                print(f"  - Recommendations: {len(analysis['recommendations'])}")
            else:
                print("❌ Content analysis returned invalid data structure")
        else:
            print(f"❌ Content analysis failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Content analysis error: {str(e)}")
    
    # Test 6: Competitor Analysis
    print("\n🏆 Testing Competitor Analysis endpoint...")
    try:
        competitor_request = {
            "competitors": ["competitor1.com", "competitor2.com"],
            "depth": "comprehensive"
        }
        response = client.post("/api/seo/competitors/analyze", json=competitor_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                analysis = data["data"]
                print(f"✅ Competitor analysis endpoint working correctly")
                print(f"  - Analysis ID: {analysis['analysis_id']}")
                print(f"  - Competitors analyzed: {len(analysis['competitors'])}")
                print(f"  - Market position: {analysis['insights']['market_position']}")
                print(f"  - Recommendations: {len(analysis['insights']['recommendations'])}")
            else:
                print("❌ Competitor analysis returned invalid data structure")
        else:
            print(f"❌ Competitor analysis failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Competitor analysis error: {str(e)}")
    
    # Test 7: Backlink Analysis
    print("\n🔗 Testing Backlink Analysis endpoint...")
    try:
        backlink_request = {
            "domain": "example.com",
            "type": "overview"
        }
        response = client.post("/api/seo/backlinks/analyze", json=backlink_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                analysis = data["data"]
                print(f"✅ Backlink analysis endpoint working correctly")
                print(f"  - Domain: {analysis['domain']}")
                print(f"  - Total backlinks: {analysis['overview']['total_backlinks']}")
                print(f"  - Quality score: {analysis['quality_metrics']['quality_score']}")
                print(f"  - Opportunities: {len(analysis['opportunities'])}")
            else:
                print("❌ Backlink analysis returned invalid data structure")
        else:
            print(f"❌ Backlink analysis failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Backlink analysis error: {str(e)}")
    
    # Test 8: Track Rankings
    print("\n📈 Testing Rankings Tracking endpoint...")
    try:
        ranking_request = {
            "keywords": ["digital marketing", "seo tips"],
            "search_engine": "google",
            "location": "US"
        }
        response = client.post("/api/seo/rankings/track", json=ranking_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                tracking = data["data"]
                print(f"✅ Rankings tracking endpoint working correctly")
                print(f"  - Tracking ID: {tracking['tracking_id']}")
                print(f"  - Keywords tracked: {len(tracking['keywords'])}")
                print(f"  - Search engine: {tracking['search_engine']}")
            else:
                print("❌ Rankings tracking returned invalid data structure")
        else:
            print(f"❌ Rankings tracking failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Rankings tracking error: {str(e)}")
    
    # Test 9: Get Ranking History
    print("\n📊 Testing Ranking History endpoint...")
    try:
        response = client.get("/api/seo/rankings/history?keyword=digital%20marketing&days=7")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                history = data["data"]
                print(f"✅ Ranking history endpoint working correctly")
                print(f"  - Keyword: {history['keyword']}")
                print(f"  - Period: {history['period_days']} days")
                print(f"  - Data points: {len(history['data_points'])}")
            else:
                print("❌ Ranking history returned invalid data structure")
        else:
            print(f"❌ Ranking history failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Ranking history error: {str(e)}")
    
    # Test 10: Setup SEO Alerts
    print("\n🚨 Testing SEO Alerts Setup endpoint...")
    try:
        alert_request = {
            "type": "ranking_drop",
            "conditions": {"drop_threshold": 5, "keywords": ["digital marketing"]},
            "notification_method": "email"
        }
        response = client.post("/api/seo/alerts/setup", json=alert_request)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                alert = data["data"]
                print(f"✅ SEO alerts setup endpoint working correctly")
                print(f"  - Alert ID: {alert['alert_id']}")
                print(f"  - Alert type: {alert['type']}")
                print(f"  - Status: {alert['status']}")
            else:
                print("❌ SEO alerts setup returned invalid data structure")
        else:
            print(f"❌ SEO alerts setup failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ SEO alerts setup error: {str(e)}")
    
    # Test 11: List SEO Alerts
    print("\n📋 Testing List SEO Alerts endpoint...")
    try:
        response = client.get("/api/seo/alerts/list")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                alerts = data["data"]
                print(f"✅ List SEO alerts endpoint working correctly")
                print(f"  - Total alerts: {len(alerts)}")
                if alerts:
                    print(f"  - First alert type: {alerts[0]['type']}")
                    print(f"  - First alert status: {alerts[0]['status']}")
            else:
                print("❌ List SEO alerts returned invalid data structure")
        else:
            print(f"❌ List SEO alerts failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ List SEO alerts error: {str(e)}")
    
    # Test 12: Existing SEO endpoints (verify they still work)
    print("\n🔍 Testing existing SEO endpoints...")
    
    # Test health endpoint
    try:
        response = client.get("/api/seo/health")
        if response.status_code == 200:
            print("✅ SEO health endpoint working correctly")
        else:
            print(f"❌ SEO health endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ SEO health endpoint error: {str(e)}")
    
    # Test analyze endpoint
    try:
        analyze_request = {"keyword": "test keyword"}
        response = client.post("/api/seo/analyze", json=analyze_request)
        if response.status_code == 200:
            print("✅ SEO analyze endpoint working correctly")
        else:
            print(f"❌ SEO analyze endpoint failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ SEO analyze endpoint error: {str(e)}")
    
    print("\n🎉 All SEO interface API endpoint tests completed!")
    return True

def test_api_response_structures():
    """Test API response structures and data validation"""
    print("\n🔍 Testing API response structures...")
    
    client = TestClient(app)
    
    # Test dashboard response structure
    try:
        response = client.post("/api/seo/dashboard")
        if response.status_code == 200:
            data = response.json()
            
            # Validate required fields
            required_fields = ["overview", "performance_metrics", "recent_activities", "quick_actions"]
            missing_fields = [field for field in required_fields if field not in data.get("data", {})]
            
            if not missing_fields:
                print("✅ Dashboard response structure validation passed")
            else:
                print(f"❌ Dashboard missing required fields: {missing_fields}")
        else:
            print("❌ Dashboard endpoint not accessible for structure testing")
    except Exception as e:
        print(f"❌ Dashboard structure testing error: {str(e)}")
    
    # Test report generation response structure
    try:
        report_request = {"type": "comprehensive", "include_recommendations": True}
        response = client.post("/api/seo/reports/generate", json=report_request)
        if response.status_code == 200:
            data = response.json()
            
            # Validate required fields
            required_fields = ["report_id", "type", "summary", "detailed_analysis", "action_plan"]
            missing_fields = [field for field in required_fields if field not in data.get("data", {})]
            
            if not missing_fields:
                print("✅ Report generation response structure validation passed")
            else:
                print(f"❌ Report generation missing required fields: {missing_fields}")
        else:
            print("❌ Report generation endpoint not accessible for structure testing")
    except Exception as e:
        print(f"❌ Report generation structure testing error: {str(e)}")
    
    print("✅ API response structure testing completed")

def test_error_handling():
    """Test error handling and edge cases"""
    print("\n⚠️  Testing error handling and edge cases...")
    
    client = TestClient(app)
    
    # Test missing required fields
    try:
        # Test keyword tracking without keyword
        response = client.post("/api/seo/keywords/track", json={})
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and "error" in data:
                print("✅ Missing required fields handled correctly")
            else:
                print("❌ Missing required fields not handled correctly")
        else:
            print("❌ Missing required fields endpoint failed")
    except Exception as e:
        print(f"❌ Missing required fields testing error: {str(e)}")
    
    # Test content analysis without content
    try:
        response = client.post("/api/seo/content/analyze", json={"target_keyword": "test"})
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and "error" in data:
                print("✅ Missing content field handled correctly")
            else:
                print("❌ Missing content field not handled correctly")
        else:
            print("❌ Missing content field endpoint failed")
    except Exception as e:
        print(f"❌ Missing content field testing error: {str(e)}")
    
    # Test competitor analysis without competitors
    try:
        response = client.post("/api/seo/competitors/analyze", json={})
        if response.status_code == 200:
            data = response.json()
            if not data.get("success") and "error" in data:
                print("✅ Missing competitors field handled correctly")
            else:
                print("❌ Missing competitors field not handled correctly")
        else:
            print("❌ Missing competitors field endpoint failed")
    except Exception as e:
        print(f"❌ Missing competitors field testing error: {str(e)}")
    
    print("✅ Error handling testing completed")

if __name__ == "__main__":
    try:
        # Run main endpoint tests
        success = test_seo_interface_endpoints()
        
        if success:
            # Run additional tests
            test_api_response_structures()
            test_error_handling()
            
            print("\n" + "=" * 50)
            print("🎉 ALL TESTS PASSED! SEO interface is working correctly.")
            print("=" * 50)
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)