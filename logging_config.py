import json
import logging
import uuid
from datetime import datetime, timezone

from flask import g, request


class JsonFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if hasattr(record, 'correlation_id'):
            log_entry['correlation_id'] = record.correlation_id
        if record.exc_info and record.exc_info[0] is not None:
            log_entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(app):
    """Configure structured logging for the Flask application."""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    log_format = app.config.get('LOG_FORMAT', 'json')

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    if log_format == 'json':
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s] %(message)s'
        ))
    root_logger.addHandler(handler)

    @app.before_request
    def add_correlation_id():
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        g.correlation_id = correlation_id

    @app.after_request
    def log_request(response):
        correlation_id = getattr(g, 'correlation_id', None)
        if correlation_id:
            response.headers['X-Correlation-ID'] = correlation_id
        logger = logging.getLogger('http')
        extra = {'correlation_id': correlation_id} if correlation_id else {}
        logger.info(
            '%s %s %s',
            request.method,
            request.path,
            response.status_code,
            extra=extra,
        )
        return response
