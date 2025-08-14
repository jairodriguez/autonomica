import pytest
import asyncio
import tempfile
import shutil
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import redis
import os
import sqlite3
from contextlib import contextmanager

# Import your FastAPI app
from main_api import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    # Create test database
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            model TEXT,
            status TEXT DEFAULT 'idle',
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_redis():
    """Mock Redis connection for integration testing."""
    with patch('redis.Redis') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        
        # Mock Redis operations
        mock_instance.ping.return_value = True
        mock_instance.get.return_value = None
        mock_instance.set.return_value = True
        mock_instance.delete.return_value = 1
        mock_instance.exists.return_value = 0
        mock_instance.keys.return_value = []
        mock_instance.hget.return_value = None
        mock_instance.hset.return_value = 1
        mock_instance.hgetall.return_value = {}
        mock_instance.lpush.return_value = 1
        mock_instance.rpop.return_value = None
        mock_instance.llen.return_value = 0
        
        yield mock_instance

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for integration testing."""
    with patch('openai.OpenAI') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        
        # Mock chat completion
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test AI response"))]
        mock_response.usage = Mock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        
        mock_instance.chat.completions.create.return_value = mock_response
        mock_instance.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        
        yield mock_instance

@pytest.fixture
def mock_clerk():
    """Mock Clerk authentication for integration testing."""
    with patch('app.auth.clerk_middleware.get_current_user') as mock:
        mock.return_value = Mock(
            id="user_123",
            email="test@example.com",
            name="Test User"
        )
        yield mock

@pytest.fixture
def mock_celery():
    """Mock Celery for integration testing."""
    with patch('celery.Celery') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        
        # Mock task submission
        mock_task = Mock()
        mock_task.id = "task_123"
        mock_instance.send_task.return_value = mock_task
        
        yield mock_instance

@pytest.fixture
def sample_user_data():
    """Sample user data for integration testing."""
    return {
        "id": "user_123",
        "email": "test@example.com",
        "name": "Test User",
        "created_at": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def sample_agent_data():
    """Sample agent data for integration testing."""
    return {
        "id": "agent_123",
        "name": "Test Agent",
        "type": "strategy",
        "description": "A test agent for integration testing",
        "model": "gpt-4",
        "status": "idle",
        "user_id": "user_123"
    }

@pytest.fixture
def sample_chat_message():
    """Sample chat message for integration testing."""
    return {
        "id": "msg_123",
        "content": "Hello, this is a test message for integration testing!",
        "role": "user",
        "timestamp": "2024-01-01T00:00:00Z",
        "user_id": "user_123",
        "agent_id": "agent_123"
    }

@pytest.fixture
def auth_headers():
    """Authentication headers for integration testing."""
    return {"Authorization": "Bearer test-integration-token"}

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for external API calls."""
    with patch('httpx.AsyncClient') as mock:
        mock_instance = Mock()
        mock.return_value.__aenter__.return_value = mock_instance
        mock.return_value.__aexit__.return_value = None
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        
        mock_instance.get.return_value = mock_response
        mock_instance.post.return_value = mock_response
        mock_instance.put.return_value = mock_response
        mock_instance.delete.return_value = mock_response
        
        yield mock_instance

@pytest.fixture(autouse=True)
def setup_integration_test_environment():
    """Setup integration test environment variables."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ.update({
        "TESTING": "true",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "DEBUG",
        "REDIS_URL": "redis://localhost:6379/1",
        "DATABASE_URL": "sqlite:///./test_integration.db",
        "OPENAI_API_KEY": "test-integration-key",
        "CLERK_SECRET_KEY": "test-integration-key",
        "AI_PROVIDER": "mock"
    })
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

@contextmanager
def mock_external_services():
    """Context manager to mock all external services."""
    with patch('redis.Redis'), \
         patch('openai.OpenAI'), \
         patch('celery.Celery'), \
         patch('httpx.AsyncClient'):
        yield