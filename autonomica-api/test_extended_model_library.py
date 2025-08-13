#!/usr/bin/env python3
"""
Test Script for Ollama Extended Model Library System

This script tests the comprehensive extended model library functionality including:
- Model library management
- Model compatibility checking
- Model recommendations
- Fine-tuning system
- Parameter optimization
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExtendedModelLibraryTester:
    """Test suite for Ollama Extended Model Library system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        
    async def run_all_tests(self):
        """Run all extended model library tests."""
        logger.info("🚀 Starting Ollama Extended Model Library Tests")
        logger.info("=" * 70)
        
        try:
            # Test Model Library
            await self.test_model_library()
            await self.test_model_search()
            await self.test_model_recommendations()
            await self.test_model_compatibility()
            await self.test_model_comparison()
            
            # Test Fine-Tuning System
            await self.test_fine_tuning_creation()
            await self.test_fine_tuning_management()
            
            # Test Parameter Optimization
            await self.test_optimization_creation()
            await self.test_optimization_management()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            self.test_results.append({
                "test": "Test Suite",
                "status": "FAILED",
                "error": str(e)
            })
        
        self.print_test_summary()
        await self.save_test_results()
        
    async def test_model_library(self):
        """Test model library functionality."""
        logger.info("📚 Testing Model Library...")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/ai/ollama/models/library")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "categories" in data:
                    categories = data["categories"]
                    logger.info(f"✅ Model library test passed. Found {len(categories)} categories")
                    
                    # Log category information
                    for category, models in categories.items():
                        logger.info(f"   - {category}: {len(models)} models")
                    
                    self.test_results.append({
                        "test": "Model Library",
                        "status": "PASSED",
                        "details": f"Found {len(categories)} categories with {sum(len(models) for models in categories.values())} total models"
                    })
                else:
                    raise Exception("Invalid response format")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Model library test failed: {e}")
            self.test_results.append({
                "test": "Model Library",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_model_search(self):
        """Test model search functionality."""
        logger.info("🔍 Testing Model Search...")
        
        try:
            # Test basic search
            response = await self.client.get(
                f"{self.base_url}/api/ai/ollama/models/search",
                params={"query": "llama"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "results" in data:
                    results = data["results"]
                    logger.info(f"✅ Model search test passed. Found {len(results)} results for 'llama'")
                    
                    # Test filtered search
                    response_filtered = await self.client.get(
                        f"{self.base_url}/api/ai/ollama/models/search",
                        params={
                            "query": "code",
                            "category": "code",
                            "size": "medium"
                        }
                    )
                    
                    if response_filtered.status_code == 200:
                        filtered_data = response_filtered.json()
                        if filtered_data.get("success"):
                            logger.info(f"✅ Filtered search test passed. Found {len(filtered_data.get('results', []))} filtered results")
                        else:
                            raise Exception("Filtered search failed")
                    else:
                        raise Exception(f"Filtered search HTTP {response_filtered.status_code}")
                    
                    self.test_results.append({
                        "test": "Model Search",
                        "status": "PASSED",
                        "details": f"Basic search: {len(results)} results, Filtered search: working"
                    })
                else:
                    raise Exception("Invalid search response format")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Model search test failed: {e}")
            self.test_results.append({
                "test": "Model Search",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_model_recommendations(self):
        """Test model recommendation system."""
        logger.info("🎯 Testing Model Recommendations...")
        
        try:
            # Test code generation recommendations
            response = await self.client.get(
                f"{self.base_url}/api/ai/ollama/models/recommendations",
                params={"task_type": "code_generation"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "recommendations" in data:
                    recommendations = data["recommendations"]
                    logger.info(f"✅ Model recommendations test passed. Found {len(recommendations)} recommendations for code generation")
                    
                    # Test with size preference
                    response_sized = await self.client.get(
                        f"{self.base_url}/api/ai/ollama/models/recommendations",
                        params={
                            "task_type": "creative_writing",
                            "preferred_size": "medium"
                        }
                    )
                    
                    if response_sized.status_code == 200:
                        sized_data = response_sized.json()
                        if sized_data.get("success"):
                            logger.info(f"✅ Sized recommendations test passed. Found {len(sized_data.get('recommendations', []))} recommendations")
                        else:
                            raise Exception("Sized recommendations failed")
                    else:
                        raise Exception(f"Sized recommendations HTTP {response_sized.status_code}")
                    
                    self.test_results.append({
                        "test": "Model Recommendations",
                        "status": "PASSED",
                        "details": f"Code generation: {len(recommendations)} recommendations, Sized recommendations: working"
                    })
                else:
                    raise Exception("Invalid recommendations response format")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Model recommendations test failed: {e}")
            self.test_results.append({
                "test": "Model Recommendations",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_model_compatibility(self):
        """Test model compatibility checking."""
        logger.info("🔧 Testing Model Compatibility...")
        
        try:
            # Test compatibility for a known model
            response = await self.client.get(
                f"{self.base_url}/api/ai/ollama/models/compatibility/llama3.1:8b"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "compatibility" in data:
                    compatibility = data["compatibility"]
                    logger.info(f"✅ Model compatibility test passed. Compatibility score: {compatibility.get('compatibility_score', 'N/A')}")
                    
                    # Test compatibility for another model
                    response2 = await self.client.get(
                        f"{self.base_url}/api/ai/ollama/models/compatibility/codellama:7b"
                    )
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        if data2.get("success"):
                            logger.info(f"✅ Second compatibility test passed")
                        else:
                            raise Exception("Second compatibility check failed")
                    else:
                        raise Exception(f"Second compatibility HTTP {response2.status_code}")
                    
                    self.test_results.append({
                        "test": "Model Compatibility",
                        "status": "PASSED",
                        "details": f"Compatibility score: {compatibility.get('compatibility_score', 'N/A')}"
                    })
                else:
                    raise Exception("Invalid compatibility response format")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Model compatibility test failed: {e}")
            self.test_results.append({
                "test": "Model Compatibility",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_model_comparison(self):
        """Test model comparison functionality."""
        logger.info("⚖️ Testing Model Comparison...")
        
        try:
            # Test comparison of multiple models
            response = await self.client.get(
                f"{self.base_url}/api/ai/ollama/models/compare",
                params={"models": "llama3.1:8b,codellama:7b,mistral:7b"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "models" in data:
                    models = data["models"]
                    comparison_table = data.get("comparison_table", {})
                    recommendations = data.get("recommendations", [])
                    
                    logger.info(f"✅ Model comparison test passed. Compared {len(models)} models")
                    logger.info(f"   - Comparison table: {len(comparison_table)} metrics")
                    logger.info(f"   - Recommendations: {len(recommendations)} suggestions")
                    
                    self.test_results.append({
                        "test": "Model Comparison",
                        "status": "PASSED",
                        "details": f"Compared {len(models)} models with {len(comparison_table)} metrics"
                    })
                else:
                    raise Exception("Invalid comparison response format")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Model comparison test failed: {e}")
            self.test_results.append({
                "test": "Model Comparison",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_fine_tuning_creation(self):
        """Test fine-tuning job creation."""
        logger.info("🎨 Testing Fine-Tuning Job Creation...")
        
        try:
            # Create a fine-tuning job
            job_data = {
                "base_model": "llama3.1:8b",
                "target_model_name": "test-finetuned-model",
                "training_data_path": "/tmp/test_data.jsonl",
                "data_type": "jsonl",
                "hyperparameters": "balanced",
                "target_capabilities": json.dumps(["text_generation", "instruction_following"])
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/ai/ollama/fine-tuning/create",
                data=job_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "job_id" in data:
                    job_id = data["job_id"]
                    logger.info(f"✅ Fine-tuning job creation test passed. Job ID: {job_id}")
                    
                    # Store job ID for later tests
                    self.test_job_id = job_id
                    
                    self.test_results.append({
                        "test": "Fine-Tuning Creation",
                        "status": "PASSED",
                        "details": f"Created job with ID: {job_id}"
                    })
                else:
                    raise Exception("Invalid job creation response format")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Fine-tuning job creation test failed: {e}")
            self.test_results.append({
                "test": "Fine-Tuning Creation",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_fine_tuning_management(self):
        """Test fine-tuning job management."""
        logger.info("⚙️ Testing Fine-Tuning Management...")
        
        try:
            if not hasattr(self, 'test_job_id'):
                logger.warning("⚠️ Skipping fine-tuning management test - no job ID available")
                self.test_results.append({
                    "test": "Fine-Tuning Management",
                    "status": "WARNED",
                    "details": "Skipped - no job ID from creation test"
                })
                return
            
            # Test job status
            response = await self.client.get(
                f"{self.base_url}/api/ai/ollama/fine-tuning/status/{self.test_job_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "job" in data:
                    job = data["job"]
                    logger.info(f"✅ Fine-tuning status test passed. Status: {job.get('status')}")
                    
                    # Test job listing
                    response_list = await self.client.get(
                        f"{self.base_url}/api/ai/ollama/fine-tuning/jobs"
                    )
                    
                    if response_list.status_code == 200:
                        list_data = response_list.json()
                        if list_data.get("success"):
                            jobs = list_data.get("jobs", [])
                            logger.info(f"✅ Fine-tuning job listing test passed. Found {len(jobs)} jobs")
                        else:
                            raise Exception("Job listing failed")
                    else:
                        raise Exception(f"Job listing HTTP {response_list.status_code}")
                    
                    self.test_results.append({
                        "test": "Fine-Tuning Management",
                        "status": "PASSED",
                        "details": f"Status check: {job.get('status')}, Job listing: {len(jobs)} jobs"
                    })
                else:
                    raise Exception("Invalid job status response format")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Fine-tuning management test failed: {e}")
            self.test_results.append({
                "test": "Fine-Tuning Management",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_optimization_creation(self):
        """Test optimization session creation."""
        logger.info("🎯 Testing Parameter Optimization Creation...")
        
        try:
            # Create an optimization session
            session_data = {
                "model_name": "llama3.1:8b",
                "objective": "balance_quality_speed",
                "strategy": "bayesian_optimization",
                "model_type": "general"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/ai/ollama/optimization/create",
                data=session_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "session_id" in data:
                    session_id = data["session_id"]
                    logger.info(f"✅ Optimization session creation test passed. Session ID: {session_id}")
                    
                    # Store session ID for later tests
                    self.test_session_id = session_id
                    
                    self.test_results.append({
                        "test": "Optimization Creation",
                        "status": "PASSED",
                        "details": f"Created session with ID: {session_id}"
                    })
                else:
                    raise Exception("Invalid optimization session creation response format")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Optimization session creation test failed: {e}")
            self.test_results.append({
                "test": "Optimization Creation",
                "status": "FAILED",
                "error": str(e)
            })

    async def test_optimization_management(self):
        """Test optimization session management."""
        logger.info("⚙️ Testing Parameter Optimization Management...")
        
        try:
            if not hasattr(self, 'test_session_id'):
                logger.warning("⚠️ Skipping optimization management test - no session ID available")
                self.test_results.append({
                    "test": "Optimization Management",
                    "status": "WARNED",
                    "details": "Skipped - no session ID from creation test"
                })
                return
            
            # Test session status
            response = await self.client.get(
                f"{self.base_url}/api/ai/ollama/optimization/status/{self.test_session_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "session" in data:
                    session = data["session"]
                    logger.info(f"✅ Optimization status test passed. Status: {session.get('status')}")
                    
                    # Test session listing
                    response_list = await self.client.get(
                        f"{self.base_url}/api/ai/ollama/optimization/sessions"
                    )
                    
                    if response_list.status_code == 200:
                        list_data = response_list.json()
                        if list_data.get("success"):
                            sessions = list_data.get("sessions", [])
                            logger.info(f"✅ Optimization session listing test passed. Found {len(sessions)} sessions")
                        else:
                            raise Exception("Session listing failed")
                    else:
                        raise Exception(f"Session listing HTTP {response_list.status_code}")
                    
                    self.test_results.append({
                        "test": "Optimization Management",
                        "status": "PASSED",
                        "details": f"Status check: {session.get('status')}, Session listing: {len(sessions)} sessions"
                    })
                else:
                    raise Exception("Invalid session status response format")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Optimization management test failed: {e}")
            self.test_results.append({
                "test": "Optimization Management",
                "status": "FAILED",
                "error": str(e)
            })

    def print_test_summary(self):
        """Print a summary of all test results."""
        logger.info("\n" + "=" * 70)
        logger.info("📊 EXTENDED MODEL LIBRARY TEST SUMMARY")
        logger.info("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASSED")
        failed = sum(1 for result in self.test_results if result["status"] == "FAILED")
        warned = sum(1 for result in self.test_results if result["status"] == "WARNED")
        total = len(self.test_results)
        
        logger.info(f"✅ PASSED: {passed}")
        logger.info(f"❌ FAILED: {failed}")
        logger.info(f"⚠️ WARNED: {warned}")
        logger.info(f"📈 SUCCESS RATE: {(passed / total * 100):.1f}%")
        
        logger.info("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌" if result["status"] == "FAILED" else "⚠️"
            logger.info(f"{status_icon} {result['test']}: {result['status']}")
            if "details" in result:
                logger.info(f"   📝 {result['details']}")
            if "error" in result:
                logger.info(f"   🚨 {result['error']}")
        
        logger.info("\n" + "=" * 70)

    async def save_test_results(self):
        """Save test results to a JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"extended_model_library_test_results_{timestamp}.json"
            
            results_data = {
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "summary": {
                    "total_tests": len(self.test_results),
                    "passed": sum(1 for r in self.test_results if r["status"] == "PASSED"),
                    "failed": sum(1 for r in self.test_results if r["status"] == "FAILED"),
                    "warned": sum(1 for r in self.test_results if r["status"] == "WARNED"),
                    "success_rate": f"{(sum(1 for r in self.test_results if r['status'] == 'PASSED') / len(self.test_results) * 100):.1f}%"
                },
                "results": self.test_results
            }
            
            with open(filename, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            logger.info(f"💾 Test results saved to: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")

    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.client.aclose()
            logger.info("🧹 Test client cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up test client: {e}")

async def main():
    """Main test execution function."""
    logger.info("🔧 Testing Ollama Extended Model Library at: http://localhost:8000")
    logger.info("Make sure the Autonomica API is running before executing tests")
    logger.info("=" * 70)
    
    # Wait a moment for user to read
    await asyncio.sleep(2)
    
    tester = ExtendedModelLibraryTester()
    
    try:
        await tester.run_all_tests()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
