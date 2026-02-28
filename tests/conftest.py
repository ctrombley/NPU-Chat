import json
import os
import sys

import pytest

# Ensure project root is on sys.path so tests can import npuchat
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db as _db
from npuchat import create_app


@pytest.fixture(scope='function')
def client():
    """
    Pytest fixture to provide a Flask test client with a clean database.
    """
    app = create_app(run_migrations=False)
    app.config['TESTING'] = True
    app.config['RATELIMIT_ENABLED'] = False
    with app.app_context():
        _db.create_all()
        yield app.test_client()
        _db.session.remove()
        _db.drop_all()


# --- JSON:API test helpers ---

JSONAPI_CONTENT_TYPE = 'application/vnd.api+json'

def jsonapi_post(client, url, type_, attrs):
    """POST a JSON:API resource and return the response."""
    return client.post(
        url,
        data=json.dumps({'data': {'type': type_, 'attributes': attrs}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )

def jsonapi_patch(client, url, type_, id_, attrs):
    """PATCH a JSON:API resource and return the response."""
    return client.patch(
        url,
        data=json.dumps({'data': {'type': type_, 'id': id_, 'attributes': attrs}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )

def get_jsonapi_data(response):
    """Parse JSON:API response and return the 'data' field."""
    return json.loads(response.data)['data']

def get_jsonapi_attrs(response):
    """Parse a single-resource JSON:API response and return its attributes."""
    data = get_jsonapi_data(response)
    if isinstance(data, list):
        return data[0]['attributes']
    return data['attributes']

def get_jsonapi_id(response):
    """Parse a single-resource JSON:API response and return its id."""
    data = get_jsonapi_data(response)
    if isinstance(data, list):
        return data[0]['id']
    return data['id']
