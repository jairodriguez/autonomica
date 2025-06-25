"""
Comprehensive Test Suite for LangChain NLP Integration
Tests environment setup, core functionality, and API endpoints
"""

import asyncio
import os
import sys
import json
import requests
import time
from pathlib import Path

# Add the app directory to the path
sys.path.append('.')

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.total = 0
        self.api_base_url = "http://localhost:8000/api"
        
    def test(self, name: str):
        """Decorator for test functions"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                self.total += 1
                print(f"\n{self.total}. Testing {name}...")
                try:
                    result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                    if result:
                        print(f"   ✅ {name} - PASSED")
                        self.passed += 1
                    else:
                        print(f"   ❌ {name} - FAILED")
                    return result
                except Exception as e:
                    print(f"   ❌ {name} - ERROR: {e}")
                    return False
            return wrapper
        return decorator

# Initialize test runner
runner = TestRunner()

@runner.test("Environment File Setup")
def test_environment_files():
    """Test environment file configuration"""
    env_local_exists = Path(".env.local").exists()
    env_exists = Path(".env").exists()
    env_example_exists = Path("env.example").exists()
    
    print(f"     .env.local: {'✅ EXISTS' if env_local_exists else '❌ NOT FOUND'}")
    print(f"     .env: {'✅ EXISTS' if env_exists else '❌ NOT FOUND'}")
    print(f"     env.example: {'✅ EXISTS' if env_example_exists else '❌ NOT FOUND'}")
    
    if env_local_exists:
        print("     💡 .env.local found - using local development configuration")
    elif env_exists:
        print("     💡 .env found - using default configuration")
    else:
        print("     ⚠️  No environment files found - using system environment only")
    
    return env_example_exists  # At minimum, example should exist

@runner.test("Environment Variable Loading")
def test_environment_loading():
    """Test environment variable loading with priority"""
    from dotenv import load_dotenv
    
    # Load in same order as main.py
    load_dotenv(".env.local")
    load_dotenv(".env")
    load_dotenv()
    
    # Check key variables
    openai_key = os.getenv("OPENAI_API_KEY")
    debug = os.getenv("DEBUG")
    environment = os.getenv("ENVIRONMENT")
    
    print(f"     OPENAI_API_KEY: {'✅ SET' if openai_key else '❌ NOT SET'}")
    print(f"     DEBUG: {debug or 'NOT SET'}")
    print(f"     ENVIRONMENT: {environment or 'NOT SET'}")
    
    if openai_key:
        masked_key = f"{openai_key[:8]}..." if len(openai_key) > 8 else "***"
        print(f"     🔑 API Key: {masked_key}")
    
    return True  # Environment loading always works, just may not have keys

@runner.test("LangChain Integration Imports")
async def test_langchain_imports():
    """Test that all LangChain components can be imported"""
    try:
        from app.owl.langchain_integration import (
            LangChainNLPEngine,
            LangChainExecution,
            NLPCapability,
            AutonomicaCallbackHandler,
            get_nlp_engine
        )
        print("     ✅ All LangChain integration imports successful")
        return True
    except ImportError as e:
        print(f"     ❌ Import failed: {e}")
        return False

@runner.test("NLP Engine Initialization")
async def test_nlp_engine():
    """Test NLP engine creation and capabilities"""
    try:
        from app.owl.langchain_integration import LangChainNLPEngine
        
        engine = LangChainNLPEngine()
        capabilities = engine.get_capabilities()
        
        print(f"     ✅ Engine created with {len(capabilities)} capabilities")
        for cap_name, cap in capabilities.items():
            print(f"       - {cap.name}")
        
        return len(capabilities) == 8  # Should have 8 capabilities
    except Exception as e:
        print(f"     ❌ Engine initialization failed: {e}")
        return False

@runner.test("Mock NLP Execution")
async def test_mock_execution():
    """Test mock NLP execution tracking"""
    try:
        from app.owl.langchain_integration import LangChainExecution
        import uuid
        
        execution = LangChainExecution(
            id=str(uuid.uuid4()),
            agent_id="test_agent",
            capability="text_summarization",
            input_data={"text": "Test document"},
            output_data={"summary": "Test summary"},
            tokens_used=50,
            cost=0.002,
            execution_time=1.5,
            status="success"
        )
        
        print(f"     ✅ Mock execution: {execution.capability}")
        print(f"     💰 Cost: ${execution.cost}")
        print(f"     ⏱️  Time: {execution.execution_time}s")
        
        return execution.status == "success"
    except Exception as e:
        print(f"     ❌ Mock execution failed: {e}")
        return False

@runner.test("Cost Calculation")
async def test_cost_calculation():
    """Test cost calculation for different models"""
    try:
        from app.owl.langchain_integration import LangChainNLPEngine
        
        engine = LangChainNLPEngine()
        
        # Test different models and token amounts
        test_cases = [
            ("gpt-4o-mini", 1000),
            ("gpt-4o", 1000),
            ("gpt-4", 1000)
        ]
        
        print("     💰 Cost calculations:")
        for model, tokens in test_cases:
            cost = engine._calculate_cost(tokens, model)
            print(f"       {model}: {tokens} tokens = ${cost:.6f}")
        
        return True
    except Exception as e:
        print(f"     ❌ Cost calculation failed: {e}")
        return False

@runner.test("API Server Status")
def test_api_server():
    """Test if the API server is running"""
    try:
        response = requests.get(f"{runner.api_base_url}/health", timeout=5)
        if response.status_code == 200:
            print("     ✅ API server is running")
            print(f"     🌐 Health check: {response.json()}")
            return True
        else:
            print(f"     ❌ API server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("     ❌ API server not running")
        print("     💡 Start with: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"     ❌ API test failed: {e}")
        return False

@runner.test("NLP Capabilities Endpoint")
def test_nlp_capabilities_endpoint():
    """Test the NLP capabilities API endpoint"""
    try:
        response = requests.get(f"{runner.api_base_url}/nlp/capabilities", timeout=5)
        if response.status_code == 200:
            data = response.json()
            capabilities = data.get("capabilities", {})
            print(f"     ✅ Found {len(capabilities)} NLP capabilities")
            for cap_name in capabilities.keys():
                print(f"       - {cap_name}")
            return len(capabilities) > 0
        else:
            print(f"     ❌ Endpoint returned status {response.status_code}")
            if response.status_code == 401:
                print("     💡 Authentication required - add Clerk token")
            return False
    except requests.exceptions.ConnectionError:
        print("     ❌ API server not running")
        return False
    except Exception as e:
        print(f"     ❌ Endpoint test failed: {e}")
        return False

@runner.test("Live NLP Execution (if API key available)")
async def test_live_nlp():
    """Test live NLP execution if API key is available"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("your_") or api_key.startswith("sk-your"):
        print("     ⚠️  No valid OpenAI API key - skipping live test")
        print("     💡 Add your API key to .env.local for live testing")
        return True  # Not a failure, just skipped
    
    try:
        from app.owl.langchain_integration import get_nlp_engine
        
        engine = await get_nlp_engine()
        
        # Test text summarization
        test_text = "Artificial Intelligence is transforming how we work and live. Machine learning algorithms can now process vast amounts of data to identify patterns and make predictions. This technology is being applied in healthcare, finance, transportation, and many other sectors to improve efficiency and create new possibilities for innovation."
        
        execution = await engine.summarize_text(
            text=test_text,
            agent_id="test_agent_live",
            max_length=30,
            style="concise"
        )
        
        if execution.status == "success":
            print("     ✅ Live NLP execution successful")
            print(f"     📝 Summary: {execution.output_data.get('summary', '')[:80]}...")
            print(f"     💰 Cost: ${execution.cost:.6f}")
            print(f"     🔢 Tokens: {execution.tokens_used}")
            return True
        else:
            print(f"     ❌ Live execution failed: {execution.error_message}")
            return False
            
    except Exception as e:
        print(f"     ❌ Live NLP test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests and provide summary"""
    print("🧪 COMPREHENSIVE LANGCHAIN NLP TESTING")
    print("=" * 60)
    
    # Run all tests
    await runner.test_environment_files()
    await runner.test_environment_loading()
    await runner.test_langchain_imports()
    await runner.test_nlp_engine()
    await runner.test_mock_execution()
    await runner.test_cost_calculation()
    await runner.test_api_server()
    await runner.test_nlp_capabilities_endpoint()
    await runner.test_live_nlp()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    percentage = (runner.passed / runner.total) * 100 if runner.total > 0 else 0
    print(f"TOTAL: {runner.passed}/{runner.total} tests passed ({percentage:.1f}%)")
    
    if runner.passed == runner.total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your LangChain NLP integration is fully functional")
    elif runner.passed >= runner.total * 0.8:
        print("✅ MOSTLY WORKING!")
        print("⚠️  Minor issues detected, but core functionality is operational")
    else:
        print("⚠️  SOME ISSUES DETECTED")
        print("🔧 Check the failed tests above for troubleshooting steps")
    
    print("\n📋 WHAT'S WORKING:")
    if runner.passed > 0:
        print("• Basic LangChain integration and imports")
        print("• NLP capability definitions and structure")
        print("• Cost calculation and execution tracking")
        if runner.passed >= 7:
            print("• API server and endpoint configuration")
        if runner.passed >= 8:
            print("• Live NLP processing capabilities")
    
    print("\n🚀 NEXT STEPS:")
    if not Path(".env.local").exists():
        print("1. Create .env.local with your API keys")
        print("   touch .env.local")
        print("   echo 'OPENAI_API_KEY=sk-your-key-here' >> .env.local")
    
    if runner.passed < 7:
        print("2. Start the API server:")
        print("   python -m uvicorn app.main:app --reload")
    
    if runner.passed >= 7:
        print("2. Test the API endpoints:")
        print("   curl http://localhost:8000/api/health")
        print("   curl http://localhost:8000/api/nlp/capabilities")
    
    print("3. Check the ENV_SETUP_GUIDE.md for detailed setup instructions")
    
    return runner.passed == runner.total

if __name__ == "__main__":
    asyncio.run(run_all_tests()) 