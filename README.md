# Emotional Wellness API

[![Alpha Status](https://img.shields.io/badge/status-alpha-red.svg)](https://github.com/yourusername/emotional-wellness-api)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> A FastAPI-based platform for mental health and emotional wellness, featuring crisis detection (VELURIA), longitudinal analytics (ROOT), clinical assessment, intervention management, and interactive monitoring dashboards.

<p align="center">
  <img src="./assets/dashboard_preview.png" alt="Emotional Wellness API Dashboard" width="80%"/>
</p>

> **⚠️ IMPORTANT: ALPHA STAGE SOFTWARE**  
> This project is in early alpha stage development and **NOT READY FOR PRODUCTION USE**. Many features are incomplete, untested in real-world scenarios, or may change significantly. Do not use with sensitive patient data or in clinical settings until a stable release is available.

## 📖 Overview

The Emotional Wellness API is a backend system being developed for mental health practitioners, crisis responders, and wellness applications. It aims to combine clinical expertise with machine learning to provide risk assessment, intervention protocols, and analytics.

- **Under Active Development**: Regular updates and feature additions
- **Analytics Prototypes**: Early implementations of crisis detection and trend analysis algorithms
- **Security Focus**: Working toward HIPAA compliance with ongoing development of security features
- **Dashboard Prototypes**: Early versions of clinical insights and system monitoring visualizations
- **Developer Preview**: API structure and documentation evolving based on feedback

## 🌟 Key Features

### Core Functionality
- **Clinical Assessment Engine**: Advanced risk assessment with ML-based analysis
- **Intervention Management**: Protocol-based intervention system with state tracking
- **Crisis Response**: Automated escalation and emergency protocols
- **User Management**: Secure authentication with role-based access control

### Advanced Features (v2.0)
- **Background Task Processing**: Celery-based distributed task queue for analytics
- **Clinical Dashboard**: Interactive web interface for clinicians with real-time visualizations
- **Longitudinal Monitoring**: Track patient wellness trajectories over time
- **Early Warning System**: AI-powered detection of deteriorating mental health patterns
- **Real-time Updates**: WebSocket support for live notifications and updates

### Technical Features
- **HIPAA Compliant**: Full audit logging and data encryption
- **Scalable Architecture**: Async FastAPI with PostgreSQL and Redis
- **Comprehensive Testing**: Unit, integration, and workflow tests
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Error Handling**: Consistent error responses with request tracking

## 🚨 Monitoring & Admin Dashboard

The Emotional Wellness API includes a robust, extensible monitoring and admin dashboard system for real-time and historical observability:

- **Admin Dashboard UI**: Secure, role-based dashboards for system health, alerts, metrics, background tasks, and integrations.
- **Metrics & Alerts APIs**: REST endpoints for listing, filtering, and exporting all system metrics and alerts.

See [MONITORING.md](./MONITORING.md) for full documentation and operational details.

## 🧵 Quick Start (Developer Preview)

> **Warning**: This alpha version is for development and testing only. Do not use in production.

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/emotional-wellness-api.git
cd emotional-wellness-api
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run database migrations**
```bash
alembic upgrade head
```

6. **Start services**
```bash
# Start Redis
redis-server

# Start Celery worker (in a new terminal)
celery -A src.tasks.celery_app worker --loglevel=info

# Start Celery beat (in a new terminal)
celery -A src.tasks.celery_app beat --loglevel=info

# Start the API
uvicorn src.main:app --reload
```

### Docker Deployment

```bash
docker-compose up -d
```

## 📊 Clinical Dashboard

Access the clinical dashboard at `http://localhost:8000/dashboard` after starting the server.

### Dashboard Features
- **Crisis Trends**: Real-time visualization of crisis events and patterns
- **Risk Stratification**: Patient cohort analysis by risk levels
- **Wellness Trajectories**: Individual and cohort wellness tracking
- **Intervention Outcomes**: Effectiveness metrics and protocol performance
- **Early Warnings**: Automated alerts for at-risk patients

### Dashboard Requirements
- Modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- Clinician or admin role authorization

## 🔧 API Usage

### Authentication

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "securepassword"}'
```

### Submit Assessment

```bash
curl -X POST http://localhost:8000/api/v1/assessments/submit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_responses": {
      "mood": 3,
      "anxiety": 7,
      "sleep_quality": 4,
      "stress_level": 8
    }
  }'
```

### Trigger Background Analysis

```bash
# Start crisis trend analysis
curl -X POST http://localhost:8000/api/v1/tasks/analyze/crisis-trends \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"period": "weekly"}'

