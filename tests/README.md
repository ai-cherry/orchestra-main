# Orchestra AI - Testing Configuration

## Test Dependencies

```bash
# Install Python testing dependencies
pip install pytest pytest-asyncio pytest-cov httpx playwright

# Install Node.js testing dependencies (for frontend)
cd web
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest

# Install k6 for performance testing (Ubuntu/Debian)
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

## Running Tests

### Unit Tests
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ -v --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_authentication.py -v
```

### Integration Tests
```bash
# Start the application first
uvicorn main_api:app --host 0.0.0.0 --port 8000

# Run integration tests (in another terminal)
pytest tests/integration/ -v --asyncio-mode=auto
```

### Performance Tests
```bash
# Run load test
k6 run tests/performance/load-test.js

# Run with custom configuration
k6 run --vus 50 --duration 5m tests/performance/load-test.js
```

### Frontend Tests
```bash
cd web
npm run test:unit
npm run test:e2e
```

## Test Configuration

### Environment Variables for Testing
```bash
export DATABASE_URL="postgresql://postgres:test_password@localhost:5432/orchestra_test"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET_KEY="test-secret-key"
export LAMBDA_LABS_API_KEY="test-key"
```

### Test Database Setup
```bash
# Create test database
createdb orchestra_test

# Run migrations (if any)
# python manage.py migrate
```

## Continuous Integration

The GitHub Actions workflow automatically runs:
1. Security scans (Bandit, Safety, Semgrep)
2. Code quality checks (flake8, mypy)
3. Unit tests with coverage
4. Integration tests
5. Performance tests (post-deployment)

## Test Coverage Goals

- **Unit Tests**: >90% code coverage
- **Integration Tests**: All API endpoints covered
- **Performance Tests**: Response times <2s for 95% of requests
- **Security Tests**: No high/critical vulnerabilities

## Writing New Tests

### Unit Test Example
```python
import pytest
from your_module import your_function

def test_your_function():
    result = your_function("input")
    assert result == "expected_output"
```

### Integration Test Example
```python
import pytest
import httpx

async def test_api_endpoint():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/endpoint")
        assert response.status_code == 200
```

### Performance Test Example
```javascript
import http from 'k6/http';
import { check } from 'k6';

export default function() {
  let response = http.get('http://localhost:8000/api/endpoint');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

