"""
Integration tests for API endpoints and component interactions.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main_api import app
from app.models.agent import Agent, AgentType
from app.models.user import ClerkUser
from app.services.workforce import Workforce
from app.services.agent_manager import AgentManager
from app.services.seo_service import SEOService
from app.config.database import get_db, Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocreate=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user():
    """Create a test user for authentication."""
    return ClerkUser(
        user_id="test_user_123",
        email="test@example.com",
        name="Test User",
        is_verified=True
    )

@pytest.fixture
def test_agents(db_session):
    """Create test agents in the database."""
    agents = [
        Agent(
            id="agent_1",
            name="Strategy Specialist",
            description="Specializes in marketing strategy",
            agent_type=AgentType.STRATEGY,
            model="gpt-4",
            is_active=True,
            user_id="test_user_123",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z"
        ),
        Agent(
            id="agent_2",
            name="Content Creator",
            description="Creates marketing content",
            agent_type=AgentType.CONTENT,
            model="gpt-4",
            is_active=True,
            user_id="test_user_123",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z"
        ),
        Agent(
            id="agent_3",
            name="Analytics Expert",
            description="Analyzes marketing data",
            agent_type=AgentType.ANALYTICS,
            model="gpt-4",
            is_active=True,
            user_id="test_user_123",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z"
        )
    ]
    
    for agent in agents:
        db_session.add(agent)
    db_session.commit()
    
    return agents

@pytest.fixture
def test_client(db_session, test_user):
    """Create a test client with database and authentication."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock authentication
    def mock_get_current_user():
        return test_user
    
    from app.auth.clerk_middleware import get_current_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with TestClient(app) as client:
        yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()

