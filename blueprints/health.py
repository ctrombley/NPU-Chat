from flask import Blueprint

from jsonapi import jsonapi_response
from models import db

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint.
    ---
    tags:
      - health
    produces:
      - application/vnd.api+json
    responses:
      200:
        description: Service is healthy
      503:
        description: Service is unhealthy
    """
    status = {"status": "ok", "database": "ok"}
    try:
        db.session.execute(db.text('SELECT 1'))
    except Exception:
        status["status"] = "degraded"
        status["database"] = "error"
        return jsonapi_response(status, 503)
    return jsonapi_response(status, 200)