# Check task status
curl -X GET http://localhost:8000/api/v1/tasks/status/TASK_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/test_veluria/
```

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Dashboard Guide**: See `docs/dashboard_guide.md`
- **Development Guide**: See `docs/development.md`
- **Deployment Guide**: See `docs/deployment.md`

## 🏗️ Architecture

```
src/
├── api/              # API endpoints and routers
├── clinical/         # Clinical domain logic
├── dashboard/        # Web dashboard interface
├── database/         # Database models and sessions
├── middleware/       # FastAPI middleware
├── models/           # SQLAlchemy models
├── security/         # Authentication and authorization
├── symbolic/         # VELURIA protocol system
├── tasks/            # Background task definitions
└── main.py          # Application entry point
```

## 🧠 Analytics Systems (Prototype Stage)

### VELURIA: Crisis Detection & Intervention

<p align="center">
  <img src="./assets/veluria_flow.png" alt="VELURIA System Flow" width="70%"/>
</p>

VELURIA is our advanced crisis pattern detection and intervention system, featuring:

- **Real-time Risk Assessment**: Multi-dimensional analysis across 8 domains (suicide, self-harm, violence, substance abuse, trauma, eating disorders, neglect, psychosis)
- **Machine Learning Models**: Uses IsolationForest for anomaly detection
- **Temporal Pattern Analysis**: Identifies patterns in emotional state over time
- **Intervention Protocol Management**: Dynamic selection of appropriate interventions based on crisis type and severity
- **Effectiveness Analytics**: Measures and reports on intervention outcomes

```python
# Example: Using the VELURIA API for crisis assessment
from src.symbolic.veluria import CrisisPatternDetector

async def detect_patterns(user_id, emotional_states):
    detector = CrisisPatternDetector()
    result = await detector.analyze_patterns(
        user_id=user_id,
        emotional_states=emotional_states,
        timeframe_days=30
    )
    
    # Get risk prediction
    if result.risk_prediction.risk_level >= 3:  # High risk
        # Trigger intervention protocol
        await intervention_service.trigger_protocol(
            user_id=user_id, 
            risk_assessment=result
        )
```

### ROOT: Longitudinal Analytics

ROOT is our longitudinal analysis system that tracks emotional wellness over time:

- **Emotional Baseline Calculation**: Establishes user-specific baselines
- **Trend Analysis**: Identifies meaningful changes and trajectories
- **Pattern Recognition**: Discovers recurring patterns in emotional states
- **Predictive Analytics**: Forecasts potential future states using RandomForestRegressor
- **Correlation Analysis**: Finds relationships between wellness factors

```python
# Example: Using ROOT for longitudinal analysis
from src.symbolic.root import ROOTAnalyzer

async def analyze_trends(user_id, start_date, end_date):
    analyzer = ROOTAnalyzer()
    
    # Calculate baseline and trends
    baseline = await analyzer.calculate_baseline(user_id, days=90)
    trends = await analyzer.analyze_trends(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        baseline=baseline
    )
    
    # Generate forecast
    forecast = await analyzer.forecast_state(
        user_id=user_id,
        days_ahead=14,
        trends=trends
    )
    
    return {
        "baseline": baseline,
        "trends": trends,
        "forecast": forecast
    }