class TestAPIIntegration:
    """Integration tests for API endpoints and component interactions."""
    
    @pytest.mark.integration
    def test_agent_workflow_integration(self, test_client, test_agents):
        """Test complete agent workflow from creation to execution."""
        # 1. Get available agents
        response = test_client.get("/api/agents")
        assert response.status_code == 200
        agents_data = response.json()
        assert len(agents_data) == 3
        
        # 2. Select agents for a task
        task_data = {
            "task": "Create a marketing strategy for a new product launch",
            "agent_types": ["STRATEGY", "CONTENT"],
            "priority": "high"
        }
        
        response = test_client.post("/api/workforce/select-agents", json=task_data)
        assert response.status_code == 200
        selected_agents = response.json()
        assert len(selected_agents) >= 1
        
        # 3. Execute task with selected agents
        execution_data = {
            "task": task_data["task"],
            "agent_ids": [agent["id"] for agent in selected_agents],
            "parameters": {
                "target_audience": "B2B professionals",
                "budget": "medium",
                "timeline": "3 months"
            }
        }
        
        response = test_client.post("/api/workforce/run-agents", json=execution_data)
        assert response.status_code == 200
        result = response.json()
        assert "result" in result
        assert "execution_id" in result
    
    @pytest.mark.integration
    def test_seo_pipeline_integration(self, test_client):
        """Test SEO pipeline integration with multiple services."""
        # 1. Submit URL for SEO analysis
        url_data = {
            "url": "https://example.com",
            "analysis_type": "comprehensive",
            "include_competitors": True
        }
        
        response = test_client.post("/api/seo/analyze", json=url_data)
        assert response.status_code == 200
        analysis_id = response.json()["analysis_id"]
        
        # 2. Get analysis status
        response = test_client.get(f"/api/seo/status/{analysis_id}")
        assert response.status_code == 200
        status = response.json()
        assert "status" in status
        
        # 3. Get keyword suggestions
        response = test_client.get(f"/api/seo/keywords/{analysis_id}")
        assert response.status_code == 200
        keywords = response.json()
        assert "keywords" in keywords
        
        # 4. Get competitor analysis
        response = test_client.get(f"/api/seo/competitors/{analysis_id}")
        assert response.status_code == 200
        competitors = response.json()
        assert "competitors" in competitors
        
        # 5. Get final SEO score
        response = test_client.get(f"/api/seo/score/{analysis_id}")
        assert response.status_code == 200
        score = response.json()
        assert "overall_score" in score
        assert "category_scores" in score
    
    @pytest.mark.integration
    def test_user_agent_management_integration(self, test_client, test_agents):
        """Test user agent management workflow."""
        # 1. Get user's agents
        response = test_client.get("/api/agents/my-agents")
        assert response.status_code == 200
        user_agents = response.json()
        assert len(user_agents) == 3
        
        # 2. Update agent configuration
        agent_id = user_agents[0]["id"]
        update_data = {
            "name": "Updated Strategy Specialist",
            "description": "Enhanced strategy capabilities",
            "is_active": True
        }
        
        response = test_client.put(f"/api/agents/{agent_id}", json=update_data)
        assert response.status_code == 200
        updated_agent = response.json()
        assert updated_agent["name"] == "Updated Strategy Specialist"
        
        # 3. Test agent activation/deactivation
        response = test_client.patch(f"/api/agents/{agent_id}/toggle", json={"is_active": False})
        assert response.status_code == 200
        toggled_agent = response.json()
        assert toggled_agent["is_active"] == False
        
        # 4. Verify agent is not available for selection
        task_data = {
            "task": "Simple strategy task",
            "agent_types": ["STRATEGY"],
            "priority": "low"
        }
        
        response = test_client.post("/api/workforce/select-agents", json=task_data)
        assert response.status_code == 200
        selected_agents = response.json()
        # Should not include the deactivated agent
        assert not any(agent["id"] == agent_id for agent in selected_agents)
    
    @pytest.mark.integration
    def test_error_handling_integration(self, test_client):
        """Test error handling across different API components."""
        # 1. Test invalid agent selection
        invalid_task = {
            "task": "",  # Empty task
            "agent_types": ["INVALID_TYPE"],
            "priority": "invalid_priority"
        }
        
        response = test_client.post("/api/workforce/select-agents", json=invalid_task)
        assert response.status_code == 422  # Validation error
        
        # 2. Test non-existent agent execution
        execution_data = {
            "task": "Valid task",
            "agent_ids": ["non_existent_agent_id"],
            "parameters": {}
        }
        
        response = test_client.post("/api/workforce/run-agents", json=execution_data)
        assert response.status_code == 404  # Not found
        
        # 3. Test invalid SEO analysis
        invalid_url_data = {
            "url": "not_a_valid_url",
            "analysis_type": "invalid_type"
        }
        
        response = test_client.post("/api/seo/analyze", json=invalid_url_data)
        assert response.status_code == 422  # Validation error
        
        # 4. Test non-existent analysis ID
        response = test_client.get("/api/seo/status/non_existent_id")
        assert response.status_code == 404  # Not found
    
    @pytest.mark.integration
    def test_concurrent_operations_integration(self, test_client, test_agents):
        """Test concurrent operations and resource management."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request(request_type, data):
            """Make a request and store the result."""
            try:
                if request_type == "get_agents":
                    response = test_client.get("/api/agents")
                elif request_type == "select_agents":
                    response = test_client.post("/api/workforce/select-agents", json=data)
                elif request_type == "seo_analyze":
                    response = test_client.post("/api/seo/analyze", json=data)
                
                results.append((request_type, response.status_code))
            except Exception as e:
                errors.append((request_type, str(e)))
        
        # Create multiple threads for concurrent requests
        threads = []
        
        # Thread 1: Get agents
        threads.append(threading.Thread(
            target=make_request, 
            args=("get_agents", None)
        ))
        
        # Thread 2: Select agents
        threads.append(threading.Thread(
            target=make_request, 
            args=("select_agents", {
                "task": "Concurrent task 1",
                "agent_types": ["STRATEGY"],
                "priority": "medium"
            })
        ))
        
        # Thread 3: SEO analysis
        threads.append(threading.Thread(
            target=make_request, 
            args=("seo_analyze", {
                "url": "https://example1.com",
                "analysis_type": "basic"
            })
        ))
        
        # Thread 4: Another agent selection
        threads.append(threading.Thread(
            target=make_request, 
            args=("select_agents", {
                "task": "Concurrent task 2",
                "agent_types": ["CONTENT"],
                "priority": "low"
            })
        ))
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests completed successfully
        assert len(results) == 4
        assert len(errors) == 0
        
        # Check that all requests returned success status codes
        for request_type, status_code in results:
            assert status_code in [200, 201], f"{request_type} failed with status {status_code}"
    
    @pytest.mark.integration
    def test_data_consistency_integration(self, test_client, test_agents):
        """Test data consistency across different API endpoints."""
        # 1. Get agents from different endpoints
        response1 = test_client.get("/api/agents")
        response2 = test_client.get("/api/agents/my-agents")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        agents1 = response1.json()
        agents2 = response2.json()
        
        # Both endpoints should return the same agent data for the authenticated user
        assert len(agents1) == len(agents2)
        
        # Verify agent IDs match
        agent_ids1 = {agent["id"] for agent in agents1}
        agent_ids2 = {agent["id"] for agent in agents2}
        assert agent_ids1 == agent_ids2
        
        # 2. Test agent data consistency after update
        agent_id = agents1[0]["id"]
        original_name = agents1[0]["name"]
        
        # Update agent name
        update_data = {"name": "Consistency Test Agent"}
        response = test_client.put(f"/api/agents/{agent_id}", json=update_data)
        assert response.status_code == 200
        
        # Verify both endpoints return updated data
        response1 = test_client.get("/api/agents")
        response2 = test_client.get("/api/agents/my-agents")
        
        agents1_updated = response1.json()
        agents2_updated = response2.json()
        
        updated_agent1 = next(agent for agent in agents1_updated if agent["id"] == agent_id)
        updated_agent2 = next(agent for agent in agents2_updated if agent["id"] == agent_id)
        
        assert updated_agent1["name"] == "Consistency Test Agent"
        assert updated_agent2["name"] == "Consistency Test Agent"
        assert updated_agent1["name"] == updated_agent2["name"]
        
        # 3. Verify agent selection consistency
        task_data = {
            "task": "Data consistency test",
            "agent_types": ["STRATEGY"],
            "priority": "medium"
        }
        
        response = test_client.post("/api/workforce/select-agents", json=task_data)
        assert response.status_code == 200
        selected_agents = response.json()
        
        # Selected agents should have consistent data with main endpoints
        for selected_agent in selected_agents:
            agent_id = selected_agent["id"]
            main_agent = next(agent for agent in agents1_updated if agent["id"] == agent_id)
            my_agent = next(agent for agent in agents2_updated if agent["id"] == agent_id)
            
            assert selected_agent["name"] == main_agent["name"]
            assert selected_agent["name"] == my_agent["name"]
            assert selected_agent["agent_type"] == main_agent["agent_type"]
            assert selected_agent["agent_type"] == my_agent["agent_type"]
    
    @pytest.mark.integration
    def test_performance_integration(self, test_client, test_agents):
        """Test API performance under normal load."""
        import time
        
        # 1. Measure agent listing performance
        start_time = time.time()
        response = test_client.get("/api/agents")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Response should be under 500ms for basic operations
        assert response_time < 0.5, f"Agent listing took {response_time:.3f}s, expected < 0.5s"
        
        # 2. Measure agent selection performance
        start_time = time.time()
        response = test_client.post("/api/workforce/select-agents", json={
            "task": "Performance test task",
            "agent_types": ["STRATEGY", "CONTENT"],
            "priority": "medium"
        })
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Agent selection should be under 1s
        assert response_time < 1.0, f"Agent selection took {response_time:.3f}s, expected < 1.0s"
        
        # 3. Measure SEO analysis performance
        start_time = time.time()
        response = test_client.post("/api/seo/analyze", json={
            "url": "https://performance-test.com",
            "analysis_type": "basic"
        })
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # SEO analysis initiation should be under 2s
        assert response_time < 2.0, f"SEO analysis took {response_time:.3f}s, expected < 2.0s"
    
    @pytest.mark.integration
    def test_authentication_integration(self, test_client):
        """Test authentication integration across protected endpoints."""
        # 1. Test protected endpoint without authentication
        # Remove authentication override temporarily
        app.dependency_overrides.clear()
        
        response = test_client.get("/api/agents/my-agents")
        assert response.status_code == 401  # Unauthorized
        
        # 2. Test protected endpoint with invalid authentication
        # Mock invalid user
        def mock_invalid_user():
            return None
        
        from app.auth.clerk_middleware import get_current_user
        app.dependency_overrides[get_current_user] = mock_invalid_user
        
        response = test_client.get("/api/agents/my-agents")
        assert response.status_code == 401  # Unauthorized
        
        # 3. Test protected endpoint with valid authentication
        # Restore valid authentication
        def mock_valid_user():
            return ClerkUser(
                user_id="test_user_123",
                email="test@example.com",
                name="Test User",
                is_verified=True
            )
        
        app.dependency_overrides[get_current_user] = mock_valid_user
        
        response = test_client.get("/api/agents/my-agents")
        assert response.status_code == 200  # Authorized
        
        # Clean up
        app.dependency_overrides.clear()

@pytest.mark.integration
def test_workflow_end_to_end(test_client, test_agents):
    """Test complete end-to-end workflow."""
    # 1. User creates a marketing task
    task_data = {
        "task": "Launch campaign for new SaaS product",
        "agent_types": ["STRATEGY", "CONTENT", "ANALYTICS"],
        "priority": "high",
        "deadline": "2025-02-01T00:00:00Z"
    }
    
    # 2. Select appropriate agents
    response = test_client.post("/api/workforce/select-agents", json=task_data)
    assert response.status_code == 200
    selected_agents = response.json()
    assert len(selected_agents) >= 2  # Should select multiple agents
    
    # 3. Execute the task
    execution_data = {
        "task": task_data["task"],
        "agent_ids": [agent["id"] for agent in selected_agents],
        "parameters": {
            "product": "AI-powered marketing automation",
            "target_audience": "Marketing professionals",
            "budget": "high",
            "channels": ["social", "email", "content"]
        }
    }
    
    response = test_client.post("/api/workforce/run-agents", json=execution_data)
    assert response.status_code == 200
    execution_result = response.json()
    assert "execution_id" in execution_result
    assert "result" in execution_result
    
    # 4. Monitor execution status
    execution_id = execution_result["execution_id"]
    response = test_client.get(f"/api/workforce/status/{execution_id}")
    assert response.status_code == 200
    status = response.json()
    assert "status" in status
    
    # 5. Get final results
    response = test_client.get(f"/api/workforce/results/{execution_id}")
    assert response.status_code == 200
    results = response.json()
    assert "output" in results
    assert "metrics" in results
    
    # 6. Verify data consistency
    # Check that all selected agents are still available
    response = test_client.get("/api/agents/my-agents")
    assert response.status_code == 200
    available_agents = response.json()
    
    for selected_agent in selected_agents:
        agent_id = selected_agent["id"]
        available_agent = next(
            (agent for agent in available_agents if agent["id"] == agent_id), 
            None
        )
        assert available_agent is not None
        assert available_agent["is_active"] == True
