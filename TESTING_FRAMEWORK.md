# Testing Framework Documentation

## Overview
This document provides comprehensive information about the testing framework setup for the Autonomica project, covering both backend (Python) and frontend (React/Next.js) testing configurations.

## Backend Testing Framework (Python)

### Tools and Configuration

#### 1. Pytest Configuration (`autonomica-api/pytest.ini`)
- **Test Discovery**: Automatically finds tests in the `tests/` directory
- **Coverage**: Integrated coverage reporting with 80% threshold
- **Markers**: Custom markers for test categorization
- **Output**: Verbose output with color coding and duration reporting

#### 2. Coverage Configuration (`autonomica-api/.coveragerc`)
- **Source Coverage**: Measures coverage for the `app/` directory
- **Exclusions**: Excludes test files, migrations, and non-source code
- **Reports**: HTML, XML, and terminal coverage reports
- **Branch Coverage**: Enables branch coverage analysis

#### 3. Test Configuration (`autonomica-api/tests/conftest.py`)
- **Fixtures**: Common test fixtures for authentication, database, and mocking
- **Test Environment**: Proper test environment setup and teardown
- **Mocking**: Comprehensive mocking for external dependencies
- **Markers**: Automatic test categorization based on naming conventions

### Test Structure

```
autonomica-api/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test configuration and fixtures
│   ├── unit/                    # Unit tests (fast, isolated)
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   └── test_utils.py
│   ├── integration/             # Integration tests
│   │   ├── test_api_endpoints.py
│   │   ├── test_database.py
│   │   └── test_external_apis.py
│   ├── e2e/                    # End-to-end tests
│   │   └── test_full_workflow.py
│   └── performance/            # Performance tests
│       └── test_load.py
```

### Test Categories and Markers

#### Unit Tests (`@pytest.mark.unit`)
- **Purpose**: Test individual functions and methods in isolation
- **Speed**: Fast execution (< 100ms per test)
- **Dependencies**: No external dependencies, fully mocked
- **Example**: Testing a utility function or model validation

#### Integration Tests (`@pytest.mark.integration`)
- **Purpose**: Test component interactions and external integrations
- **Speed**: Medium execution (100ms - 1s per test)
- **Dependencies**: May use test databases or mocked external services
- **Example**: Testing API endpoints with database operations

#### End-to-End Tests (`@pytest.mark.e2e`)
- **Purpose**: Test complete user workflows
- **Speed**: Slow execution (1s - 10s per test)
- **Dependencies**: Full system setup, may use staging services
- **Example**: Testing complete user registration and login flow

#### Performance Tests (`@pytest.mark.performance`)
- **Purpose**: Test system performance and load handling
- **Speed**: Variable execution time
- **Dependencies**: Performance testing tools (Locust, pytest-benchmark)
- **Example**: Load testing API endpoints

### Running Tests

#### Basic Test Execution
```bash
# Run all tests
cd autonomica-api
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run tests with specific marker
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

#### Advanced Test Execution
```bash
# Run tests in parallel
pytest -n auto

# Run tests with specific Python version
pytest --python-version=3.11

# Generate coverage report
pytest --cov=. --cov-report=xml --cov-report=html

# Run tests with custom markers
pytest -m "unit and not slow"
pytest -m "api or auth"
```

### Test Fixtures

#### Authentication Fixtures
```python
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
def test_client(mock_auth_dependency) -> TestClient:
    """Test client with mocked authentication."""
    app.dependency_overrides[get_current_user] = mock_auth_dependency
    return TestClient(app)
```

#### Database Fixtures
```python
@pytest.fixture
def test_db():
    """Test database with sample data."""
    # Setup test database
    yield test_db
    # Cleanup after tests
```

#### Mock Fixtures
```python
@pytest.fixture
def mock_redis():
    """Mock Redis connection for testing."""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    return mock_redis
