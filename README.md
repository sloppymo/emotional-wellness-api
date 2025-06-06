# Emotional Wellness API

A comprehensive FastAPI-based backend system for mental health and emotional wellness support, featuring clinical assessment, intervention management, real-time analytics, and an interactive clinical dashboard.

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
- **Historical Metrics Storage**: Efficient time-series storage and aggregation with Redis TimeSeries.
- **Advanced Filtering & Export**: UI and API support for aggregation, label-based filtering, custom date ranges, and CSV/JSON export.
- **Extensible**: Add new metrics, integrations, and alert rules with minimal code changes.

See [MONITORING.md](./MONITORING.md) for full documentation and operational details.

## 🚀 Quick Start

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

## 🔒 Security Features

- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Request rate limiting
- HIPAA-compliant audit logging
- Encrypted data at rest and in transit
- Input validation and sanitization
- SQL injection prevention
- XSS protection

## 🚀 Performance Features

- Async/await throughout
- Connection pooling for PostgreSQL
- Redis caching for frequently accessed data
- Background task processing for heavy computations
- Optimized database queries with proper indexing
- Horizontal scaling support

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions
- Add tests for new features
- Run `black` and `isort` before committing

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics
- Prometheus metrics available at `/metrics`
- Grafana dashboards for visualization
- Custom alerts for critical events

## 🐛 Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check PostgreSQL is running
   - Verify database credentials in `.env`
   - Ensure database exists

2. **Redis connection errors**
   - Check Redis is running
   - Verify Redis URL in `.env`

3. **Celery worker issues**
   - Ensure Redis is accessible
   - Check worker logs for errors
   - Verify task imports

See [Troubleshooting Guide](docs/troubleshooting.md) for more details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI team for the excellent framework
- Anthropic for Claude AI integration
- All contributors and testers

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/emotional-wellness-api/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/emotional-wellness-api/discussions)

---

Built with ❤️ for mental health support
