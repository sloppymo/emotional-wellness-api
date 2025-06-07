# 🚀 Quick Development Guide

> For when you just want to get stuff done without reading 800 lines of README

## Essential Commands

```bash
# Start development server (most common)
uvicorn src.main:app --reload

# Run tests  
pytest --cov=src

# Quick test (no coverage)
pytest -x

# Crisis tests only
pytest tests/test_crisis_compliance.py -v

# Start everything with Docker
docker-compose up -d

# Reset database (nuclear option)
alembic downgrade base && alembic upgrade head
```

## When Things Break

```bash
# Check logs
tail -f logs/app.log

# Test database connection
python -c "from src.config.settings import get_settings; print(get_settings().DATABASE_URL)"

# Test Redis connection  
redis-cli ping

# Check if services are running
docker-compose ps

# Restart everything
docker-compose down && docker-compose up -d
```

## Important URLs

- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8000/dashboard  
- **Health Check**: http://localhost:8000/health

## Quick Tests

```bash
# Test crisis detection
python -c "
import asyncio
from src.symbolic.crisis.vectorized_detector import VectorizedCrisisDetector
async def test():
    d = VectorizedCrisisDetector()
    r = await d.detect_crisis_patterns('I want to hurt myself')
    print(f'Crisis: {r.detected}, Severity: {r.severity}')
asyncio.run(test())
"

# Test auth system
curl -X GET http://localhost:8000/health

# Test with auth
curl -X POST http://localhost:8000/emotional-state \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "session_id": "test", "text": "I feel sad"}'
```

## Environment Setup

1. Copy `.env.example` to `.env`
2. Edit database/redis URLs if needed
3. Set `JWT_SECRET_KEY` and `API_KEY`
4. Run `alembic upgrade head`

## Common Issues

**Database connection fails**: Check PostgreSQL is running
**Redis connection fails**: Check Redis is running  
**Import errors**: Check virtual environment is activated
**Tests fail**: Check test database is set up
**CORS errors**: Check `ALLOWED_ORIGINS` in settings

## File Structure (The Important Stuff)

```
src/
├── main.py              # FastAPI app setup
├── routers/            # API endpoints
├── symbolic/           # The AI/crisis detection
├── security/           # Auth and encryption
├── models/             # Data structures
└── config/             # Settings

tests/
├── test_crisis_compliance.py  # The critical tests
└── unit/                      # Regular tests
```

## Pro Tips

- Use `pytest -x` to stop on first failure
- Use `--tb=short` for cleaner error output
- Check `test-report.html` for test results
- Crisis tests are in `test_crisis_compliance.py`
- Comments explain the weird stuff (look for "# basically" etc.)
- When in doubt, check the logs in `logs/` directory 