```

## Frontend Testing Framework (React/Next.js)

### Tools and Configuration

#### 1. Jest Configuration (`autonomica-frontend/jest.config.js`)
- **Test Environment**: jsdom for DOM testing
- **Coverage**: 80% threshold with HTML and LCOV reports
- **Transform**: Next.js Babel configuration
- **Module Mapping**: Path aliases and CSS module handling

#### 2. Jest Setup (`autonomica-frontend/jest.setup.js`)
- **Global Mocks**: Next.js router, fetch, and browser APIs
- **Test Utilities**: Common testing utilities and helpers
- **Environment Setup**: Test environment configuration
- **Cleanup**: Automatic test cleanup and mock reset

### Test Structure

```
autonomica-frontend/
├── src/
│   ├── components/
│   │   ├── __tests__/           # Component tests
│   │   │   ├── ChatContainerAI.test.tsx
│   │   │   ├── Dashboard.test.tsx
│   │   │   └── Navigation.test.tsx
│   │   └── ...
│   ├── hooks/
│   │   ├── __tests__/           # Hook tests
│   │   │   ├── useAuth.test.ts
│   │   │   └── useApi.test.ts
│   │   └── ...
│   ├── utils/
│   │   ├── __tests__/           # Utility tests
│   │   │   ├── formatters.test.ts
│   │   │   └── validators.test.ts
│   │   └── ...
│   └── pages/
│       ├── __tests__/           # Page tests
│       │   ├── index.test.tsx
│       │   └── dashboard.test.tsx
│       └── ...
```

### Test Categories

#### Component Tests
- **Purpose**: Test React component rendering and behavior
- **Coverage**: Props, state changes, user interactions
- **Tools**: React Testing Library, Jest DOM matchers
- **Example**: Testing button clicks, form submissions, conditional rendering

#### Hook Tests
- **Purpose**: Test custom React hooks
- **Coverage**: State changes, side effects, return values
- **Tools**: React Testing Library hooks testing utilities
- **Example**: Testing authentication state, API data fetching

#### Utility Tests
- **Purpose**: Test pure functions and utilities
- **Coverage**: Input/output validation, edge cases
- **Tools**: Jest assertions
- **Example**: Testing date formatting, data validation

### Running Tests

#### Basic Test Execution
```bash
# Run all tests
cd autonomica-frontend
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test -- ChatContainerAI.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="renders"
```

#### Advanced Test Execution
```bash
# Run tests in CI mode
npm test -- --ci --coverage --watchAll=false

# Run tests with verbose output
npm test -- --verbose

# Run tests with specific environment
npm test -- --env=jsdom

# Generate coverage report
npm test -- --coverage --coverageReporters=html
```

### Test Utilities

#### Global Test Utilities
```typescript
// Wait for element to be present
await testUtils.waitForElement('.chat-input', 5000)

// Mock API responses
testUtils.mockApiResponse('/api/chat', { message: 'Hello' }, 200)

// Create test user
const user = testUtils.createTestUser({ role: 'admin' })
```

#### React Testing Library Helpers
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

// Render component
render(<ChatContainerAI />)

// Find elements
const input = screen.getByPlaceholderText(/Ask me anything/i)
const button = screen.getByRole('button', { name: /send/i)

// Interact with elements
fireEvent.change(input, { target: { value: 'Hello' } })
fireEvent.click(button)

// Wait for changes
await waitFor(() => {
  expect(screen.getByText('Hello')).toBeInTheDocument()
})
```

## Test Data Management

### Test Data Factories
```python
# Backend test data factory
def create_test_agent(**overrides):
    """Create a test agent with default values."""
    defaults = {
        'id': 'test_agent_123',
        'name': 'Test Agent',
        'type': 'STRATEGY',
        'model': 'gpt-4',
        'status': 'idle',
        'user_id': 'test_user_123',
    }
    defaults.update(overrides)
    return Agent(**defaults)
```

```typescript
// Frontend test data factory
export const createTestUser = (overrides = {}) => ({
  id: 'test_user_123',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  imageUrl: 'https://example.com/avatar.jpg',
  ...overrides,
})
```

### Test Database Setup
```python
@pytest.fixture(scope="session")
def test_database():
    """Create test database with sample data."""
    # Setup test database
    engine = create_engine("sqlite:///./test.db")
    Base.metadata.create_all(bind=engine)
    
    # Insert sample data
    with Session(engine) as session:
        session.add_all(sample_agents)
        session.commit()
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
```

## Mocking and Stubbing

### Backend Mocking
```python
# Mock external API calls
@patch('app.services.openai_client.chat.completions.create')
def test_chat_completion(mock_openai):
    mock_openai.return_value = Mock(
        choices=[Mock(message=Mock(content="Test response"))]
    )
    
    result = chat_service.generate_response("Hello")
    assert result == "Test response"
```