```

### CANOPY: Metaphor Extraction & Symbolic Mapping

CANOPY provides metaphor analysis and symbolic mapping capabilities:

- **Metaphor Extraction**: Identifies underlying metaphors in user expressions
- **Cultural Adaptation**: Maps metaphors to culturally appropriate responses
- **Symbolic Integration**: Connects metaphorical expressions to clinical concepts
- **Multi-lingual Support**: Works across multiple languages and cultures

## 🏢 Architecture (Evolving Design)

### System Architecture

<p align="center">
  <img src="./assets/architecture.png" alt="Planned System Architecture" width="80%"/>
</p>

The Emotional Wellness API is being designed with the following architecture (subject to change during development):

- **FastAPI Backend**: Asynchronous API with dependency injection and middleware
- **Domain-Driven Design**: Separated domains for clinical, symbolic, and monitoring concerns
- **CQRS Pattern**: Command and Query Responsibility Segregation for complex operations
- **Event-Driven**: Pub/sub patterns for system events and notifications
- **Microservices-Ready**: Modular design that can be deployed as monolith or microservices

### Data Flow

1. **Input Processing**: User emotional states and clinical inputs are processed through API endpoints
2. **Risk Assessment**: VELURIA analyzes inputs for crisis patterns and risk levels
3. **Intervention Selection**: Protocol selection based on assessment results
4. **Longitudinal Storage**: Data stored for ROOT analysis with appropriate retention policies
5. **Analytics & Visualization**: Results presented through dashboards and API responses

### Component Structure

```
src/
├── api/             # API layer with versioning and endpoints
├── clinical/        # Clinical domain logic and assessment
│   ├── analytics.py  # Clinical analytics capabilities
│   └── service.py    # Core clinical services
├── dashboard/       # Web dashboards for admin and clinical views
│   ├── admin/        # Admin dashboard components
│   └── clinical/     # Clinical dashboard components
├── integrations/    # External system integrations
├── middleware/      # Request/response processing
├── models/          # Data models and schemas
├── monitoring/      # System monitoring and observability
│   ├── metrics_storage.py  # Time-series metrics storage
│   └── metrics_collector.py # Metrics collection service
├── security/        # Security, auth, and compliance
├── services/        # Application services
├── symbolic/        # Symbolic processing subsystems
│   ├── canopy/       # Metaphor extraction system
│   ├── moss/         # Core symbolic processing
│   ├── root/         # Longitudinal analytics
│   └── veluria/      # Crisis detection and intervention
├── tasks/           # Background task processing
└── utils/           # Shared utilities
```

## 🔒 Security Features (In Development)

> **Note**: Security features are under active development and have not undergone formal security audits or penetration testing.

### Authentication & Authorization (Prototype)

- **JWT Authentication**: Secure, short-lived access tokens with refresh capability
- **Role-Based Access Control**: Fine-grained permissions by clinical, admin, and user roles
- **Multi-factor Authentication**: SMS or authenticator app support (optional)
- **Password Security**: Argon2id hashing with adaptive parameters and policy enforcement
- **Session Management**: Secure, short-lived sessions with automatic expiration

### Data Protection (Planned)

- **PHI Protection**: Working toward HIPAA compliance with data redaction and anonymization
- **Encryption**: Implementing AES-256 for data at rest, TLS 1.3 for data in transit
- **Database Security**: Planning column-level encryption for sensitive fields
- **Audit Logging**: Developing comprehensive audit trail capabilities

```python
# Example: Using the secure PHI logger
from src.structured_logging.phi_logger import PHILogger

async def access_patient_data(user_id, patient_id, reason):
    # Audit logging for PHI access
    await PHILogger.log_access(
        actor_id=user_id,
        subject_id=patient_id,
        data_category="clinical_records",
        action="view",
        reason=reason
    )
    
    # Rest of the function...
```

### Network & Infrastructure

- **Web Security Headers**:
  - Content-Security-Policy (CSP)
  - X-XSS-Protection
  - Strict-Transport-Security (HSTS)
  - X-Content-Type-Options
- **Rate Limiting**: Protection against brute force and DDoS attacks
- **Input Validation**: Pydantic models and validation for all inputs
- **SQL Injection Protection**: Parameterized queries and ORM usage
- **CORS Protection**: Strict origin policies
- **Vulnerability Scanning**: Integrated security scanner in CI/CD pipeline

### Compliance (Roadmap)

- **HIPAA Compliance**: Working toward technical safeguards for PHI
- **Audit Trails**: Developing logging systems for access tracking
- **Risk Assessment**: Planning security assessment procedures
- **Incident Response**: Drafting protocols for security incidents

## 📈 Monitoring & Observability (Early Development)

The Emotional Wellness API is developing a monitoring and observability stack:

### Metrics & Dashboards

- **Admin Dashboard**: Secure, role-based web UI for all monitoring needs
- **Real-time Metrics**: System resources, API usage, integration health
- **Historical Metrics**: Redis TimeSeries storage with multiple retention policies
- **Advanced Filtering**: Label-based, time range, and aggregation filtering
- **Export Options**: CSV, JSON, and visualization formats

```python
# Example: Accessing metrics via API
import httpx

async def get_system_metrics(token, start_time, end_time):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/metrics/system/resources",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "aggregation": "hourly"
            }
        )
        return response.json()
