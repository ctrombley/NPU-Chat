import json
from unittest.mock import patch

import pytest

from conftest import JSONAPI_CONTENT_TYPE
from models import Chat, db
from npuchat import create_app
from services import ChatService


class MockResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        # Simulate successful status
        return None


def test_context_persistence_and_autoname(monkeypatch):
    """Verify that assistant replies are preserved in server-side context across messages

    We mock requests.post to simulate the NPU/LLM. The sequence of mocked responses is:
      1) assistant reply to the user's first question
      2) a JSON string suggesting a name+emoji for the chat
      3) assistant reply to the follow-up question

    The test asserts that:
      - a session_id is returned and a Chat object is created
      - the chat.messages contains both the user and assistant entries after the first call
      - the auto-naming step updates the chat.name when valid JSON is returned
      - the second LLM invocation receives the previous assistant reply in its `input_str` (i.e. context was prepended)
    """

    app = create_app()
    app.config['TESTING'] = True

    # Start with a clean server-side state
    with app.app_context():
        db.session.query(Chat).delete()
        db.session.commit()

    # Prepare mocked responses for the sequence of LLM calls
    responses = [
        {"content": "Okay, this chat is about apples. Let me know how I can help you explore the topic!"},
        {"content": json.dumps({"name": "Apple Chat", "emoji": "\U0001f34e"})},
        {"content": "This chat is about apples."},
    ]

    call_log = []

    def fake_post(url, headers=None, json=None, timeout=None):
        # Record the outgoing payload so tests can inspect it
        call_log.append(json)
        # Pop the next prepared response
        if not responses:
            return MockResponse({"content": ""})
        return MockResponse(responses.pop(0))

    # Patch requests.post used by services.LLMService.feed_the_llama
    monkeypatch.setattr('services.requests.post', fake_post)

    client = app.test_client()

    # 1) First user message -- no session_id provided so server creates one
    rv = client.post(
        '/api/search',
        data=json.dumps({'data': {'type': 'search-requests', 'attributes': {'input_text': 'This chat is about apples.'}}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert 'data' in body
    session_id = body['data']['attributes']['session_id']

    # Ensure server created the chat and saved the user+assistant messages
    with app.app_context():
        chat = Chat.query.get(session_id)
        assert chat is not None
        messages = ChatService.get_chat_messages(session_id) or []
        assert any('User: This chat is about apples.' in m for m in messages), "User message not saved"
        assert any('Assistant: Okay, this chat is about apples.' in m for m in messages), "Assistant reply not saved"

        # Auto-naming should have run and set a name (best-effort)
        assert not chat.needs_naming
        assert 'Apple' in chat.name or chat.name.startswith('\U0001f34e'), f"Unexpected chat name: {chat.name}"

    # 2) Follow-up message using the returned session_id
    rv2 = client.post(
        '/api/search',
        data=json.dumps({'data': {'type': 'search-requests', 'attributes': {'input_text': 'What is this chat about?', 'session_id': session_id}}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert rv2.status_code == 200
    body2 = rv2.get_json()
    assert body2['data']['attributes']['session_id'] == session_id

    # The follow-up LLM call should include the previous assistant reply in its payload.
    assert call_log, "No LLM calls were recorded"
    assert any(p and 'input_str' in p and 'Assistant: Okay, this chat is about apples.' in p['input_str'] for p in call_log), \
        "Context (previous assistant reply) was not included in any LLM call payload"
