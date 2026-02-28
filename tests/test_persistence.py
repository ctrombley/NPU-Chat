import json

from conftest import (
    JSONAPI_CONTENT_TYPE,
    get_jsonapi_id,
    jsonapi_patch,
    jsonapi_post,
)

from models import Chat, Message, db
from npuchat import create_app


def test_auto_naming_and_persistence(client, monkeypatch):
    # Monkeypatch feed_the_llama to return predictable assistant response and naming JSON
    responses = [
        "This is the assistant reply.",
        json.dumps({"name": "Quick Help", "emoji": "\u26a1"})
    ]

    def fake_feed(query, prefix, postfix):
        if responses:
            return responses.pop(0)
        return ""

    monkeypatch.setattr('services.LLMService.feed_the_llama', fake_feed)

    resp = client.post(
        '/api/v1/search',
        data=json.dumps({'data': {'type': 'search-requests', 'attributes': {'input_text': 'Hello world'}}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert resp.status_code == 200
    body = json.loads(resp.data)
    session_id = body['data']['attributes']['session_id']

    # Verify data using SQLAlchemy
    app = client.application
    with app.app_context():
        chat = db.session.get(Chat, session_id)
        assert chat is not None
        assert chat.name == 'Quick Help'
        assert chat.emoji == '\u26a1'

        # Check messages exist
        msgs = Message.query.filter_by(chat_id=session_id).order_by(Message.position).all()
        assert any(m.role == 'user' for m in msgs)
        assert any(m.role == 'assistant' for m in msgs)


def test_explicit_chat_creation_persists_name(client):
    resp = jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Persisted Chat'})
    assert resp.status_code == 201
    cid = get_jsonapi_id(resp)

    app = client.application
    with app.app_context():
        chat = db.session.get(Chat, cid)
        assert chat is not None
        assert chat.name == 'Persisted Chat'


def test_update_chat_metadata(client):
    # Create a chat first
    resp = jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Original Name'})
    assert resp.status_code == 201
    cid = get_jsonapi_id(resp)

    # Update name
    resp = jsonapi_patch(client, f'/api/v1/chats/{cid}', 'chats', cid, {'name': 'Updated Name'})
    assert resp.status_code == 200
    data = json.loads(resp.data)['data']
    assert data['id'] == cid
    assert data['attributes']['name'] == 'Updated Name'
    assert data['attributes']['emoji'] == ''

    # Update emoji
    resp = jsonapi_patch(client, f'/api/v1/chats/{cid}', 'chats', cid, {'emoji': '\U0001f680'})
    assert resp.status_code == 200
    data = json.loads(resp.data)['data']
    assert data['id'] == cid
    assert data['attributes']['name'] == 'Updated Name'
    assert data['attributes']['emoji'] == '\U0001f680'

    # Update both
    resp = jsonapi_patch(client, f'/api/v1/chats/{cid}', 'chats', cid, {'name': 'Final Name', 'emoji': '\U0001f31f'})
    assert resp.status_code == 200
    data = json.loads(resp.data)['data']
    assert data['id'] == cid
    assert data['attributes']['name'] == 'Final Name'
    assert data['attributes']['emoji'] == '\U0001f31f'

    # Verify persistence via SQLAlchemy
    app = client.application
    with app.app_context():
        chat = db.session.get(Chat, cid)
        assert chat is not None
        assert chat.name == 'Final Name'
        assert chat.emoji == '\U0001f31f'

    # Test empty attributes (still valid PATCH, just no changes)
    resp = jsonapi_patch(client, f'/api/v1/chats/{cid}', 'chats', cid, {})
    assert resp.status_code == 200

    # Test non-existent chat
    resp = jsonapi_patch(client, '/api/v1/chats/nonexistent', 'chats', 'nonexistent', {'name': 'New Name'})
    assert resp.status_code == 404
