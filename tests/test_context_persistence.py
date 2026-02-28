import json
from unittest.mock import patch

from conftest import JSONAPI_CONTENT_TYPE

from models import Chat, db
from services import ChatService


class MockResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


def test_context_persistence_and_autoname(client, monkeypatch):
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
    app = client.application

    # Prepare mocked responses for the sequence of LLM calls
    responses = [
        {"content": "Okay, this chat is about apples. Let me know how I can help you explore the topic!"},
        {"content": json.dumps({"name": "Apple Chat", "emoji": "\U0001f34e"})},
        {"content": "This chat is about apples."},
    ]

    call_log = []

    def fake_post(url, headers=None, json=None, timeout=None):
        call_log.append(json)
        if not responses:
            return MockResponse({"content": ""})
        return MockResponse(responses.pop(0))

    monkeypatch.setattr('services.requests.post', fake_post)

    # 1) First user message -- no session_id provided so server creates one
    rv = client.post(
        '/api/v1/search',
        data=json.dumps({'data': {'type': 'search-requests', 'attributes': {'input_text': 'This chat is about apples.'}}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert 'data' in body
    session_id = body['data']['attributes']['session_id']

    # Ensure server created the chat and saved the user+assistant messages
    with app.app_context():
        chat = db.session.get(Chat, session_id)
        assert chat is not None
        messages = ChatService.get_chat_messages(session_id) or []
        # Messages now have role column instead of prefixed content
        assert any(m.role == 'user' and 'This chat is about apples.' in m.content for m in messages), "User message not saved"
        assert any(m.role == 'assistant' and 'Okay, this chat is about apples.' in m.content for m in messages), "Assistant reply not saved"

        # Auto-naming should have run and set a name (best-effort)
        assert not chat.needs_naming
        assert 'Apple' in chat.name or chat.name.startswith('\U0001f34e'), f"Unexpected chat name: {chat.name}"

    # 2) Follow-up message using the returned session_id
    rv2 = client.post(
        '/api/v1/search',
        data=json.dumps({'data': {'type': 'search-requests', 'attributes': {'input_text': 'What is this chat about?', 'session_id': session_id}}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert rv2.status_code == 200
    body2 = rv2.get_json()
    assert body2['data']['attributes']['session_id'] == session_id

    # The follow-up LLM call should include the previous assistant reply in its payload.
    assert call_log, "No LLM calls were recorded"
    assert any(p and 'input_str' in p and 'Okay, this chat is about apples.' in p['input_str'] for p in call_log), \
        "Context (previous assistant reply) was not included in any LLM call payload"
