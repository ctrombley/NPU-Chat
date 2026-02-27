import json
from unittest.mock import patch
from npuchat import create_app, CONTEXTS


def test_autonaming_on_new_search_session():
    """Verify that POSTing to /search without session_id creates a new Chat and attempts to auto-name it."""
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    # Ensure clean state
    CONTEXTS.clear()

    # Mock feed_the_llama responses: first call is the content reply, second call is naming JSON
    naming_json = json.dumps({'name': 'Summary', 'emoji': '📝'})

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
        response = client.post('/search', data={'input_text': 'Hello'})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'content' in data

    # There should be exactly one chat created
    assert len(CONTEXTS) == 1
    chat = next(iter(CONTEXTS.values()))
    # The chat should have been renamed to include the emoji and name from naming_json
    assert chat.name.startswith('📝') or 'Summary' in chat.name
    assert chat.needs_naming is False

