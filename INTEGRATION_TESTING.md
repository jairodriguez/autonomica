# Integration Testing Framework

## Overview

This document describes the comprehensive integration testing framework implemented for the Autonomica project. The framework covers both frontend and backend components, ensuring proper component interactions, API integration, and system behavior validation.

## Architecture

### Backend Integration Tests
- **Location**: `autonomica-api/tests/integration/`
- **Framework**: Pytest with FastAPI TestClient
- **Coverage**: API endpoints, database operations, Redis integration, external services
- **Mocking**: Comprehensive mocking of external dependencies

### Frontend Integration Tests
- **Location**: `autonomica-frontend/src/__tests__/integration/`
- **Framework**: Jest with React Testing Library and MSW
- **Coverage**: Component interactions, API calls, user workflows
- **Mocking**: Mock Service Worker for API simulation

### Worker Pod Integration Tests
- **Location**: `autonomica-worker/tests/integration/`
- **Framework**: Pytest with FastAPI TestClient
- **Coverage**: Task processing, Redis integration, Celery workflows
- **Mocking**: External service and dependency mocking

## Test Categories

### 1. API Integration Tests
- **Endpoint Testing**: Verify all API endpoints respond correctly
- **Authentication**: Test Clerk authentication middleware
- **Data Validation**: Validate request/response schemas
- **Error Handling**: Test error scenarios and edge cases
- **Performance**: Test concurrent requests and large payloads

### 2. Database Integration Tests
- **CRUD Operations**: Test database create, read, update, delete
- **Transaction Handling**: Verify database transaction integrity
- **Connection Management**: Test database connection pooling
- **Migration Testing**: Validate database schema migrations

### 3. Redis Integration Tests
- **Cache Operations**: Test Redis caching functionality
- **Queue Management**: Verify task queue operations
- **Session Storage**: Test user session management
- **Connection Failures**: Test Redis failure scenarios

### 4. External Service Integration Tests
- **OpenAI API**: Test AI service integration
- **Clerk Authentication**: Verify authentication service
- **Social Media APIs**: Test social platform integrations
- **Web Scraping**: Validate Playwright integration

### 5. Component Integration Tests
- **User Workflows**: Test complete user journeys
- **State Management**: Verify component state interactions
- **API Integration**: Test frontend-backend communication
- **Error Boundaries**: Test error handling in components

## Running Integration Tests

### Backend Tests

```bash
# Run all integration tests
cd autonomica-api
python run_integration_tests.py

# Run specific test categories
pytest tests/integration/ -m "api"
pytest tests/integration/ -m "database"
pytest tests/integration/ -m "redis"

# Run with coverage
pytest tests/integration/ --cov=app --cov-report=html
```

### Frontend Tests

```bash
# Run all integration tests
cd autonomica-frontend
npm run test:integration

# Run specific test patterns
node run_integration_tests.js "chat"
node run_integration_tests.js "authentication"

# Run with Jest directly
npm run test:integration:coverage
```

### Worker Tests

```bash
# Run worker integration tests
cd autonomica-worker
pytest tests/integration/ -v --cov=.

# Run specific worker test types
pytest tests/integration/ -k "web_scraping"
pytest tests/integration/ -k "ai_processing"
```

## Test Configuration

### Backend Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=70

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    api: API endpoint tests
    database: Database tests
    redis: Redis tests
    slow: Slow running tests
