# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime
FROM python:3.11-slim AS runtime
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY npuchat.py config.py models.py services.py jsonapi.py schemas.py extensions.py logging_config.py ./
COPY blueprints/ ./blueprints/
COPY migrations/ ./migrations/
COPY settings.ini ./

# Copy built frontend from stage 1
COPY --from=frontend-build /app/static/dist ./static/dist

# Create data directory
RUN mkdir -p data

EXPOSE 1314

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:1314/api/health')" || exit 1

CMD ["python", "npuchat.py"]
