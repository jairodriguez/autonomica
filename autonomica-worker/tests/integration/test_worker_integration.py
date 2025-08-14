import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import redis
import celery

# Import worker components
from worker import app as worker_app

class TestWorkerIntegration:
    """Integration tests for the worker pod."""
    
    def test_worker_health_endpoint(self):
        """Test the worker health check endpoint."""
        client = TestClient(worker_app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "worker_name" in data
        assert "redis_connected" in data
        assert "active_tasks" in data
    
    def test_task_submission_endpoint(self):
        """Test the task submission endpoint."""
        client = TestClient(worker_app)
        
        task_data = {
            "task_type": "web_scraping",
            "payload": {
                "url": "https://example.com",
                "user_id": "user_123"
            }
        }
        
        response = client.post("/tasks/submit", json=task_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "submitted"
    
    def test_task_status_endpoint(self):
        """Test the task status endpoint."""
        client = TestClient(worker_app)
        
        # First submit a task
        task_data = {
            "task_type": "web_scraping",
            "payload": {
                "url": "https://example.com",
                "user_id": "user_123"
            }
        }
        
        submit_response = client.post("/tasks/submit", json=task_data)
        task_id = submit_response.json()["task_id"]
        
        # Then check its status
        response = client.get(f"/tasks/{task_id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert "created_at" in data
    
    def test_redis_integration(self):
        """Test Redis integration functionality."""
        with patch('redis.Redis') as mock_redis:
            mock_instance = Mock()
            mock_redis.return_value = mock_instance
            
            # Mock Redis operations
            mock_instance.ping.return_value = True
            mock_instance.set.return_value = True
            mock_instance.get.return_value = json.dumps({
                "task_id": "test_123",
                "status": "completed",
                "result": "test result"
            })
            
            # Test Redis connectivity
            client = TestClient(worker_app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["redis_connected"] == True
    
    def test_celery_task_processing(self):
        """Test Celery task processing integration."""
        with patch('celery.Celery') as mock_celery:
            mock_instance = Mock()
            mock_celery.return_value = mock_instance
            
            # Mock task submission
            mock_task = Mock()
            mock_task.id = "celery_task_123"
            mock_instance.send_task.return_value = mock_task
            
            # Test task submission
            client = TestClient(worker_app)
            task_data = {
                "task_type": "ai_processing",
                "payload": {
                    "prompt": "Test prompt",
                    "user_id": "user_123"
                }
            }
            
            response = client.post("/tasks/submit", json=task_data)
            assert response.status_code == 200
            
            data = response.json()
            assert "task_id" in data
    
    def test_web_scraping_task(self):
        """Test web scraping task integration."""
        with patch('playwright.async_api.async_playwright') as mock_playwright:
            mock_playwright_instance = Mock()
            mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
            
            mock_browser = Mock()
            mock_page = Mock()
            
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_browser.new_page.return_value = mock_page
            mock_page.goto.return_value = None
            mock_page.content.return_value = "<html><body>Test content</body></html>"
            mock_browser.close.return_value = None
            
            # Test web scraping task
            client = TestClient(worker_app)
            task_data = {
                "task_type": "web_scraping",
                "payload": {
                    "url": "https://example.com",
                    "user_id": "user_123"
                }
            }
            
            response = client.post("/tasks/submit", json=task_data)
            assert response.status_code == 200
    
    def test_ai_processing_task(self):
        """Test AI processing task integration."""
        with patch('openai.OpenAI') as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance
            
            # Mock OpenAI response
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="AI generated response"))]
            mock_instance.chat.completions.create.return_value = mock_response
            
            # Test AI processing task
            client = TestClient(worker_app)
            task_data = {
                "task_type": "ai_processing",
                "payload": {
                    "prompt": "Generate a response",
                    "user_id": "user_123"
                }
            }
            
            response = client.post("/tasks/submit", json=task_data)
            assert response.status_code == 200
    
    def test_data_analysis_task(self):
        """Test data analysis task integration."""
        with patch('pandas.read_csv') as mock_pandas:
            mock_dataframe = Mock()
            mock_pandas.return_value = mock_dataframe
            mock_dataframe.describe.return_value = Mock()
            mock_dataframe.head.return_value = Mock()
            
            # Test data analysis task
            client = TestClient(worker_app)
            task_data = {
                "task_type": "data_analysis",
                "payload": {
                    "data_source": "test_data.csv",
                    "analysis_type": "summary",
                    "user_id": "user_123"
                }
            }
            
            response = client.post("/tasks/submit", json=task_data)
            assert response.status_code == 200
    
    def test_social_media_task(self):
        """Test social media task integration."""
        with patch('tweepy.API') as mock_tweepy:
            mock_instance = Mock()
            mock_tweepy.return_value = mock_instance
            mock_instance.update_status.return_value = Mock()
            
            # Test social media task
            client = TestClient(worker_app)
            task_data = {
                "task_type": "social_media",
                "payload": {
                    "platform": "twitter",
                    "content": "Test post",
                    "user_id": "user_123"
                }
            }
            
            response = client.post("/tasks/submit", json=task_data)
            assert response.status_code == 200
    
    def test_task_queue_management(self):
        """Test task queue management functionality."""
        with patch('redis.Redis') as mock_redis:
            mock_instance = Mock()
            mock_redis.return_value = mock_instance
            
            # Mock queue operations
            mock_instance.lpush.return_value = 1
            mock_instance.rpop.return_value = json.dumps({
                "task_type": "test",
                "payload": {}
            })
            mock_instance.llen.return_value = 5
            
            # Test queue status
            client = TestClient(worker_app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "active_tasks" in data
    
    def test_error_handling(self):
        """Test error handling in worker tasks."""
        with patch('redis.Redis') as mock_redis:
            mock_instance = Mock()
            mock_redis.return_value = mock_instance
            
            # Mock Redis failure
            mock_instance.ping.side_effect = Exception("Redis connection failed")
            
            # Test health endpoint with Redis failure
            client = TestClient(worker_app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["redis_connected"] == False
    
    def test_concurrent_task_processing(self):
        """Test concurrent task processing capability."""
        import threading
        import time
        
        results = []
        
        def submit_task():
            try:
                client = TestClient(worker_app)
                task_data = {
                    "task_type": "web_scraping",
                    "payload": {
                        "url": "https://example.com",
                        "user_id": "user_123"
                    }
                }
                
                response = client.post("/tasks/submit", json=task_data)
                results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {e}")
        
        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=submit_task)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All tasks should be submitted successfully
        assert len(results) == 3
        assert all(status == 200 for status in results if isinstance(status, int))
    
    def test_task_validation(self):
        """Test task validation functionality."""
        client = TestClient(worker_app)
        
        # Test with invalid task type
        invalid_task = {
            "task_type": "invalid_type",
            "payload": {}
        }
        
        response = client.post("/tasks/submit", json=invalid_task)
        assert response.status_code == 400
        
        # Test with missing payload
        incomplete_task = {
            "task_type": "web_scraping"
        }
        
        response = client.post("/tasks/submit", json=incomplete_task)
        assert response.status_code == 422
    
    def test_worker_metrics(self):
        """Test worker metrics and monitoring."""
        client = TestClient(worker_app)
        
        # Submit a few tasks to generate metrics
        for i in range(3):
            task_data = {
                "task_type": "web_scraping",
                "payload": {
                    "url": f"https://example{i}.com",
                    "user_id": "user_123"
                }
            }
            client.post("/tasks/submit", json=task_data)
        
        # Check health endpoint for metrics
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "active_tasks" in data
        assert "worker_name" in data
        assert "timestamp" in data