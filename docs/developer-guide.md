# Developer Onboarding Guide

> Welcome to the Emotional Wellness API development team! This guide will help you set up your development environment, understand the codebase structure, and follow our development workflow.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourorg/emotional-wellness-api.git
cd emotional-wellness-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your local settings

# Start development services (Redis, etc.)
docker-compose up -d

# Run database migrations
alembic upgrade head

# Start the development server
python -m src.main
```

Visit http://localhost:8000/docs to see the API documentation.

## Development Environment

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Redis
- PostgreSQL
- Git

### Environment Configuration

The application uses dotenv for configuration. Key environment variables include:

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://localhost/wellness` | Yes |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` | Yes |
| `SECRET_KEY` | JWT signing key | None | Yes |
| `DEBUG` | Enable debug mode | `False` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `ENABLE_FEATURE_FLAGS` | Enable feature flag system | `True` | No |

### IDE Setup

#### VSCode Configuration

We recommend using VSCode with the following extensions:
- Python
- Pylance
- Python Test Explorer
- Python Docstring Generator
- ENV

Recommended settings (`.vscode/settings.json`):

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.nosetestsEnabled": false,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "tests"
  ]
}
```

## Project Structure

```
emotional-wellness-api/
├── src/                      # Application source code
│   ├── api/                  # API layer
│   │   ├── middleware/       # FastAPI middleware components
│   │   ├── routers/          # API route definitions
│   │   └── models/           # Pydantic models
│   ├── symbolic/             # Symbolic analysis modules
│   │   ├── canopy/           # Canopy processing system
│   │   ├── root/             # Root analysis module
│   │   ├── veluria/          # Crisis protocol
│   │   └── grove/            # Pattern matching
│   ├── integration/          # Integration components
│   │   └── enhanced_security.py  # Security integration
│   ├── security/             # Security components
│   │   └── phi_encryption.py # PHI encryption
│   ├── structured_logging/   # Logging infrastructure
│   │   └── phi_logger.py     # PHI access logger
│   ├── utils/                # Utility functions
│   │   └── hipaa.py          # HIPAA compliance utilities
│   └── main.py               # Application entry point
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test fixtures
├── docs/                     # Documentation
├── alembic/                  # Database migrations
├── scripts/                  # Utility scripts
├── .env.example              # Example environment variables
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
└── docker-compose.yml        # Development services
```

## Key Concepts

### Symbolic Processing Pipeline

The core of the Emotional Wellness API is the symbolic processing pipeline:

1. **Input**: Emotional state data enters the system
2. **Canopy Processing**: Initial analysis and metaphor extraction
3. **Root Analysis**: Longitudinal pattern recognition
4. **Veluria Crisis Protocol**: Crisis detection and response
5. **Response Generation**: Insights and recommendations

### HIPAA Compliance

As a healthcare application, HIPAA compliance is critical:

- All PHI data must be encrypted (see `security/phi_encryption.py`)
- All PHI access must be logged (see `structured_logging/phi_logger.py`)
- Authentication and authorization are enforced for all operations
- Security anomalies are detected and logged

### Enhanced Security Integration

The `integration/enhanced_security.py` module provides decorators and middleware for:

- Redis-based pattern caching
- Batched PHI access logging
- Vectorized crisis detection
- Circuit breaker pattern
- Feature flags integration

Example usage:

```python
from integration.enhanced_security import cache_pattern, circuit_breaker

@cache_pattern(ttl_seconds=300)
@circuit_breaker(name="user_profile")
async def get_user_profile(user_id: str):
    # Function implementation
    pass
```

## Development Workflow

### Git Workflow

We follow a GitHub Flow workflow:

1. Create a feature branch from `main`: `git checkout -b feature/your-feature-name`
2. Make changes and commit regularly: `git commit -am "Meaningful commit message"`
3. Push your branch: `git push -u origin feature/your-feature-name`
4. Create a Pull Request (PR) in GitHub
5. Address review feedback
6. Merge to `main` when approved

### Coding Standards

We follow these coding standards:

- **PEP 8** for Python style
- **Black** for code formatting
- **Pylint** for static analysis
- **Type hints** for all function parameters and return values
- **Comprehensive docstrings** using Google style

Example:

```python
def encrypt_phi_field(data: str, context: dict) -> str:
    """
    Encrypt a field containing PHI data.
    
    Args:
        data: The PHI data to encrypt
        context: Additional context about the encryption operation
        
    Returns:
        The encrypted data as a string
        
    Raises:
        EncryptionError: If encryption fails
    """
    # Implementation
```

### Testing

We use pytest for testing. All code should include:

- Unit tests for individual functions
- Integration tests for component interactions
- Security tests for HIPAA compliance

Run tests with:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_phi_encryption.py
```

### Pull Request Guidelines

Each PR should include:

1. **Description**: What changes does this PR introduce?
2. **Why**: What is the purpose of these changes?
3. **How**: Brief explanation of implementation approach
4. **Testing**: How the changes were tested
5. **Screenshots**: For UI changes (if applicable)

### CI/CD Pipeline

Our CI/CD pipeline consists of:

1. **Build**: Verify the code builds successfully
2. **Lint**: Check code quality with Pylint and Flake8
3. **Test**: Run unit and integration tests
4. **Security Scan**: Check for security vulnerabilities
5. **Deploy**: Deploy to development/staging environments

## Advanced Topics

### Feature Flags

The application uses feature flags for gradual feature rollout:

```python
from integration.enhanced_security import get_feature_flag_manager

async def process_with_feature_flag():
    ff_manager = await get_feature_flag_manager()
    
    if await ff_manager.is_enabled("new_analysis_algorithm"):
        # Use new algorithm
        return await process_with_new_algorithm()
    else:
        # Use existing algorithm
        return await process_with_existing_algorithm()
```

### Anomaly Detection

The security system includes anomaly detection for PHI access:

```python
from integration.enhanced_security import get_anomaly_detector

async def check_for_anomalies(user_id: str, access_pattern: dict):
    detector = await get_anomaly_detector()
    is_anomaly = await detector.check_access_pattern(
        user_id=user_id,
        pattern=access_pattern
    )
    
    if is_anomaly:
        await alert_security_team(user_id, access_pattern)
```

### Circuit Breaker Pattern

Use circuit breakers to prevent cascading failures:

```python
from integration.enhanced_security import circuit_breaker

@circuit_breaker(
    name="external_api", 
    failure_threshold=5,
    timeout_seconds=30
)
async def call_external_api(data: dict) -> dict:
    # Implementation that calls external API
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Redis connection errors | Check Redis is running with `docker-compose ps` |
| Database migration failures | Check database connection and migration history |
| JWT validation errors | Verify SECRET_KEY is properly set |
| PHI encryption errors | Ensure encryption keys are properly initialized |

### Debugging Tools

- Use `src/utils/debug.py` for advanced debugging helpers
- Check logs in `logs/application.log` for application events
- Use Redis CLI to inspect cache: `redis-cli -h localhost`

### Getting Help

If you need assistance:

1. Check the documentation in the `docs/` directory
2. Review existing issues in GitHub
3. Ask in the #dev-wellness-api Slack channel
4. Contact the team lead for urgent matters

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Redis Documentation](https://redis.io/documentation)
- [HIPAA Technical Safeguards](https://www.hhs.gov/hipaa/for-professionals/security/guidance/technical-safeguards/index.html)
