"""
API Endpoint Testing Script for LangChain NLP Integration
Tests all NLP endpoints with sample data
"""

import requests
import json
import time
from typing import Dict, Any

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            # Add Clerk auth token here if you have one:
            # "Authorization": "Bearer your_clerk_token_here"
        }
        
    def test_endpoint(self, method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[str, Any]:
        """Test a single endpoint and return results"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "response_time": response.elapsed.total_seconds()
            }
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection failed - is the server running?"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    """Run all API endpoint tests"""
    tester = APITester()
    
    print("🧪 TESTING AUTONOMICA API ENDPOINTS")
    print("=" * 50)
    
    # Test cases
    tests = [
        {
            "name": "Health Check",
            "method": "GET",
            "endpoint": "/health",
            "description": "Basic server health check"
        },
        {
            "name": "NLP Capabilities",
            "method": "GET", 
            "endpoint": "/nlp/capabilities",
            "description": "Get available NLP capabilities"
        },
        {
            "name": "Text Summarization",
            "method": "POST",
            "endpoint": "/nlp/summarize",
            "data": {
                "text": "Artificial Intelligence is revolutionizing industries across the globe. Machine learning algorithms are becoming more sophisticated, enabling computers to perform tasks that were once thought to be exclusively human. From healthcare to finance, AI is improving efficiency, accuracy, and decision-making processes. However, this rapid advancement also raises important questions about ethics, job displacement, and the need for proper regulation.",
                "max_length": 50,
                "style": "concise"
            },
            "description": "Test text summarization capability"
        },
        {
            "name": "Sentiment Analysis",
            "method": "POST",
            "endpoint": "/nlp/sentiment",
            "data": {
                "text": "I absolutely love this new AI system! It's incredibly helpful and makes my work so much easier. The interface is intuitive and the results are amazing.",
                "detailed": True
            },
            "description": "Test sentiment analysis capability"
        },
        {
            "name": "Language Translation",
            "method": "POST",
            "endpoint": "/nlp/translate",
            "data": {
                "text": "Hello, how are you today?",
                "target_language": "Spanish",
                "source_language": "English"
            },
            "description": "Test language translation capability"
        },
        {
            "name": "Named Entity Recognition",
            "method": "POST",
            "endpoint": "/nlp/entities",
            "data": {
                "text": "Apple Inc. was founded by Steve Jobs in Cupertino, California. The company is now led by CEO Tim Cook and has offices in New York, London, and Tokyo.",
                "entity_types": ["PERSON", "ORG", "GPE"]
            },
            "description": "Test named entity recognition"
        },
        {
            "name": "Question Answering",
            "method": "POST",
            "endpoint": "/nlp/qa",
            "data": {
                "question": "What is the capital of France?",
                "context": "France is a country in Western Europe. Its capital and largest city is Paris, which is located in the north-central part of the country.",
                "confidence_threshold": 0.7
            },
            "description": "Test question answering capability"
        },
        {
            "name": "Document Analysis",
            "method": "POST",
            "endpoint": "/nlp/analyze-document",
            "data": {
                "content": "Executive Summary: This quarterly report shows significant growth in our AI division. Revenue increased by 35% compared to last quarter. Key achievements include launching three new products and expanding our team by 20 engineers. Challenges include increased competition and supply chain issues.",
                "analysis_types": ["summary", "key_points", "sentiment"],
                "include_metadata": True
            },
            "description": "Test document analysis capability"
        },
        {
            "name": "Text Classification",
            "method": "POST",
            "endpoint": "/nlp/classify",
            "data": {
                "text": "I need to cancel my subscription and get a refund. This service is not working as advertised and I'm very disappointed.",
                "categories": ["support_request", "complaint", "compliment", "inquiry"],
                "confidence_threshold": 0.6
            },
            "description": "Test text classification capability"
        },
        {
            "name": "NLP Analytics",
            "method": "GET",
            "endpoint": "/nlp/analytics",
            "description": "Get NLP usage analytics"
        }
    ]
    
    # Run tests
    passed = 0
    total = len(tests)
    
    for i, test in enumerate(tests, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   📝 {test['description']}")
        
        result = tester.test_endpoint(
            method=test['method'],
            endpoint=test['endpoint'],
            data=test.get('data')
        )
        
        if result['success']:
            print(f"   ✅ PASSED ({result['status_code']}) - {result['response_time']:.2f}s")
            passed += 1
            
            # Show sample response for interesting endpoints
            if test['endpoint'] in ['/health', '/nlp/capabilities']:
                print(f"   📄 Response: {json.dumps(result['data'], indent=2)[:200]}...")
            elif test['endpoint'].startswith('/nlp/') and 'data' in result:
                data = result['data']
                if isinstance(data, dict):
                    if 'result' in data:
                        print(f"   📊 Result: {str(data['result'])[:100]}...")
                    elif 'summary' in data:
                        print(f"   📊 Summary: {data['summary'][:100]}...")
                    elif 'sentiment' in data:
                        print(f"   📊 Sentiment: {data['sentiment']}")
        else:
            print(f"   ❌ FAILED - {result.get('error', 'Unknown error')}")
            if 'status_code' in result:
                print(f"   🔍 Status: {result['status_code']}")
                if result['status_code'] == 401:
                    print("   💡 This might be due to missing Clerk authentication")
                elif result['status_code'] == 422:
                    print("   💡 This might be due to validation errors in request data")
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 API TEST RESULTS")
    print("=" * 50)
    
    percentage = (passed / total) * 100
    print(f"PASSED: {passed}/{total} ({percentage:.1f}%)")
    
    if passed == total:
        print("🎉 ALL ENDPOINTS WORKING!")
    elif passed >= total * 0.8:
        print("✅ MOST ENDPOINTS WORKING!")
    else:
        print("⚠️  SOME ENDPOINTS NEED ATTENTION")
    
    print("\n🔧 TROUBLESHOOTING TIPS:")
    if passed == 0:
        print("• Make sure the API server is running:")
        print("  python -m uvicorn app.main:app --reload")
    
    print("• For authentication errors (401):")
    print("  - Add Clerk token to headers in this script")
    print("  - Or test without auth by modifying the middleware")
    
    print("• For validation errors (422):")
    print("  - Check the request data format")
    print("  - Verify required fields are included")
    
    print("• For OpenAI API errors:")
    print("  - Ensure OPENAI_API_KEY is set in .env.local")
    print("  - Check API key has sufficient credits")
    
    return passed == total

if __name__ == "__main__":
    main() 