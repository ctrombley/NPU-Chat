import json

from conftest import JSONAPI_CONTENT_TYPE


def test_empty_input(client):
    """Test for empty input"""
    response = client.post(
        '/api/v1/search',
        data=json.dumps({'data': {'type': 'search-requests', 'attributes': {'input_text': ''}}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert response.status_code == 400
    body = json.loads(response.data)
    assert 'errors' in body


def test_whitespace_only_input(client):
    """Test for whitespace-only input"""
    response = client.post(
        '/api/v1/search',
        data=json.dumps({'data': {'type': 'search-requests', 'attributes': {'input_text': '   '}}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert response.status_code == 400
    body = json.loads(response.data)
    assert 'errors' in body


def test_missing_request_body(client):
    """Test for missing request body"""
    response = client.post(
        '/api/v1/search',
        data='{}',
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert response.status_code == 400
    body = json.loads(response.data)
    assert 'errors' in body
