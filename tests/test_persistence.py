import json
import os
import sqlite3

from conftest import JSONAPI_CONTENT_TYPE, get_jsonapi_attrs, get_jsonapi_id, jsonapi_patch, jsonapi_post
from npuchat import create_app
from services import LLMService


def setup_function():
    # Ensure a clean DB before each test
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chats.db')
    print(f"DEBUG: Removing DB file: {db_path}")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"DEBUG: Removed DB file")
        except Exception as e:
            print(f"DEBUG: Failed to remove DB file: {e}")
            pass


def test_auto_naming_and_persistence(monkeypatch):
    app = create_app()
    app.config['TESTING'] = True

    # Start with a clean server-side state
    with app.app_context():
        from models import db, Chat
        db.session.query(Chat).delete()
        db.session.commit()

    client = app.test_client()

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
        '/api/search',
        data=json.dumps({'data': {'type': 'search-requests', 'attributes': {'input_text': 'Hello world'}}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )
    assert resp.status_code == 200
    body = json.loads(resp.data)
    session_id = body['data']['attributes']['session_id']

    # Verify data in SQLite
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chats.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, emoji FROM chats WHERE id = ?", (session_id,))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 'Quick Help'
    assert row[1] == '\u26a1'

    # Check messages exist
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT content FROM messages WHERE chat_id = ? ORDER BY position", (session_id,))
    msgs = [r[0] for r in cur.fetchall()]
    conn.close()

    assert any('User:' in m for m in msgs)
    assert any('Assistant:' in m for m in msgs)


def test_explicit_chat_creation_persists_name():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    resp = jsonapi_post(client, '/api/chats', 'chats', {'name': 'Persisted Chat'})
    assert resp.status_code == 201
    cid = get_jsonapi_id(resp)

    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chats.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM chats WHERE id = ?", (cid,))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 'Persisted Chat'


def test_update_chat_metadata():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    # Create a chat first
    resp = jsonapi_post(client, '/api/chats', 'chats', {'name': 'Original Name'})
    assert resp.status_code == 201
    cid = get_jsonapi_id(resp)

    # Update name
    resp = jsonapi_patch(client, f'/api/chats/{cid}', 'chats', cid, {'name': 'Updated Name'})
    assert resp.status_code == 200
    data = json.loads(resp.data)['data']
    assert data['id'] == cid
    assert data['attributes']['name'] == 'Updated Name'
    assert data['attributes']['emoji'] == ''

    # Update emoji
    resp = jsonapi_patch(client, f'/api/chats/{cid}', 'chats', cid, {'emoji': '\U0001f680'})
    assert resp.status_code == 200
    data = json.loads(resp.data)['data']
    assert data['id'] == cid
    assert data['attributes']['name'] == 'Updated Name'
    assert data['attributes']['emoji'] == '\U0001f680'

    # Update both
    resp = jsonapi_patch(client, f'/api/chats/{cid}', 'chats', cid, {'name': 'Final Name', 'emoji': '\U0001f31f'})
    assert resp.status_code == 200
    data = json.loads(resp.data)['data']
    assert data['id'] == cid
    assert data['attributes']['name'] == 'Final Name'
    assert data['attributes']['emoji'] == '\U0001f31f'

    # Verify persistence
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chats.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, emoji FROM chats WHERE id = ?", (cid,))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 'Final Name'
    assert row[1] == '\U0001f31f'

    # Test empty attributes (still valid PATCH, just no changes)
    resp = jsonapi_patch(client, f'/api/chats/{cid}', 'chats', cid, {})
    assert resp.status_code == 200

    # Test non-existent chat
    resp = jsonapi_patch(client, '/api/chats/nonexistent', 'chats', 'nonexistent', {'name': 'New Name'})
    assert resp.status_code == 404