### Frontend Mocking
```typescript
// Mock API calls
jest.mock('@/lib/api', () => ({
  fetchApi: jest.fn(),
}))

// Mock authentication
jest.mock('@clerk/nextjs', () => ({
  useAuth: () => ({
    isSignedIn: true,
    userId: 'test_user_123',
  }),
}))
```

## Coverage and Quality

### Coverage Thresholds
- **Backend**: 80% minimum coverage
- **Frontend**: 80% minimum coverage
- **Critical Paths**: 95% minimum coverage

### Quality Metrics
- **Test Execution Time**: Unit tests < 100ms, Integration < 1s
- **Test Reliability**: 99.9% pass rate
- **Code Coverage**: Maintain above thresholds
- **Test Maintenance**: Regular review and updates

### Coverage Reports
```bash
# Backend coverage
cd autonomica-api
pytest --cov=. --cov-report=html
# Open htmlcov/index.html

# Frontend coverage
cd autonomica-frontend
npm test -- --coverage
# Open coverage/lcov-report/index.html
```

## Continuous Integration

### GitHub Actions Integration
```yaml
# Backend testing
- name: Test backend
  run: |
    cd autonomica-api
    pytest --cov=. --cov-report=xml --cov-report=html

# Frontend testing
- name: Test frontend
  run: |
    cd autonomica-frontend
    npm test -- --ci --coverage --watchAll=false
```

### Coverage Upload
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
```

## Best Practices

### Test Writing Guidelines

#### 1. Test Structure (AAA Pattern)
```python
def test_user_creation():
    # Arrange
    user_data = {"email": "test@example.com", "name": "Test User"}
    
    # Act
    user = create_user(user_data)
    
    # Assert
    assert user.email == "test@example.com"
    assert user.name == "Test User"
```

#### 2. Descriptive Test Names
```python
# Good
def test_user_login_with_valid_credentials_returns_success()

# Bad
def test_login()
```

#### 3. Test Isolation
```python
@pytest.fixture(autouse=True)
def clean_database():
    """Clean database before each test."""
    yield
    # Cleanup after test
```

#### 4. Mock External Dependencies
```python
@patch('app.services.email_service.send_email')
def test_user_registration_sends_welcome_email(mock_send_email):
    # Test without actually sending emails
    pass
```

### Test Maintenance

#### 1. Regular Review
- Review test coverage monthly
- Update tests when requirements change
- Remove obsolete tests

#### 2. Performance Monitoring
- Monitor test execution time
- Identify slow tests
- Optimize test setup and teardown

#### 3. Documentation
- Keep test documentation updated
- Document complex test scenarios
- Maintain test data schemas

## Troubleshooting

### Common Issues

#### 1. Test Environment Issues
```bash
# Clear test cache
pytest --cache-clear

# Reset test database
pytest --reset-db

# Run with debug output
pytest -v --tb=long
```

#### 2. Coverage Issues
```bash
# Check coverage configuration
pytest --cov=. --cov-report=term-missing

# Generate detailed coverage report
pytest --cov=. --cov-report=html --cov-report=xml
```

#### 3. Mock Issues
```python
# Reset all mocks
@pytest.fixture(autouse=True)
def reset_mocks():
    yield
    Mock.reset_mock()
```

### Debugging Tests

#### 1. Interactive Debugging
```python
import pdb; pdb.set_trace()  # Python
debugger;                     # JavaScript
```

#### 2. Verbose Output
```bash
# Backend
pytest -v -s --tb=long

# Frontend
npm test -- --verbose --no-coverage
```

#### 3. Test Isolation
```bash
# Run single test
pytest tests/unit/test_models.py::test_user_creation

# Run with specific marker
pytest -m "unit and not slow"
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
- [Pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

### Community
- [Pytest Community](https://pytest.org/latest/community.html)
- [Testing Library Community](https://testing-library.com/docs/community)
- [Jest Community](https://jestjs.io/community)

### Tools
- [Pytest Plugins](https://pytest.org/latest/plugins.html)
- [Jest Ecosystem](https://jestjs.io/docs/ecosystem)
- [Coverage Tools](https://coverage.readthedocs.io/en/latest/cmd.html)
