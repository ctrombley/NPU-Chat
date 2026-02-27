import json
import pytest

import npuchat
from npuchat import create_app, contexts


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

    # Ensure context usage is enabled for the test
    npuchat.use_chat_context = True

    # Start with a clean server-side state
    contexts.clear()

    # Prepare mocked responses for the sequence of LLM calls
    responses = [
        {"content": "Okay, this chat is about apples. Let me know how I can help you explore the topic!"},
        {"content": json.dumps({"name": "Apple Chat", "emoji": "🍎"})},
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

    # Patch requests.post used by npuchat.feed_the_llama
    monkeypatch.setattr(npuchat.requests, "post", fake_post)

    app = create_app()
    client = app.test_client()

    # 1) First user message — no session_id provided so server creates one
    rv = client.post('/search', data={'input_text': 'This chat is about apples.'})
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'session_id' in data
    session_id = data['session_id']

    # Ensure server created the chat and saved the user+assistant messages
    assert session_id in contexts
    chat = contexts[session_id]
    assert any('User: This chat is about apples.' in m for m in chat.messages), "User message not saved"
    assert any('Assistant: Okay, this chat is about apples.' in m for m in chat.messages), "Assistant reply not saved"

    # Auto-naming should have run and set a name (best-effort)
    assert not chat.needs_naming
    assert 'Apple' in chat.name or chat.name.startswith('🍎'), f"Unexpected chat name: {chat.name}"

    # 2) Follow-up message using the returned session_id
    rv2 = client.post(f'/search?session_id={session_id}', data={'input_text': 'What is this chat about?'})
    assert rv2.status_code == 200
    data2 = rv2.get_json()
    assert data2['session_id'] == session_id

    # Verify that one of the outgoing LLM payloads for this follow-up contained the prior assistant reply
    found = False
    for payload in call_log:
        if payload and 'input_str' in payload and 'Assistant: Okay, this chat is about apples.' in payload['input_str']:
            found = True
            break
    assert found, "Context (previous assistant reply) was not included in the follow-up LLM call"