```

### Frontend Configuration

```javascript
// jest.integration.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{js,jsx,ts,tsx}'
  ],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/*.test.{js,jsx,ts,tsx}'
  ],
  coverageThreshold: {
    global: {
      branches: 60,
      functions: 60,
      lines: 60,
      statements: 60
    }
  }
}
```

## Test Fixtures and Mocks

### Backend Fixtures

```python
@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_redis():
    """Mock Redis connection for testing."""
    with patch('redis.Redis') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        # Configure mock behavior
        yield mock_instance

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user_123",
        "email": "test@example.com",
        "name": "Test User"
    }
```

### Frontend Fixtures

```typescript
// test-utils.tsx
export const createMockUser = (overrides = {}) => ({
  id: 'user_123',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  ...overrides,
})

export const createMockApiResponse = <T>(data: T, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async (): Promise<T> => data,
  text: async (): Promise<string> => JSON.stringify(data),
})
```

## Mock Service Worker (MSW)

### API Mocking

```typescript
// Setup MSW server
const server = setupServer(
  rest.post('/api/chat', (req, res, ctx) => {
    return res(
      ctx.json({
        content: 'This is a test AI response',
        role: 'assistant',
        timestamp: new Date().toISOString()
      })
    )
  }),
  
  rest.get('/api/agents', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 'agent_1',
          name: 'Strategy Agent',
          type: 'strategy',
          status: 'idle'
        }
      ])
    )
  })
)
```

## Test Data Management

### Test Database

```python
@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    # Create test database schema
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    shutil.rmtree(temp_dir)
```

### Test Data Factories

```python
def create_test_user(user_id="user_123", **overrides):
    """Create a test user with default values."""
    user_data = {
        "id": user_id,
        "email": f"test{user_id}@example.com",
        "name": f"Test User {user_id}",
        "created_at": "2024-01-01T00:00:00Z"
    }
    user_data.update(overrides)
    return user_data

def create_test_agent(agent_id="agent_123", **overrides):
    """Create a test agent with default values."""
    agent_data = {
        "id": agent_id,
        "name": f"Test Agent {agent_id}",
        "type": "strategy",
        "description": "A test agent",
        "model": "gpt-4",
        "status": "idle"
    }
    agent_data.update(overrides)
    return agent_data
```

## Performance Testing

### Load Testing

```python
def test_concurrent_requests(self, test_client, mock_clerk, mock_redis):
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
```

### Large Payload Testing

```python
def test_large_payload_handling(self, test_client, mock_clerk, mock_redis):
    """Test API behavior with large payloads."""
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
    assert response.status_code in [200, 413, 500]
```

## Error Handling Tests

### API Error Scenarios

```python
def test_redis_connection_failure(self, test_client, mock_clerk):
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

def test_openai_api_failure(self, test_client, mock_clerk, mock_redis):
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
```

## Coverage Requirements

### Backend Coverage
- **Minimum Coverage**: 70%
- **Critical Paths**: 90%
- **API Endpoints**: 100%
- **Error Handling**: 80%

### Frontend Coverage
- **Minimum Coverage**: 60%
- **Component Logic**: 80%
- **User Interactions**: 70%
- **API Integration**: 90%

## Continuous Integration

### GitHub Actions Integration

```yaml
# .github/workflows/ci-cd-pipeline.yml
integration:
  name: Integration Tests
  runs-on: ubuntu-latest
  needs: [frontend, backend, worker]
  
  services:
    redis:
      image: redis:7-alpine
      ports:
        - 6379:6379
      options: >-
        --health-cmd "redis-cli ping"
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
        
  steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        cache: 'pip'
        
    - name: Install dependencies
      run: |
        cd autonomica-api
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio httpx
        
    - name: Run integration tests
      run: |
        cd autonomica-api
        python run_integration_tests.py
```

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fresh fixtures for each test
- Clean up test data after each test
- Avoid shared state between tests

### 2. Mocking Strategy
- Mock external services and APIs
- Use realistic mock data
- Test both success and failure scenarios
- Verify mock interactions

### 3. Test Data Management
- Use factories for test data creation
- Keep test data minimal and focused
- Use meaningful test data values
- Clean up test data after tests

### 4. Error Testing
- Test all error scenarios
- Verify error messages and status codes
- Test edge cases and boundary conditions
- Ensure graceful degradation

### 5. Performance Considerations
- Test with realistic data sizes
- Verify response times under load
- Test concurrent request handling
- Monitor resource usage during tests

## Troubleshooting

### Common Issues

1. **Redis Connection Failures**
   - Ensure Redis server is running
   - Check Redis connection configuration
   - Verify Redis port and authentication

2. **Database Connection Issues**
   - Check database URL configuration
   - Verify database permissions
   - Ensure database is accessible

3. **Mock Service Worker Issues**
   - Verify MSW server setup
   - Check request/response handlers
   - Ensure proper cleanup between tests

4. **Test Environment Issues**
   - Verify environment variables
   - Check Python/Node.js versions
   - Ensure all dependencies are installed

### Debug Commands

```bash
# Backend debugging
pytest tests/integration/ -v -s --pdb

# Frontend debugging
npm run test:integration -- --verbose --no-coverage

# Worker debugging
pytest tests/integration/ -v -s -k "worker"
```

## Future Enhancements

### Planned Improvements

1. **Visual Regression Testing**
   - Screenshot comparison testing
   - UI component visual testing
   - Cross-browser compatibility testing

2. **Performance Benchmarking**
   - Automated performance testing
   - Load testing integration
   - Performance regression detection

3. **Security Testing**
   - Automated security scanning
   - Vulnerability testing
   - Penetration testing integration

4. **API Contract Testing**
   - OpenAPI specification validation
   - Contract testing with external services
   - API version compatibility testing

## Conclusion

The integration testing framework provides comprehensive coverage of component interactions, API integrations, and system behavior. By following the established patterns and best practices, developers can ensure reliable and maintainable tests that validate the system's functionality across all layers.

For questions or issues with the integration testing framework, please refer to the troubleshooting section or contact the development team.