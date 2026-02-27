## Project Information
- **Project Name:** NPU Chat
- **Version:** 1.0.0

## Overview
NPU Chat is a web-based chat interface for LLM models running on RK3588 NPU hardware. It features a React/TypeScript frontend served by a Flask backend, with SQLite persistence via SQLAlchemy.

## Architecture
- **Backend:** Flask with blueprints (`chats`, `search`, `templates`), service layer, SQLAlchemy models
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS, built to `static/dist/`
- **API:** JSON:API specification, documented via Swagger/Flasgger
- **Database:** SQLite (stored in `data/chats.db`)

## How to Run

```bash
# Install dependencies
make install

# Development
cd frontend && npm run dev    # Frontend dev server on :5173
python3 npuchat.py            # Backend server on :1314

# Production
make build-frontend           # Build React app
python3 npuchat.py            # Serves from static/dist/
```

## How to Test

```bash
# All checks
make all

# Individual
make test                     # Python tests (pytest)
make test-frontend            # Frontend tests (Jest)
make lint                     # Python linting (ruff)
make lint-frontend            # Frontend linting (ESLint)
```

## Key Files
- `npuchat.py` - Flask app factory and entry point
- `models.py` - Chat, Message, Template database models
- `services.py` - ChatService, LLMService, TemplateService, NamingService
- `blueprints/` - API route handlers (chats, search, templates)
- `config.py` - Configuration loader (reads `settings.ini`)
- `frontend/src/` - React components and API client
