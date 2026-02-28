# NPU-Chat Developer Guide

This guide covers everything you need to set up, develop, test, and deploy NPU-Chat.

## Prerequisites

- Python 3.11+
- Node.js 20+
- npm 9+
- Docker (optional, for containerized deployment)

## Quick Start

```bash
# 1. Clone and install
make install

# 2. Copy environment config
cp .env.example .env

# 3. Start the backend (serves on http://localhost:1314)
make run

# 4. In a separate terminal, start the frontend dev server
cd frontend && npm run dev
```

The Vite dev server runs on `http://localhost:5173` and proxies API requests to Flask on port 5000. For production, Flask serves the built frontend from `static/dist/`.

## Project Structure

```
NPU-Chat/
├── npuchat.py              # Flask application factory + entry point
├── config.py               # Environment-based configuration
├── models.py               # SQLAlchemy models (Chat, Message, Template)
├── services.py             # Business logic (ChatService, LLMService, etc.)
├── jsonapi.py              # JSON:API serialization, validation, pagination
├── schemas.py              # Pydantic request validation models
├── extensions.py           # Flask extension instances (rate limiter)
├── logging_config.py       # Structured JSON logging + correlation IDs
├── blueprints/
│   ├── health.py           # GET /api/health
│   ├── chats.py            # /api/v1/chats CRUD
│   ├── templates.py        # /api/v1/templates CRUD
│   └── search.py           # POST /api/v1/search (LLM queries)
├── migrations/             # Alembic database migrations
├── tests/                  # Backend tests (pytest)
├── frontend/
│   ├── src/
│   │   ├── main.tsx        # Entry point (ErrorBoundary + QueryClient)
│   │   ├── App.tsx         # Root component
│   │   ├── api.ts          # JSON:API client functions
│   │   ├── types.ts        # TypeScript interfaces
│   │   ├── hooks/          # TanStack Query hooks
│   │   ├── components/     # React components
│   │   └── __tests__/      # Frontend tests (Jest)
│   ├── vite.config.ts      # Build config + dev proxy
│   └── jest.config.js      # Test runner config
├── e2e/                    # Playwright end-to-end tests
├── Dockerfile              # Multi-stage production build
├── docker-compose.yml      # Container orchestration
└── .github/workflows/ci.yml # CI pipeline
```

## Configuration

All configuration uses environment variables with sensible defaults. Copy `.env.example` to `.env` and customize as needed.

| Variable | Default | Description |
|---|---|---|
| `BINDING_ADDRESS` | `0.0.0.0` | Host address for the web server |
| `BINDING_PORT` | `1314` | Port for the web server |
| `NPU_ADDRESS` | `192.168.0.196` | NPU/LLM server address |
| `NPU_PORT` | `31337` | NPU/LLM server port |
| `CONNECTION_TIMEOUT` | `45` | LLM request timeout in seconds |
| `USE_CONTEXT` | `True` | Enable multi-turn context |
| `CONTEXT_DEPTH` | `1` | Number of previous messages to retain (min 2 enforced) |
| `DATABASE_URL` | `sqlite:///data/chats.db` | Database connection string |
| `LOG_FORMAT` | `json` | Log format: `json` or `text` |
| `LOG_LEVEL` | `INFO` | Python log level |
| `RATELIMIT_DEFAULT` | `200 per day;50 per hour` | Global rate limit |
| `RATELIMIT_STORAGE_URI` | `memory://` | Rate limit backend |

For local development, set `LOG_FORMAT=text` for readable logs.

## Backend Development

### Running the Server

```bash
python3 npuchat.py
# or
make run
```

The server automatically runs database migrations on startup, creates the default template, and serves the built frontend.

### API Endpoints

