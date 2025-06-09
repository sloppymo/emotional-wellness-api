# SylvaTune

**Empathy-Focused LLM Fine-Tuning Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)](https://pypi.org/project/PyQt6/)

## Overview

SylvaTune is an empathy-focused LLM fine-tuning platform that addresses the growing need for responsible AI development. Our platform provides tools for bias detection, ethical training, and empathetic model development, targeting researchers, developers, and organizations building AI systems.

### Mission Statement
To democratize ethical AI development by providing accessible tools for creating empathetic, unbiased, and responsible language models.

### Vision Statement
A world where all AI systems are developed with empathy, fairness, and ethical considerations at their core.

## Features

### 🎯 **Core Functionality**
- **Dataset Management**: Import, validate, and prepare training data
- **Bias Detection**: Advanced bias scanning and analysis
- **Empathy Training**: Specialized training for empathetic responses
- **Model Evaluation**: Comprehensive evaluation metrics
- **Visualization**: Interactive charts and analysis tools
- **Project Management**: Collaborative project workflows

### 🖥️ **User Interface**
- **Modern PyQt6 GUI**: Cross-platform desktop application
- **Three-panel Layout**: Draggable/resizable sections
- **Multiple Themes**: Light, Dark, and Blue themes
- **Tabbed Interface**: Organized workflows for different tasks

### 🔧 **Technical Features**
- **Modular Design**: Extensible architecture for new features
- **Multi-Framework Support**: Hugging Face and OpenAI integration
- **Cloud Integration**: Seamless cloud service integration
- **API Support**: RESTful API for automation and integration

## Installation

### Prerequisites
- Python 3.8 or higher
- PyQt6
- Virtual environment (recommended)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sloppymo/sylva-tune.git
   cd sylva-tune
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv sylva-venv
   source sylva-venv/bin/activate  # On Windows: sylva-venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application**:
   ```bash
   python main.py
   ```

## Usage

### Getting Started

1. **Create a New Project**:
   - Launch SylvaTune
   - Click "New Project" or File → New Project
   - Enter project details and select base model
   - Choose your preferred framework (Hugging Face/OpenAI)

2. **Import Your Dataset**:
   - Use the Dataset Hub panel
   - Import JSONL or CSV files
   - Validate your data for empathy requirements
   - Tag emotions and review examples

3. **Configure Training**:
   - Set up LoRA parameters
   - Configure empathy-specific settings
   - Adjust hyperparameters
   - Save your configuration

4. **Train Your Model**:
   - Start training with live monitoring
   - Track empathy metrics
   - Monitor bias detection
   - Save checkpoints

5. **Evaluate Results**:
   - Test responses in conversation simulator
   - Analyze empathy scores
   - Review bias reports
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