```

### Alerting

- **Alert Rules**: Configurable thresholds for system, API, and integration metrics
- **Notification Channels**: Email, SMS, Slack, and webhooks
- **Alert Lifecycle**: Acknowledgment, resolution, and silencing workflow
- **Alert History**: Historical view of past alerts and resolution times

### Logging

- **Structured Logging**: JSON-formatted logs with consistent schema
- **Log Levels**: Configurable verbosity by component
- **Log Aggregation**: Compatible with ELK, Graylog, and other aggregators
- **PHI Protection**: Automatic redaction in logs for compliance

For comprehensive details on monitoring and observability, see [MONITORING.md](./MONITORING.md).

## 🛠️ Deployment Planning

> **Important**: The deployment architecture described below is aspirational and not yet fully implemented or tested.

### Future Deployment Architecture

<p align="center">
  <img src="./assets/deployment_architecture.png" alt="Production Architecture" width="80%"/>
</p>

### Planned Cloud Deployment (AWS)

```bash
# Note: Terraform scripts are under development and not yet functional
# cd terraform/aws
# terraform init
# terraform apply
```

Future production deployments are planned to use containerization:

- **Docker Containers**: Separate containers for API, workers, and Redis
- **Kubernetes**: Orchestration for scaling and resilience
- **Auto-scaling**: Dynamic scaling based on load
- **Load Balancing**: Distributed traffic handling
- **Secret Management**: Secure handling of credentials
- **Database**: Managed PostgreSQL with high availability
- **Caching**: Redis clusters with replication

### On-Premises Deployment

For healthcare organizations requiring on-premises deployment:

1. **Hardware Requirements**:
   - Minimum: 4 CPU cores, 8GB RAM, 100GB SSD
   - Recommended: 8+ CPU cores, 16GB+ RAM, 500GB+ SSD

2. **Network Configuration**:
   - Reverse proxy with HTTPS termination (nginx or HAProxy)
   - Internal network segmentation for database and Redis

3. **High Availability**:
   - Database replication
   - API load balancing
   - Redis sentinel or cluster

4. **Backup & Recovery**:
   - Automated database backups
   - Point-in-time recovery options
   - Disaster recovery procedures

### CI/CD Pipeline

The project includes GitLab CI/GitHub Actions workflows for:

- **Automated Testing**: Unit, integration, and end-to-end tests
- **Static Analysis**: Code quality and security scanning
- **Build & Package**: Docker image creation
- **Deployment**: Automated deployment to staging/production
- **Post-Deployment Verification**: Health checks and smoke tests

## 👩‍💻 Contributing to this Alpha Project

We welcome contributions to the Emotional Wellness API during its alpha development! Here's how to get involved:

### Development Setup

1. **Fork the repository** and clone it locally:

```bash
git clone https://github.com/yourusername/emotional-wellness-api.git
cd emotional-wellness-api
```

2. **Set up a virtual environment**:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development tools
```

4. **Set up environment variables**:

```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run database migrations**:

```bash
alembic upgrade head
```

6. **Start Redis** (required for metrics, caching, and task queue):

```bash
redis-server
```

7. **Start the development server**:

```bash
uvicorn src.main:app --reload --port 8000
```

8. **Start Celery workers** (in a separate terminal):

```bash
celery -A src.tasks.celery_app worker --loglevel=info
```

### Code Standards

- Follow PEP 8 style guide
- Use type hints for all functions and methods
- Write docstrings for all modules, classes, and functions
- Maintain test coverage (minimum 85%)
- Use async/await patterns for I/O operations

### Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Implement your changes with tests
3. Update documentation as needed
4. Run the linters: `black src tests && isort src tests && flake8 src tests`
5. Run tests: `pytest --cov=src`
6. Submit a pull request with a clear description

## 🧪 Testing (In Progress)

> **Note**: Test coverage is incomplete and under active development. Many components still require comprehensive test suites.

### Running Tests

Run the full test suite:

```bash
pytest --cov=src --cov-report=term-missing
```

Run specific test categories:

```bash
# Unit tests only
pytest tests/unit

# Integration tests only
pytest tests/integration

# Specific test file
pytest tests/unit/test_veluria.py

