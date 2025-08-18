"""
Pytest configuration and fixtures for Autonomica API tests.
"""
import os
import sys
import pytest
import asyncio
from pathlib import Path
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, patch

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import FastAPI test client
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import application components
from main_api import app
from app.auth.clerk_middleware import get_current_user
from app.models.agent import Agent, AgentType
from app.models.user import ClerkUser

# Test configuration
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "DEBUG"

# Mock authentication for tests
@pytest.fixture
def mock_current_user() -> ClerkUser:
    """Mock authenticated user for testing."""
    return ClerkUser(
        user_id="test_user_123",
        email="test@example.com",
        name="Test User",
        is_verified=True
    )

@pytest.fixture
def mock_auth_dependency(mock_current_user: ClerkUser):
    """Mock authentication dependency."""
    def _mock_get_current_user():
        return mock_current_user
    
    return _mock_get_current_user

@pytest.fixture
def test_app(mock_auth_dependency) -> FastAPI:
    """Test FastAPI application with mocked authentication."""
    # Override the authentication dependency
    app.dependency_overrides[get_current_user] = mock_auth_dependency
    return app

@pytest.fixture
def test_client(test_app: FastAPI) -> TestClient:
    """Test client for making requests to the test app."""
    return TestClient(test_app)

@pytest.fixture
def sample_agent() -> Agent:
    """Sample agent for testing."""
    return Agent(
        id="test_agent_123",
        name="Test Strategy Agent",
        description="A test agent for strategy analysis",
        agent_type=AgentType.STRATEGY,
        model="gpt-4",
        is_active=True,
        user_id="test_user_123",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z"
    )

@pytest.fixture
def sample_agents() -> list[Agent]:
    """Sample list of agents for testing."""
    return [
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

@pytest.fixture
def mock_redis():
    """Mock Redis connection for testing."""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = 0
    mock_redis.incr.return_value = 1
    mock_redis.decr.return_value = 0
    return mock_redis

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = Mock(
        choices=[
            Mock(
                message=Mock(
                    content="This is a test response from the AI model."
                )
            )
        ]
    )
    return mock_client

@pytest.fixture
def mock_workforce():
    """Mock workforce for testing."""
    mock_workforce = Mock()
    mock_workforce.run_agents.return_value = "Test response from workforce"
    mock_workforce.select_agents.return_value = []
    return mock_workforce

# Database fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_test_environment():
    """Set up test environment before each test."""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["ENVIRONMENT"] = "test"
    
    # Clean up any test data
    yield
    
    # Cleanup after tests
    pass

# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, external dependencies)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (slowest, full system)"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer than 5 seconds"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "auth: Authentication and authorization tests"
    )
    config.addinivalue_line(
        "markers", "database: Database-related tests"
    )
    config.addinivalue_line(
        "markers", "worker: Worker pod tests"
    )
    config.addinivalue_line(
        "markers", "security: Security-related tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and load tests"
    )
    config.addinivalue_line(
        "markers", "smoke: Basic functionality tests"
    )
    config.addinivalue_line(
        "markers", "regression: Regression test suite"
    )

# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add unit marker to tests that don't have any marker
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)
        
        # Add API marker to tests that test API endpoints
        if "api" in item.name.lower() or "endpoint" in item.name.lower():
            item.add_marker(pytest.mark.api)
        
        # Add auth marker to tests that test authentication
        if "auth" in item.name.lower() or "login" in item.name.lower():
            item.add_marker(pytest.mark.auth)
        
        # Add database marker to tests that test database operations
        if "db" in item.name.lower() or "database" in item.name.lower():
            item.add_marker(pytest.mark.database)

# Test reporting
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Custom test summary output."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    # Print test counts by marker
    for marker in ["unit", "integration", "e2e", "api", "auth", "database"]:
        items = terminalreporter.stats.get(f"passed_{marker}", [])
        if items:
            print(f"{marker.upper()}: {len(items)} tests passed")
    
    print("="*60)
