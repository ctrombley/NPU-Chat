import json
from unittest.mock import patch

from conftest import JSONAPI_CONTENT_TYPE

from models import Chat, db


def test_autonaming_on_new_search_session(client):
    """Verify that POSTing to /api/v1/search without session_id creates a new Chat and attempts to auto-name it."""
    app = client.application

    # Mock feed_the_llama responses: first call is the content reply, second call is naming JSON
    naming_json = json.dumps({'name': 'Summary', 'emoji': '\U0001f4dd'})

    # Patch requests.post used inside feed_the_llama to return controlled responses
    class MockResp:
        def __init__(self, json_data, status_code=200):
            self._json = json_data
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception('HTTP error')

        def json(self):
            return self._json

    def side_effect_post(url, headers=None, json=None, timeout=None):
        # Distinguish between regular LLM response and naming prompt by checking the input_str
        input_str = json.get('input_str', '') if isinstance(json, dict) else ''
        if 'Please provide a very short' in input_str:
            return MockResp({'content': naming_json})
        else:
            return MockResp({'content': 'LLM normal reply'})

    with patch('requests.post', side_effect=side_effect_post):
        response = client.post(
            '/api/v1/search',
            data=json.dumps({'data': {'type': 'search-requests', 'attributes': {'input_text': 'Hello'}}}),
            content_type=JSONAPI_CONTENT_TYPE,
        )

    assert response.status_code == 200
    body = json.loads(response.data)
    assert 'data' in body
    assert body['data']['attributes']['content']

    # There should be exactly one chat created
    with app.app_context():
        chats = Chat.query.all()
        assert len(chats) == 1
        chat = chats[0]
        # The chat should have been renamed to include the emoji and name from naming_json
        assert chat.name.startswith('\U0001f4dd') or 'Summary' in chat.name
        assert chat.needs_naming is False
