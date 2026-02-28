import json

from conftest import JSONAPI_CONTENT_TYPE

from npuchat import create_app


def test_empty_input():
    """Test for empty input"""
    app = create_app(run_migrations=False)
    app.config['TESTING'] = True
    client = app.test_client()

    response = client.post(
        '/api/search',
        data=json.dumps({'data': {'type': 'search-requests', 'attributes': {'input_text': ''}}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert response.status_code == 400
    body = json.loads(response.data)
    assert 'errors' in body
    assert 'empty input' in body['errors'][0]['detail'].lower()


def test_whitespace_only_input():
    """Test for whitespace-only input"""
    app = create_app(run_migrations=False)
    app.config['TESTING'] = True
    client = app.test_client()

    response = client.post(
        '/api/search',
        data=json.dumps({'data': {'type': 'search-requests', 'attributes': {'input_text': '   '}}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert response.status_code == 400
    body = json.loads(response.data)
    assert 'errors' in body
    assert 'empty input' in body['errors'][0]['detail'].lower()


def test_missing_request_body():
    """Test for missing request body"""
    app = create_app(run_migrations=False)
    app.config['TESTING'] = True
    client = app.test_client()

    response = client.post(
        '/api/search',
        data='{}',
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert response.status_code == 400
    body = json.loads(response.data)
    assert 'errors' in body
