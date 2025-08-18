# Integration Testing Framework

## Overview
This document provides comprehensive information about the integration testing framework for the Autonomica project, covering both backend API integration tests and frontend component integration tests.

## What is Integration Testing?

Integration testing verifies that different components of the system work together correctly. Unlike unit tests that test individual functions in isolation, integration tests test the interaction between:

- **Backend**: API endpoints, database operations, external service integrations
- **Frontend**: Component interactions, state management, API calls
- **Cross-system**: Frontend-backend communication, data flow, error handling

## Backend Integration Testing

### Test Structure

```
autonomica-api/tests/integration/
├── __init__.py
├── test_api_integration.py      # Main API integration tests
├── test_database_integration.py # Database integration tests
├── test_external_services.py    # External API integration tests
└── test_workflow_integration.py # End-to-end workflow tests
```

### Key Test Categories

#### 1. API Endpoint Integration
Tests the interaction between different API endpoints and their dependencies:

```python
@pytest.mark.integration
def test_agent_workflow_integration(self, test_client, test_agents):
    """Test complete agent workflow from creation to execution."""
    # 1. Get available agents
    response = test_client.get("/api/agents")
    assert response.status_code == 200
    
    # 2. Select agents for a task
    response = test_client.post("/api/workforce/select-agents", json=task_data)
    assert response.status_code == 200
    
    # 3. Execute task with selected agents
    response = test_client.post("/api/workforce/run-agents", json=execution_data)
    assert response.status_code == 200
```

#### 2. Database Integration
Tests database operations and data consistency:

```python
@pytest.mark.integration
def test_data_consistency_integration(self, test_client, test_agents):
    """Test data consistency across different API endpoints."""
    # Get agents from different endpoints
    response1 = test_client.get("/api/agents")
    response2 = test_client.get("/api/agents/my-agents")
    
    # Verify consistency
    agents1 = response1.json()
    agents2 = response2.json()
    assert len(agents1) == len(agents2)
```

#### 3. External Service Integration
Tests integration with third-party services:

```python
@pytest.mark.integration
def test_seo_pipeline_integration(self, test_client):
    """Test SEO pipeline integration with multiple services."""
    # Submit URL for analysis
    response = test_client.post("/api/seo/analyze", json=url_data)
    analysis_id = response.json()["analysis_id"]
    
    # Get analysis results
    response = test_client.get(f"/api/seo/score/{analysis_id}")
    assert response.status_code == 200
```

#### 4. Workflow Integration
Tests complete end-to-end workflows:

```python
@pytest.mark.integration
def test_workflow_end_to_end(test_client, test_agents):
    """Test complete end-to-end workflow."""
    # 1. Create task
    # 2. Select agents
    # 3. Execute task
    # 4. Monitor progress
    # 5. Get results
    # 6. Verify consistency
```

### Test Fixtures

#### Database Fixtures
```python
@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
```

#### Test Data Fixtures
```python
@pytest.fixture
def test_agents(db_session):
    """Create test agents in the database."""
    agents = [
        Agent(id="agent_1", name="Strategy Specialist", ...),
        Agent(id="agent_2", name="Content Creator", ...),
        Agent(id="agent_3", name="Analytics Expert", ...),
    ]
    
    for agent in agents:
        db_session.add(agent)
    db_session.commit()
    
    return agents
```

#### Test Client Fixtures
```python
@pytest.fixture
def test_client(db_session, test_user):
    """Create a test client with database and authentication."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()
```

### Running Backend Integration Tests

```bash
# Run all integration tests
cd autonomica-api
pytest -m integration

# Run specific integration test file
pytest tests/integration/test_api_integration.py

# Run with coverage
pytest -m integration --cov=. --cov-report=html

# Run with verbose output
pytest -m integration -v -s
```

## Frontend Integration Testing

### Test Structure

```
autonomica-frontend/src/
├── components/
│   ├── __tests__/
│   │   ├── ChatContainerAI.test.tsx           # Unit tests
│   │   ├── Dashboard.integration.test.tsx     # Integration tests
│   │   └── ...
│   └── ...
└── test-utils/
    └── integration-test-setup.ts              # Integration test utilities
```

### Key Test Categories

#### 1. Component Integration
Tests how different components work together:

```typescript
describe('Component Integration', () => {
  it('renders all dashboard components and integrates them properly', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    )

    // Check that all main sections are rendered
    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText('Active Agents')).toBeInTheDocument()
    expect(screen.getByText('Recent Projects')).toBeInTheDocument()
  })
})
```

#### 2. User Interaction Integration
Tests user interactions across components:

```typescript
describe('User Interaction Integration', () => {
  it('integrates quick actions with other dashboard components', async () => {
    // Test quick action buttons
    const createProjectButton = screen.getByText('Create Project')
    const addAgentButton = screen.getByText('Add Agent')
    
    // Test button interactions
    fireEvent.click(createProjectButton)
    fireEvent.click(addAgentButton)
  })
})
```

#### 3. Data Flow Integration
Tests data consistency and state management:

