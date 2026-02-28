import json


def test_health_check_returns_ok(client):
    """Test health check endpoint returns 200 with ok status."""
    response = client.get('/api/health')
    assert response.status_code == 200
    body = json.loads(response.data)
    assert body['status'] == 'ok'
    assert body['database'] == 'ok'
