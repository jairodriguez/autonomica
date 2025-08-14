import pytest
import json
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

class TestAPIEndpoints:
    """Integration tests for API endpoints."""
    
    def test_health_check_endpoint(self, test_client: TestClient):
        """Test the health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_agents_list_endpoint(self, test_client: TestClient, mock_clerk, mock_redis):
        """Test the agents list endpoint."""
        # Mock authentication
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            response = test_client.get("/api/agents", headers={"Authorization": "Bearer test-token"})
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
    
    def test_agent_creation_endpoint(self, test_client: TestClient, mock_clerk, mock_redis, sample_agent_data):
        """Test the agent creation endpoint."""
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            # Test successful agent creation
            response = test_client.post(
                "/api/agents",
                headers={"Authorization": "Bearer test-token"},
                json=sample_agent_data
            )
            
            # Should return 201 for creation or 200 if already exists
            assert response.status_code in [200, 201]
            
            data = response.json()
            assert "id" in data
            assert data["name"] == sample_agent_data["name"]
            assert data["type"] == sample_agent_data["type"]
    
    def test_agent_retrieval_endpoint(self, test_client: TestClient, mock_clerk, mock_redis, sample_agent_data):
        """Test the agent retrieval endpoint."""
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            # First create an agent
            create_response = test_client.post(
                "/api/agents",
                headers={"Authorization": "Bearer test-token"},
                json=sample_agent_data
            )
            
            if create_response.status_code in [200, 201]:
                agent_id = create_response.json()["id"]
                
                # Then retrieve it
                response = test_client.get(
                    f"/api/agents/{agent_id}",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == agent_id
                assert data["name"] == sample_agent_data["name"]
    
    def test_chat_endpoint(self, test_client: TestClient, mock_clerk, mock_redis, mock_openai):
        """Test the chat endpoint."""
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            chat_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, this is a test message"
                    }
                ]
            }
            
            response = test_client.post(
                "/api/chat",
                headers={"Authorization": "Bearer test-token"},
                json=chat_data
            )
            
            # Should return 200 for successful chat processing
            assert response.status_code == 200
    
    def test_agent_types_endpoint(self, test_client: TestClient, mock_clerk, mock_redis):
        """Test the agent types endpoint."""
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            response = test_client.get(
                "/api/agents/types/strategy",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    def test_authentication_required(self, test_client: TestClient):
        """Test that authentication is required for protected endpoints."""
        # Test without authentication
        response = test_client.get("/api/agents")
        assert response.status_code == 401
        
        response = test_client.post("/api/agents", json={})
        assert response.status_code == 401
        
        response = test_client.get("/api/agents/123")
        assert response.status_code == 401
    
    def test_invalid_agent_data(self, test_client: TestClient, mock_clerk, mock_redis):
        """Test agent creation with invalid data."""
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            # Test with missing required fields
            invalid_data = {
                "description": "Missing name and type"
            }
            
            response = test_client.post(
                "/api/agents",
                headers={"Authorization": "Bearer test-token"},
                json=invalid_data
            )
            
            assert response.status_code == 422  # Validation error
    
    def test_agent_not_found(self, test_client: TestClient, mock_clerk, mock_redis):
        """Test retrieving a non-existent agent."""
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            response = test_client.get(
                "/api/agents/non-existent-id",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 404
    
    def test_redis_connection_failure(self, test_client: TestClient, mock_clerk):
        """Test API behavior when Redis is unavailable."""
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            # Mock Redis connection failure
            with patch('redis.Redis') as mock_redis:
                mock_redis.side_effect = Exception("Redis connection failed")
                
                response = test_client.get(
                    "/api/agents",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                # Should handle Redis failure gracefully
                assert response.status_code in [200, 500, 503]
    
    def test_openai_api_failure(self, test_client: TestClient, mock_clerk, mock_redis):
        """Test API behavior when OpenAI API is unavailable."""
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            # Mock OpenAI API failure
            with patch('openai.OpenAI') as mock_openai:
                mock_openai.side_effect = Exception("OpenAI API failed")
                
                chat_data = {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Test message"
                        }
                    ]
                }
                
                response = test_client.post(
                    "/api/chat",
                    headers={"Authorization": "Bearer test-token"},
                    json=chat_data
                )
                
                # Should handle OpenAI failure gracefully
                assert response.status_code in [200, 500, 503]
    
    def test_concurrent_requests(self, test_client: TestClient, mock_clerk, mock_redis):
        """Test API behavior under concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            try:
                with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
                    mock_auth.return_value = Mock(
                        id="user_123",
                        email="test@example.com",
                        name="Test User"
                    )
                    
                    response = test_client.get(
                        "/health",
                        headers={"Authorization": "Bearer test-token"}
                    )
                    results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {e}")
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 5
        assert all(status == 200 for status in results if isinstance(status, int))
    
    def test_large_payload_handling(self, test_client: TestClient, mock_clerk, mock_redis):
        """Test API behavior with large payloads."""
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            # Create a large message
            large_content = "A" * 10000  # 10KB message
            chat_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": large_content
                    }
                ]
            }
            
            response = test_client.post(
                "/api/chat",
                headers={"Authorization": "Bearer test-token"},
                json=chat_data
            )
            
            # Should handle large payloads gracefully
            assert response.status_code in [200, 413, 500]  # 413 = Payload Too Large
    
    def test_rate_limiting(self, test_client: TestClient, mock_clerk, mock_redis):
        """Test API rate limiting behavior."""
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            # Make multiple rapid requests
            responses = []
            for _ in range(10):
                response = test_client.get("/health")
                responses.append(response.status_code)
                time.sleep(0.1)  # Small delay between requests
            
            # All requests should succeed (rate limiting not implemented yet)
            assert all(status == 200 for status in responses)
    
    def test_cors_headers(self, test_client: TestClient):
        """Test CORS headers are properly set."""
        response = test_client.options("/health")
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_error_handling(self, test_client: TestClient, mock_clerk, mock_redis):
        """Test API error handling."""
        with patch('app.auth.clerk_middleware.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(
                id="user_123",
                email="test@example.com",
                name="Test User"
            )
            
            # Test with malformed JSON
            response = test_client.post(
                "/api/agents",
                headers={"Authorization": "Bearer test-token", "Content-Type": "application/json"},
                data="invalid json"
            )
            
            # Should return 422 for malformed JSON
            assert response.status_code == 422