All API responses use [JSON:API](https://jsonapi.org/) format with content type `application/vnd.api+json`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check (DB connectivity) |
| `GET` | `/api/v1/chats` | List chats (paginated) |
| `POST` | `/api/v1/chats` | Create chat |
| `GET` | `/api/v1/chats/:id` | Get chat |
| `PATCH` | `/api/v1/chats/:id` | Update chat |
| `DELETE` | `/api/v1/chats/:id` | Delete chat |
| `GET` | `/api/v1/chats/:id/messages` | List messages (paginated) |
| `GET` | `/api/v1/templates` | List templates (paginated) |
| `POST` | `/api/v1/templates` | Create template |
| `PATCH` | `/api/v1/templates/:id` | Update template |
| `DELETE` | `/api/v1/templates/:id` | Delete template |
| `POST` | `/api/v1/search` | Send message to LLM |

Legacy `/api/*` paths redirect to `/api/v1/*` with HTTP 308.

**Pagination** uses query params `page[number]` and `page[size]` (default 50, max 100). Responses include a `meta` object with `page`, `per_page`, `total`, and `pages`.

**Rate limiting**: The search endpoint is limited to 10 requests per minute.

**Swagger docs** are available at `/apidocs` when the server is running.

### Adding a New Endpoint

1. Create or edit a blueprint in `blueprints/`
2. Add a Pydantic schema to `schemas.py` if the endpoint accepts input
3. Use `validate_jsonapi_request(request, SchemaClass)` to validate
4. Use `serialize_resource()` / `serialize_collection()` for responses
5. Use `paginate_query()` for list endpoints
6. Register the blueprint in `npuchat.py` if it's new
7. Write tests in `tests/`

### Database Migrations

The project uses Flask-Migrate (Alembic) for schema changes.

```bash
# Create a new migration after modifying models.py
make db-migrate msg="add is_archived column to chats"

# Apply pending migrations
make db-upgrade

# Revert the last migration
make db-downgrade

# View migration history
make db-history
```

Migrations support both SQLite (local dev) and PostgreSQL (production). SQLite migrations use `render_as_batch=True` automatically.

### Using PostgreSQL

Set `DATABASE_URL` in your `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/npuchat
```

Or use the commented-out PostgreSQL service in `docker-compose.yml`.

## Frontend Development

### Dev Server

```bash
cd frontend
npm install
npm run dev
```

Vite runs on port 5173 and proxies `/api/*` requests to `http://localhost:5000` (Flask). Start Flask separately with `make run`.

### Architecture

The frontend uses **TanStack Query** for server state management:

- `hooks/useChats.ts` - Chat list queries and mutations (create, delete, toggle favorite)
- `hooks/useMessages.ts` - Message queries per chat
- `hooks/useSearch.ts` - Send message mutation (invalidates chats + messages)

Local UI state (`currentChatId`, `showTemplates`, `isCreatingChat`, `newChatName`) stays in `App.tsx` as `useState`.

**Component variants** use [CVA](https://cva.style/) (class-variance-authority) with Tailwind. Reusable UI components live in `components/ui/`.

The `@` path alias maps to `src/` for cleaner imports.

### Building for Production

```bash
cd frontend
npm run build      # TypeScript check + Vite build → ../static/dist/
```

Or from the project root:

```bash
make build-frontend
```

## Testing

### Backend Tests

```bash
make test                        # Run all backend tests
python3 -m pytest tests -v       # Verbose output
python3 -m pytest tests -k chat  # Run tests matching "chat"
```

Tests use an in-memory SQLite database with a clean schema per test function. Rate limiting is disabled in the test fixture. See `tests/conftest.py` for fixtures and JSON:API test helpers (`jsonapi_post`, `jsonapi_patch`, `get_jsonapi_data`, etc.).

### Frontend Tests

```bash
make test-frontend       # Run all frontend tests
cd frontend && npm test  # Same thing
```

Jest is configured with `jsdom` environment and `ts-jest` for TypeScript. The custom `render` in `test-utils.tsx` wraps components in `QueryClientProvider` (with `retry: false`). Mock data factories (`createMockChat`, `createMockMessage`, `createMockTemplate`) are available from `test-utils`.

### E2E Tests (Playwright)

```bash
cd e2e
npm install
npx playwright install    # Install browsers
npx playwright test       # Run tests
```

Or from the project root: `make test-e2e`

Playwright auto-starts the Flask server on port 1314. Tests cover chat creation, switching, deletion, favorites, and template management.

### Run Everything

```bash
make all    # Runs: lint, lint-frontend, test, test-frontend
```

## Linting

### Python (Ruff)

```bash
make lint       # Check for issues
make lint-fix   # Auto-fix issues
```

Ruff is configured in `pyproject.toml` with rules for errors (E), pyflakes (F), import sorting (I), and warnings (W). Line length is 88. E501 (line too long) is ignored.

### Frontend (ESLint)

```bash
make lint-frontend
```

ESLint is configured for TypeScript + React with `react-hooks` and `react-refresh` plugins. Zero warnings allowed.

## Docker

### Build and Run

```bash
make docker-build    # Build the image
make docker-run      # Start with docker compose
make docker-stop     # Stop containers
```

The Dockerfile uses a multi-stage build:
1. **Stage 1** (`node:20-slim`): Builds the React frontend
2. **Stage 2** (`python:3.11-slim`): Installs Python deps, copies app code + built frontend

The container exposes port 1314 and includes a health check against `/api/health`.

### Environment

Create a `.env` file (copy from `.env.example`) before running. The `data/` directory is volume-mounted for SQLite persistence.

To use PostgreSQL, uncomment the `postgres` service in `docker-compose.yml` and set:

```
DATABASE_URL=postgresql://npuchat:npuchat@postgres:5432/npuchat
```

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on pushes and PRs to `main`:

| Job | What it does |
|---|---|
| `backend-test` | Install Python 3.11, `pip install`, `make lint`, `make test` |
| `frontend-test` | Install Node 20, `npm ci`, `make lint-frontend`, `make test-frontend` |
| `build-validation` | Build frontend, build Docker image, smoke test `/api/health` |

## Structured Logging

Logs are JSON-formatted by default (set `LOG_FORMAT=text` for local dev). Each request gets a correlation ID via the `X-Correlation-ID` header (generated if not provided). Example JSON log entry:

```json
{
  "timestamp": "2026-02-27T12:00:00+00:00",
  "level": "INFO",
  "logger": "http",
  "message": "POST /api/v1/search 200",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Common Tasks

| Task | Command |
|---|---|
| Install everything | `make install` |
| Run the app | `make run` |
| Run all checks | `make all` |
| Build frontend | `make build-frontend` |
| Run backend tests | `make test` |
| Run frontend tests | `make test-frontend` |
| Run E2E tests | `make test-e2e` |
| Lint Python | `make lint` |
| Lint frontend | `make lint-frontend` |
| Create migration | `make db-migrate msg="description"` |
| Apply migrations | `make db-upgrade` |
| Build Docker image | `make docker-build` |
| Start containers | `make docker-run` |
| Stop containers | `make docker-stop` |
| Clean artifacts | `make clean` |