# With verbose output
pytest -v tests/unit
```

### Test Coverage

Generate a coverage report:

```bash
pytest --cov=src --cov-report=html
# View the report in ./htmlcov/index.html
```

### Test Structure

```
tests/
├── conftest.py                # Shared fixtures
├── unit/                      # Fast, isolated tests
│   ├── api/                   # API endpoint tests
│   ├── clinical/              # Clinical domain tests
│   ├── monitoring/            # Monitoring tests
│   └── symbolic/              # Symbolic subsystem tests
├── integration/               # Tests with dependencies
│   ├── database/              # Database integration
│   ├── redis/                 # Redis integration
│   └── external/              # External API integration
└── fixtures/                  # Test data
```

## 📈 Monitoring

The Emotional Wellness API provides comprehensive monitoring capabilities:

### Health Check

Verify system health status:

```bash
curl http://localhost:8000/health
```

### Metrics

- **System Metrics**: CPU, memory, disk usage via Redis TimeSeries
- **API Metrics**: Request rates, response times, error rates
- **Business Metrics**: User activity, risk assessments, interventions triggered

### Dashboards

- **Admin Dashboard**: Available at `/admin/dashboard`
- **Metrics Dashboard**: Available at `/admin/metrics`
- **Alerts Dashboard**: Available at `/admin/alerts`

### Export Options

- CSV exports for offline analysis
- JSON exports for integration with other systems
- Visualization snapshots

For full details, see [MONITORING.md](./MONITORING.md).

## 🐛 Troubleshooting (Alpha Development)

> **Note**: As this is alpha software, you may encounter additional issues not listed here. Please report them via GitHub issues.

### Common Issues

#### API Startup Issues

**Problem**: API fails to start with database connection errors.

**Solution**: 
- Verify PostgreSQL is running and accessible
- Check connection string in `.env` file
- Ensure database migrations are applied: `alembic upgrade head`

#### Worker/Celery Issues

**Problem**: Background tasks not running or failing silently.

**Solution**:
- Check Redis connection
- Verify Celery worker is running: `celery -A src.tasks.celery_app worker --loglevel=info`
- Check Celery logs for errors

#### Dashboard Access Issues

**Problem**: Can't access admin dashboard.

**Solution**:
- Verify admin role is assigned to your user
- Check JWT token validity
- Ensure frontend assets are properly served

#### Redis TimeSeries Issues

**Problem**: Metrics not appearing in dashboard.

**Solution**:
- Verify Redis TimeSeries module is installed: `redis-cli MODULE LIST`
- Check Redis connection settings
- Verify metrics collector service is running

### Performance Tuning

- **API Performance**: Adjust worker count in `uvicorn` or Gunicorn for concurrent requests
- **Database**: Add indexes for frequently queried fields
- **Caching**: Configure Redis caching for frequently accessed, read-heavy data
- **Task Queue**: Adjust Celery concurrency with `--concurrency=N`

### FAQ

**Q: Can the system handle multiple languages?**

A: Yes, CANOPY supports multilingual metaphor extraction and cultural adaptation.

**Q: What machine learning models are used?**

A: We use IsolationForest for anomaly detection, RandomForestRegressor for predictive analytics, and custom models for risk assessment.

**Q: Is the system suitable for clinical trials?**

A: While designed with clinical best practices, specific trial validation may be required depending on your research protocol.

**Q: How do I add a new metric to monitor?**

A: Use the `MetricsCollector` service to define and track new metrics. See [MONITORING.md](./MONITORING.md) for details.

```python
from src.monitoring.metrics_collector import MetricsCollector

# Register and track a new metric
await MetricsCollector.track_metric(
    name="user_engagement_score",
    value=85.2,
    labels={"user_type": "clinician", "feature": "dashboard"}
)
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

The Emotional Wellness API builds upon the work of many open-source projects and research in mental health technology:

- FastAPI for the web framework
- PostgreSQL and SQLAlchemy for data storage
- Redis for caching, time-series, and task queue
- Scikit-learn for machine learning components
- Plotly and Chart.js for visualizations
- Clinical advisors who provided domain expertise

Special thanks to:
- The mental health professionals who provided domain expertise during development
- The open-source community for their invaluable contributions
- Our early adopters and testers for their feedback
- All contributors and maintainers of the project

## 📞 Alpha Support

For support with this alpha version of the Emotional Wellness API:

- **GitHub Issues**: Please report bugs, request features, or ask questions via GitHub issues
- **Documentation**: Reference the docs directory, though please note documentation is still being developed
- **Development Updates**: Watch the GitHub repository for updates on development progress

This is an alpha project and not yet ready for enterprise deployments or HIPAA-compliant implementations.

---

## 🏞️ Land Acknowledgement

We respectfully acknowledge that the work on this project takes place on the traditional, ancestral, and unceded territory of the Kumeyaay/Diegueño/Ipai/Tipai peoples, who have stewarded these lands since time immemorial. We recognize their continuing connection to the land, waters, and community, and pay our respects to Kumeyaay elders past, present, and emerging. We commit to building relationships of reciprocity with the Indigenous peoples of this territory and supporting the ongoing work of Indigenous sovereignty.

---

<p align="center">
  <strong>Emotional Wellness API</strong><br>
  <em>Alpha Development Version</em><br>
  Built with ❤️ for mental health support<br>
  <a href="https://github.com/yourusername/emotional-wellness-api/stargazers">⭐ Star us on GitHub</a>
</p>
