# Emotional Wellness API

**AI-Powered Emotional Health Analytics and Support Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103.1-green.svg)](https://fastapi.tiangolo.com/)

## Overview

Emotional Wellness API is a comprehensive backend platform for emotional health analysis, monitoring, and support. Leveraging advanced AI systems, natural language processing, and psychological models, it provides tools for emotion tracking, crisis detection, and personalized intervention suggestions.

### Mission Statement
To improve mental and emotional wellness through accessible, scalable, and privacy-focused AI-powered support systems.

### Vision Statement
A world where everyone has access to effective, personalized emotional support and early intervention resources through ethically-developed AI systems.

## Features

### 🎯 **Core Functionality**
- **Emotional State Analysis**: Detection and tracking of emotional states from text
- **Crisis Monitoring**: Real-time detection of mental health risks and crisis indicators
- **Symbolic Processing**: Deep analysis of language patterns, metaphors, and archetypes
- **Intervention Suggestions**: Context-aware recommendations based on emotional patterns
- **Longitudinal Analysis**: Tracking emotional trends and patterns over time
- **Privacy-First Design**: PHI encryption and secure data handling

### 🔧 **Technical Architecture**
- **FastAPI Backend**: High-performance async API framework
- **Modular Design**: Specialized subsystems for different analysis domains
- **PostgreSQL Database**: Scalable, relational data storage
- **Redis Caching**: Performance optimization through caching
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Configurable request throttling and DDoS protection

### 🔍 **Key Subsystems**
- **MOSS**: Mental health crisis detection and safety protocol system
- **CANOPY**: Symbolic and metaphor analysis system
- **VELURIA**: State tracking and intervention recommendation system
- **ROOT**: Longitudinal trend analysis and pattern recognition system
- **SYLVA-WREN**: Multimodal support functionality system

## Installation

### Prerequisites
- Python 3.10 or higher
- PostgreSQL database
- Redis (optional, for caching)
- Virtual environment (recommended)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/emotional-wellness-api.git
   cd emotional-wellness-api
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root with the following variables:
   ```
   # API settings
   API_KEY=your_api_key
   JWT_SECRET_KEY=your_jwt_secret
   PHI_ENCRYPTION_KEY=your_encryption_key
   
   # Database settings
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=emotionalwellness
   POSTGRES_HOST=localhost
   
   # External APIs (replace with your keys)
   ANTHROPIC_API_KEY=your_anthropic_key
   OPENAI_API_KEY=your_openai_key
   
   # Redis (optional)
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=
   REDIS_DB=0
   ```

5. **Start the API server**:
   ```bash
   # For development with auto-reload
   cd src
   uvicorn main:app --reload
   
   # Or use Gunicorn for production
   gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 src.main:app
   ```

## Usage

### API Endpoints

Once the server is running, you can access:

- API documentation: http://localhost:8000/docs
- Alternative documentation: http://localhost:8000/redoc

### Key Endpoints

1. **Authentication**:
   - `POST /auth/register`: Register a new user
   - `POST /auth/login`: Login and receive JWT token
   - `POST /auth/refresh`: Refresh authentication token

2. **Emotional State Analysis**:
   - `POST /emotional-state/analyze`: Analyze text for emotional content
   - `GET /emotional-state/{user_id}`: Get user's emotional state history
   - `POST /emotional-state/track`: Record a new emotional state entry

3. **Crisis Detection**:
   - `POST /safety/check`: Evaluate text for crisis indicators
   - `GET /safety/protocols`: Get intervention protocols

4. **Symbolic Analysis**:
   - `POST /symbolic/analyze`: Perform deep symbolic analysis of text
   - `GET /symbolic/archetypes`: Get archetypal patterns from user history

5. **User Management**:
   - `GET /users/profile`: Get user profile information
   - `PUT /users/profile`: Update user profile

### Example API Request

```python
import requests
import json

# Login to get access token
login_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "demo", "password": "password"}
)
token = login_response.json()["access_token"]

# Analyze text for emotional content
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "http://localhost:8000/emotional-state/analyze",
    headers=headers,
    json={
        "text": "I'm feeling overwhelmed with work lately, but I'm trying to stay positive.",
        "user_id": "user123"
    }
)

# Print the analysis results
print(json.dumps(response.json(), indent=2))
```

## Project Structure

```
/emotional-wellness-api
├── src/                  # Source code
│   ├── api/              # API modules
│   ├── auth/             # Authentication
│   ├── cache/            # Caching mechanisms
│   ├── config/           # Configuration settings
│   ├── database/         # Database models and connections
│   ├── middleware/       # API middleware components
│   ├── routers/          # API routes and endpoints
│   ├── schemas/          # Pydantic schemas/models
│   ├── symbolic/         # Symbolic analysis subsystems
│   │   ├── canopy/       # CANOPY metaphor analysis
│   │   ├── moss/         # MOSS crisis detection
│   │   ├── root/         # ROOT longitudinal analysis
│   │   └── veluria/      # VELURIA intervention system
│   ├── utils/            # Utility functions
│   └── main.py           # Application entry point
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── conftest.py       # Test configurations
├── alembic/              # Database migrations
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## Development Roadmap

### Current Status

- ✅ Core infrastructure and database schema complete
- ✅ Basic authentication and token management implemented
- ✅ Initial version of symbolic processing systems (MOSS, CANOPY, ROOT, VELURIA)
- ✅ Privacy and security features (PHI encryption, rate limiting)
- ✅ Demo client application for testing and demonstration

### Short-term Goals (Next 2-4 Weeks)

- 🔄 Complete full test suite (unit, integration, performance)
- 🔄 Fix remaining import and dependency issues
- 🔄 Complete database integration and optimization
- 🔄 Improve error handling and validation
- 🔄 Enhanced logging and monitoring

### Medium-term Goals (2-3 Months)

- 📅 Implement advanced analytics and trend detection
- 📅 Enhance intervention recommendation system
- 📅 Develop admin dashboard and monitoring tools
- 📅 Add multi-tenant support and isolation
- 📅 Implement comprehensive caching strategy

### Long-term Vision (6+ Months)

- 🔮 Clinical integration features
- 🔮 ML-based risk prediction models
- 🔮 Multi-modal input support (audio, visual)
- 🔮 Research partnerships and validation studies
- 🔮 Public API and developer platform

## Contributing

We welcome contributions to the Emotional Wellness API project! Here's how you can help:

### Getting Started

1. **Fork the repository and create your branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow the coding style and conventions
   - Write tests for new functionality
   - Update documentation as needed

3. **Run tests**:
   ```bash
   pytest
   ```

4. **Submit a pull request**:
   - Describe the changes you've made
   - Reference any related issues

### Contribution Guidelines

- **Code Style**: Follow PEP 8 for Python code
- **Documentation**: Update docs for any changed functionality
- **Testing**: Add tests for new features and fix broken tests
- **Commits**: Write clear, concise commit messages
- **Pull Requests**: Keep PRs focused on a single change

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- FastAPI framework for the API foundation
- PostgreSQL and SQLAlchemy for database functionality
- OpenAI and Anthropic for language model integration
- All contributors who have helped build and improve this project

   - Export your model

### Key Panels

#### **Conversation Simulator**
- Real-time chat interface for testing model responses
- Emotion control with 7 basic emotions + intensity slider
- Mock empathy scoring (to be replaced with neural scoring)
- Response analysis panel with metrics

#### **Dataset Hub**
- JSONL and CSV file import
- Dataset validation for empathy requirements
- Example editor with navigation
- Emotion tagging system
- Multi-threaded loading with progress tracking

#### **Training Panel**
- LoRA configuration interface
- Training hyperparameter controls
- Empathy-specific settings
- Live monitoring dashboard
- Training history tracking

## Architecture

### Project Structure
```
sylva-tune/
├── src/
│   ├── core/              # Business logic
│   │   ├── project_manager.py
│   │   └── ...
│   ├── gui/               # UI components
│   │   ├── panels/        # Main UI panels
│   │   ├── dialogs/       # Modal dialogs
│   │   └── utils/         # UI utilities
│   ├── data/              # Data processing
│   ├── training/          # Training modules
│   └── evaluation/        # Evaluation tools
├── data/                  # Sample datasets
├── docs/                  # Documentation
├── models/                # Trained models
├── exports/               # Exported models
├── tests/                 # Test suite
├── main.py               # Entry point
├── requirements.txt      # Dependencies
└── setup.py             # Package setup
```

### Design Patterns
- **MVC Pattern**: Clear separation of models, views, and controllers
- **Observer Pattern**: PyQt signals/slots for component communication
- **Worker Threads**: Non-blocking UI during long operations
- **Factory Pattern**: Project creation and configuration

## Development

### Setting Up Development Environment

1. **Clone and setup**:
   ```bash
   git clone https://github.com/sloppymo/sylva-tune.git
   cd sylva-tune
   python3 -m venv sylva-venv
   source sylva-venv/bin/activate
   pip install -r requirements-dev.txt
   ```

2. **Run tests**:
   ```bash
   pytest tests/
   ```

3. **Code formatting**:
   ```bash
   black src/
   isort src/
   ```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Write unit tests for new features

## Roadmap

### Phase 1 (Months 1-6) ✅
- Core fine-tuning functionality
- Basic bias detection
- Dataset management
- User interface development

### Phase 2 (Months 7-12) 🚧
- Advanced empathy training
- Enhanced bias detection
- Evaluation and visualization
- API development

### Phase 3 (Months 13-18) 📋
- Collaboration features
- Enterprise integrations
- Advanced analytics
- Mobile application

### Phase 4 (Months 19-24) 📋
- AI-powered insights
- Industry-specific templates
- Advanced security features
- International expansion

## Business Information

### Pricing
- **Free Tier**: Limited personal/educational use
- **Professional Plan**: $49/month for individual commercial use
- **Enterprise Plan**: $199/month for team/organizational use
- **Enterprise Plus**: Custom pricing for unlimited features

### Target Market
- **Research Institutions**: Universities, research labs, think tanks
- **AI Startups**: Companies building AI products
- **Enterprise Organizations**: Large companies implementing AI
- **Healthcare Providers**: Medical AI applications
- **Educational Institutions**: AI education and training

## Support

### Documentation
- [User Guide](docs/USER_GUIDE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

### Community
- [GitHub Issues](https://github.com/sloppymo/sylva-tune/issues)
- [Discussions](https://github.com/sloppymo/sylva-tune/discussions)
- [Wiki](https://github.com/sloppymo/sylva-tune/wiki)

### Contact
- **Email**: support@sylvatune.ai
- **Website**: https://sylvatune.ai
- **Twitter**: [@SylvaTune](https://twitter.com/SylvaTune)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built by Forest Within Therapeutic Services Professional Corporation
- Inspired by the need for ethical AI development
- Thanks to the open-source community for foundational tools

---

**SylvaTune** - Building empathetic AI with confidence.