```typescript
describe('Data Flow Integration', () => {
  it('maintains data consistency across component updates', async () => {
    // Simulate data update
    const updatedAgents = mockAgents.map(agent => 
      agent.id === 'agent_1' 
        ? { ...agent, status: 'busy' }
        : agent
    )
    
    // Verify update is reflected
    await waitFor(() => {
      expect(screen.getByText('busy')).toBeInTheDocument()
    })
  })
})
```

### Test Utilities

#### Integration Test Setup
```typescript
// test-utils/integration-test-setup.ts
export function setupIntegrationTest() {
  // Mock external dependencies
  jest.mock('@/lib/api', () => ({
    fetchApi: jest.fn(),
    postApi: jest.fn(),
    putApi: jest.fn(),
    deleteApi: jest.fn(),
  }))

  // Setup global mocks
  global.fetch = jest.fn()
  global.localStorage = mockLocalStorage
  global.sessionStorage = mockSessionStorage
}
```

#### Custom Render Function
```typescript
export function renderWithProviders(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <UserProvider>
        <AgentProvider>
          <ProjectProvider>
            <NotificationProvider>
              <DashboardProvider>
                {children}
              </DashboardProvider>
            </NotificationProvider>
          </ProjectProvider>
        </AgentProvider>
      </UserProvider>
    )
  }

  return render(ui, { wrapper: Wrapper, ...options })
}
```

#### Mock Data
```typescript
export const mockTestData = {
  agents: [
    {
      id: 'agent_1',
      name: 'Strategy Specialist',
      type: 'STRATEGY',
      status: 'idle',
      is_active: true,
    },
    // ... more agents
  ],
  projects: [
    {
      id: 'project_1',
      name: 'Marketing Campaign 2025',
      status: 'active',
      progress: 75,
    },
    // ... more projects
  ],
  // ... more data
}
```

### Running Frontend Integration Tests

```bash
# Run all tests (including integration)
cd autonomica-frontend
npm test

# Run only integration tests
npm test -- --testNamePattern="Integration"

# Run specific integration test file
npm test -- Dashboard.integration.test.tsx

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

## Integration Test Best Practices

### 1. Test Realistic Scenarios
Test actual user workflows and business processes:

```python
# Good: Test complete user journey
def test_user_creates_project_and_assigns_agents():
    # 1. User creates project
    # 2. System suggests agents
    # 3. User assigns agents
    # 4. System validates assignment
    # 5. Project is created with agents

# Avoid: Testing implementation details
def test_internal_function_calls():
    # Don't test private methods or internal state
```

### 2. Use Realistic Test Data
Create test data that mirrors production scenarios:

```typescript
// Good: Realistic test data
const mockUser = {
  id: 'user_123',
  email: 'test@example.com',
  firstName: 'John',
  lastName: 'Doe',
  role: 'marketing_manager',
  permissions: ['create_project', 'assign_agents', 'view_analytics']
}

// Avoid: Minimal test data
const mockUser = { id: '1', name: 'Test' }
```

### 3. Test Error Scenarios
Verify system behavior under failure conditions:

```python
def test_error_handling_integration(self, test_client):
    """Test error handling across different API components."""
    # Test invalid input
    invalid_task = {"task": "", "agent_types": ["INVALID_TYPE"]}
    response = test_client.post("/api/workforce/select-agents", json=invalid_task)
    assert response.status_code == 422
    
    # Test non-existent resources
    response = test_client.get("/api/agents/non_existent_id")
    assert response.status_code == 404
```

### 4. Test Performance Under Load
Verify system behavior with concurrent operations:

```python
def test_concurrent_operations_integration(self, test_client, test_agents):
    """Test concurrent operations and resource management."""
    import threading
    
    results = []
    errors = []
    
    def make_request(request_type, data):
        try:
            if request_type == "get_agents":
                response = test_client.get("/api/agents")
            elif request_type == "select_agents":
                response = test_client.post("/api/workforce/select-agents", json=data)
            
            results.append((request_type, response.status_code))
        except Exception as e:
            errors.append((request_type, str(e)))
    
    # Create multiple threads for concurrent requests
    threads = []
    for i in range(4):
        threads.append(threading.Thread(
            target=make_request, 
            args=(f"request_{i}", {"task": f"Task {i}"})
        ))
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    # Verify all requests completed successfully
    assert len(results) == 4
    assert len(errors) == 0
```

### 5. Test Data Consistency
Ensure data remains consistent across operations:

```typescript
it('maintains data consistency across component updates', async () => {
  // Get initial data
  const initialAgents = screen.getAllByText(/Agent/i)
  expect(initialAgents).toHaveLength(3)
  
  // Update agent status
  fireEvent.click(screen.getByText('Strategy Specialist'))
  
  // Verify update is reflected everywhere
  await waitFor(() => {
    const updatedAgent = screen.getByText('Strategy Specialist')
    expect(updatedAgent).toHaveTextContent('busy')
  })
  
  // Verify other components show updated data
  const projectList = screen.getByText('Recent Projects')
  expect(projectList).toHaveTextContent('Strategy Specialist (busy)')
})
```

## Integration Test Configuration

### Backend Configuration

#### Pytest Configuration
```ini
# pytest.ini
[tool:pytest]
markers =
    integration: Integration tests (slower, external dependencies)
    unit: Unit tests (fast, isolated)
    e2e: End-to-end tests (slowest, full system)
    slow: Tests that take longer than 5 seconds

addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
    --durations=10
```

#### Test Database Configuration
```python
# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocreate=False, autoflush=False, bind=engine)
```

### Frontend Configuration

#### Jest Configuration
```javascript
// jest.config.js
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jsdom',
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{test,spec}.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{js,jsx,ts,tsx}',
  ],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
}
```

#### Test Environment Setup
```typescript
// jest.setup.js
import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: {},
      asPath: '/',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn().mockResolvedValue(undefined),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
      isFallback: false,
    }
  },
}))

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = 'test_key'
```

## Continuous Integration

### GitHub Actions Integration

#### Backend Integration Tests
```yaml
# .github/workflows/ci-cd-pipeline.yml
- name: Test backend
  run: |
    cd autonomica-api
    pytest --cov=. --cov-report=xml --cov-report=html

- name: Run integration tests
  run: |
    cd autonomica-api
    pytest -m integration --cov=. --cov-report=xml
```

#### Frontend Integration Tests
```yaml
- name: Test frontend
  run: |
    cd autonomica-frontend
    npm test -- --ci --coverage --watchAll=false

- name: Run integration tests
  run: |
    cd autonomica-frontend
    npm test -- --testNamePattern="Integration" --ci
```

### Coverage Reporting

#### Codecov Integration
```yaml
- name: Upload coverage reports
  uses: codecov/codecov-action@v3
  with:
    file: |
      autonomica-api/coverage.xml
      autonomica-frontend/coverage/lcov.info
    flags: |
      backend
      frontend
    name: integration-test-coverage
```

## Monitoring and Maintenance

### Test Performance Monitoring

#### Execution Time Tracking
```bash
# Run tests with timing information
pytest -m integration --durations=10

# Frontend test timing
npm test -- --verbose --no-coverage
```

#### Coverage Tracking
```bash
# Generate coverage reports
pytest -m integration --cov=. --cov-report=html
npm test -- --coverage

# View coverage reports
open autonomica-api/htmlcov/index.html
open autonomica-frontend/coverage/lcov-report/index.html
```

### Regular Maintenance

#### Test Data Updates
- Update mock data to match schema changes
- Refresh test scenarios for new features
- Remove obsolete test cases

#### Performance Optimization
- Identify slow tests and optimize
- Parallelize independent tests
- Cache test data where appropriate

#### Documentation Updates
- Keep test documentation current
- Document new test patterns
- Update troubleshooting guides

## Troubleshooting

### Common Issues

#### 1. Test Environment Problems
```bash
# Clear test cache
pytest --cache-clear

# Reset test database
pytest --reset-db

# Run with debug output
pytest -v -s --tb=long
```

#### 2. Mock Configuration Issues
```typescript
// Ensure mocks are properly configured
beforeEach(() => {
  jest.clearAllMocks()
  jest.resetAllMocks()
})

// Check mock implementations
expect(mockApi.fetchApi).toHaveBeenCalledWith('/api/agents')
```

#### 3. Async Test Issues
```typescript
// Use proper async/await patterns
it('handles async operations', async () => {
  const result = await asyncOperation()
  expect(result).toBeDefined()
})

// Use waitFor for dynamic content
await waitFor(() => {
  expect(screen.getByText('Updated Content')).toBeInTheDocument()
})
```

### Debugging Integration Tests

#### Backend Debugging
```python
# Add debug output
import logging
logging.basicConfig(level=logging.DEBUG)

# Use pytest-sugar for better output
pytest -v -s --tb=long --capture=no
```

#### Frontend Debugging
```typescript
// Add console logs for debugging
console.log('Component rendered:', screen.debug())

// Use React Testing Library debug
screen.debug()

// Check for specific elements
expect(screen.queryByText('Error')).not.toBeInTheDocument()
```

## Future Enhancements

### Planned Improvements

1. **Visual Regression Testing**: Screenshot comparison testing
2. **Contract Testing**: API contract validation
3. **Load Testing**: Automated performance testing
4. **Mutation Testing**: Code quality validation
5. **Test Parallelization**: Faster test execution

### Integration Opportunities

1. **SonarQube**: Code quality and test coverage analysis
2. **TestRail**: Test case management and reporting
3. **Allure**: Advanced test reporting and analytics
4. **Playwright**: End-to-end browser testing

## Resources and References

### Documentation
- [Pytest Integration Testing](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [React Testing Library Integration](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest Integration Testing](https://jestjs.io/docs/tutorial-async)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

### Community
- [Pytest Community](https://pytest.org/latest/community.html)
- [Testing Library Community](https://testing-library.com/docs/community)
- [Jest Community](https://jestjs.io/community)

### Tools
- [Pytest Plugins](https://pytest.org/latest/plugins.html)
- [Jest Ecosystem](https://jestjs.io/docs/ecosystem)
- [Coverage Tools](https://coverage.readthedocs.io/en/latest/cmd.html)
