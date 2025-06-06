# Emotional Wellness API

A HIPAA-compliant emotional wellness companion API featuring advanced symbolic processing, rate limiting, and narrative intelligence.

## 🌟 Features

### Core Systems

- **🏛️ SYLVA-WREN Integration**: Advanced symbolic processing and narrative engine
- **🛡️ Enterprise Rate Limiting**: Zero-trust security with HIPAA compliance
- **🎭 CANOPY Metaphor Extraction**: AI-powered symbolic meaning analysis
- **🌳 ROOT Archetype Analysis**: Jungian archetype mapping and analysis
- **🍃 MOSS Crisis Detection**: Real-time safety assessment and intervention
- **💎 MARROW Safety Protocols**: Multi-layered emotional safety systems

### Advanced Capabilities

- **Zero-Trust Security**: Context-aware rate limiting with trust assessment
- **Business Intelligence**: Revenue impact analysis and customer journey mapping
- **Observability 2.0**: SLI/SLO management with abuse pattern detection
- **Claude 3 Haiku Integration**: Advanced metaphor extraction with fallback systems
- **Redis Caching**: Distributed caching with HIPAA-compliant PHI protection
- **Real-time Monitoring**: OpenTelemetry tracing and Prometheus metrics

## 🏗️ Architecture

### SYLVA Adapter System

The SYLVA (Symbolic Language and Visualization Architecture) adapter system provides a standardized interface for symbolic processing:

```
src/symbolic/adapters/
├── base.py              # Abstract base adapter with caching & error handling
├── canopy_adapter.py    # Metaphor extraction adapter  
├── root_adapter.py      # Archetype analysis adapter
├── moss_adapter.py      # Crisis detection adapter
├── marrow_adapter.py    # Safety protocol adapter
└── factory.py           # Adapter factory pattern
```

### Enhanced CANOPY System

Advanced metaphor extraction with multiple processing layers:

```
src/symbolic/canopy/
├── metaphor_extraction.py  # Enhanced extraction with Claude 3 Haiku
├── prompt_templates.py     # Structured LLM prompts
├── fallback_system.py      # Rule-based fallback extraction
└── caching.py             # Redis-based distributed caching
```

### Rate Limiting Architecture

Enterprise-grade rate limiting with zero-trust security:

```
src/api/middleware/
├── rate_limiter.py           # Core rate limiting middleware
├── zero_trust_security.py    # Zero-trust assessment system
├── business_intelligence.py  # BI analytics and journey mapping
├── observability_2.py        # Advanced observability and monitoring
└── multi_tenancy.py          # Multi-tenant support
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Redis 6.0+
- PostgreSQL 13+ (for production)
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/emotional-wellness-api.git
   cd emotional-wellness-api
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   alembic upgrade head
   ```

6. **Start the API**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 🔧 Configuration

### Environment Variables

```env
# API Configuration
DEBUG=true
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=postgresql://user:password@localhost/emotional_wellness

# Redis
REDIS_URL=redis://localhost:6379/0

# External Services
ANTHROPIC_API_KEY=your-anthropic-key

# HIPAA Compliance
ENCRYPTION_KEY=your-encryption-key
AUDIT_LOG_LEVEL=INFO
```

### Rate Limiting Configuration

```python
RATE_LIMITS = {
    "PHI_OPERATION": {"auth": 100, "unauth": 10, "window": 3600},
    "CRISIS_INTERVENTION": {"auth": 1000, "unauth": 50, "window": 3600},
    "AUTHENTICATED": {"auth": 500, "unauth": 100, "window": 3600},
    "PUBLIC": {"auth": 200, "unauth": 50, "window": 3600}
}
```

## 📖 API Documentation

### CANOPY Metaphor Extraction

```python
POST /api/v1/symbolic/extract
{
    "text": "I feel like I'm drowning in responsibilities",
    "context": {
        "session_type": "therapy",
        "previous_symbols": ["water", "ocean"]
    }
}
```

Response:
```json
{
    "primary_symbol": "water",
    "archetype": "self",
    "alternative_symbols": ["ocean", "current", "depth"],
    "valence": -0.6,
    "arousal": 0.8,
    "metaphors": [
        {
            "text": "drowning",
            "symbol": "overwhelm",
            "confidence": 0.9
        }
    ],
    "confidence": 0.85
}
```

### Zero-Trust Security Assessment

The system automatically evaluates trust based on:

- **Device Context**: Known devices, security status, fingerprinting
- **Location Context**: Geographic validation, VPN detection, approved facilities
- **Behavioral Context**: Usage patterns, anomaly detection, symbolic evolution
- **Authentication Context**: MFA status, role verification, session security

## 🏥 HIPAA Compliance

### Data Protection

- **Encryption at Rest**: AES-256 encryption for all PHI
- **Encryption in Transit**: TLS 1.3 for all API communications  
- **Access Controls**: Role-based access with zero-trust principles
- **Audit Logging**: Comprehensive audit trails for all PHI access
- **Data Minimization**: PHI hashing and anonymization where possible

### Crisis Intervention

Special handling for mental health emergencies:

- **Zero Rate Limiting**: Crisis counselors get unlimited access during emergencies
- **Priority Routing**: Crisis endpoints bypass normal queuing
- **Safety Escalation**: Automatic escalation for detected safety concerns
- **Audit Compliance**: Enhanced logging for crisis interventions

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m "unit"
pytest -m "integration"
pytest -m "hipaa_compliance"
```

## 📊 Monitoring

### Health Checks

- `GET /health` - Basic health check
- `GET /health/detailed` - Comprehensive system status
- `GET /health/adapters` - SYLVA adapter status

### Metrics

- **Prometheus**: `/metrics` endpoint for monitoring
- **Custom Metrics**: Symbolic processing, rate limiting, security events
- **Business Intelligence**: Revenue impact, user journey analytics

### Observability

- **OpenTelemetry**: Distributed tracing across all components
- **Structured Logging**: HIPAA-compliant logging with correlation IDs
- **Real-time Dashboards**: Grafana dashboards for operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Standards

- **Code Quality**: Black formatting, flake8 linting, type hints
- **Testing**: 85%+ test coverage required
- **Documentation**: Comprehensive docstrings and API documentation
- **HIPAA Compliance**: All changes must maintain HIPAA compliance

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security

For security concerns, please email security@example.com instead of using the issue tracker.

## 🙏 Acknowledgments

- **Anthropic Claude 3 Haiku** for advanced language processing
- **FastAPI** for the robust web framework
- **Redis** for distributed caching and rate limiting
- **OpenTelemetry** for observability infrastructure

---

## 🚧 Development Status

### ✅ Completed
- SYLVA Adapter System (base, CANOPY adapter)
- Enhanced CANOPY Metaphor Extraction
- Zero-Trust Rate Limiting
- Business Intelligence Analytics
- Advanced Observability System

### 🔄 In Progress
- ROOT Archetype Analysis Adapter
- MOSS Crisis Detection Adapter
- MARROW Safety Protocol Adapter
- WREN Narrative Engine
- Comprehensive Test Suite

### 📋 Planned
- Cultural Symbolic Libraries
- Narrative Memory Persistence
- Scene State Transition Logic
- Multi-language Support
- Mobile SDK

---

Built with ❤️ for emotional wellness and mental health support.
