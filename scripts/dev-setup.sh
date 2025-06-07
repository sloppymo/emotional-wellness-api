#!/bin/bash
# Development setup script for Emotional Wellness API
# Run this once to get everything working

set -e  # exit on any error

echo "🏥 Emotional Wellness API - Development Setup"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher required. Found: $python_version"
    exit 1
fi
echo "✅ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-test.txt

# Check if .env exists
echo "⚙️  Checking configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
        echo "⚠️  Please edit .env with your configuration"
    else
        echo "❌ Warning: No .env file found. You'll need to create one."
    fi
else
    echo "✅ .env file exists"
fi

# Check for Docker
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker found"
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose found"
        
        # Start background services
        echo "🚀 Starting background services..."
        docker-compose up -d postgres redis
        
        # Wait a moment for services to start
        echo "⏳ Waiting for services to initialize..."
        sleep 5
        
    else
        echo "⚠️  Docker Compose not found. You'll need to start PostgreSQL and Redis manually."
    fi
else
    echo "⚠️  Docker not found. You'll need to install PostgreSQL and Redis manually."
fi

# Run database migrations
echo "🗄️  Setting up database..."
if alembic upgrade head; then
    echo "✅ Database migrations complete"
else
    echo "⚠️  Database migrations failed. Check your database connection."
fi

# Run a quick test
echo "🧪 Running quick health check..."
if python -c "from src.config.settings import get_settings; get_settings()"; then
    echo "✅ Configuration loaded successfully"
else
    echo "❌ Configuration error. Check your .env file."
fi

# Create useful directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p tmp
echo "✅ Directories created"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run 'make dev' to start the development server"
echo "3. Visit http://localhost:8000/docs for API documentation"
echo "4. Visit http://localhost:8000/dashboard for the clinical dashboard"
echo ""
echo "Quick commands:"
echo "  make dev          - Start development server"
echo "  make test         - Run tests"
echo "  make docker-up    - Start with Docker"
echo "  make help         - See all available commands"
echo ""
echo "Happy coding! 🚀" 