import json
import os
import sqlite3
from npuchat import create_app, DB_PATH, contexts


def setup_function():
    # Ensure a clean DB before each test
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass


def teardown_function():
    contexts.clear()


def test_auto_naming_and_persistence(monkeypatch):
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    # Monkeypatch feed_the_llama to return predictable assistant response and naming JSON
    responses = [
        "This is the assistant reply.",
        json.dumps({"name": "Quick Help", "emoji": "⚡"})
    ]

    def fake_feed(query, prefix, postfix):
        if responses:
            return responses.pop(0)
        return ""

    monkeypatch.setattr('npuchat.feed_the_llama', fake_feed)

    resp = client.post('/search', data={'input_text': 'Hello world'})
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'session_id' in data
    session_id = data['session_id']

    # Verify data in SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name, emoji FROM chats WHERE id = ?", (session_id,))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 'Quick Help'
    assert row[1] == '⚡'

    # Check messages exist
    conn = sqlite3.connect(DB_PATH)
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

    resp = client.post('/chats', data=json.dumps({'name': 'Persisted Chat'}), content_type='application/json')
    assert resp.status_code == 201
    data = json.loads(resp.data)
    cid = data['chat_id']

    conn = sqlite3.connect(DB_PATH)
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
    resp = client.post('/chats', data=json.dumps({'name': 'Original Name'}), content_type='application/json')
    assert resp.status_code == 201
    data = json.loads(resp.data)
    cid = data['chat_id']

    # Update name
    resp = client.put(f'/chats/{cid}', data=json.dumps({'name': 'Updated Name'}), content_type='application/json')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['id'] == cid
    assert data['name'] == 'Updated Name'
    assert data['emoji'] == ''

    # Update emoji
    resp = client.put(f'/chats/{cid}', data=json.dumps({'emoji': '🚀'}), content_type='application/json')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['id'] == cid
    assert data['name'] == 'Updated Name'
    assert data['emoji'] == '🚀'

    # Update both
    resp = client.put(f'/chats/{cid}', data=json.dumps({'name': 'Final Name', 'emoji': '🌟'}), content_type='application/json')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['id'] == cid
    assert data['name'] == 'Final Name'
    assert data['emoji'] == '🌟'

    # Verify persistence
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name, emoji FROM chats WHERE id = ?", (cid,))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 'Final Name'
    assert row[1] == '🌟'

    # Test no changes if no name or emoji
    resp = client.put(f'/chats/{cid}', data=json.dumps({}), content_type='application/json')
    assert resp.status_code == 400

    # Test non-existent chat
    resp = client.put('/chats/nonexistent', data=json.dumps({'name': 'New Name'}), content_type='application/json')
    assert resp.status_code == 404

