import json

from conftest import (
    JSONAPI_CONTENT_TYPE,
    get_jsonapi_attrs,
    get_jsonapi_data,
    get_jsonapi_id,
    jsonapi_patch,
    jsonapi_post,
)

from npuchat import create_app


class TestChatManagement:
    """Test class for chat management functionality"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.app = create_app(run_migrations=False)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            from models import db
            db.create_all()
            db.session.remove()
            db.drop_all()
            db.create_all()

    def test_create_chat_success(self):
        """Test successful chat creation"""
        response = jsonapi_post(self.client, '/api/chats', 'chats', {'name': 'New Test Chat'})

        assert response.status_code == 201
        data = get_jsonapi_data(response)
        assert data['type'] == 'chats'
        assert data['id']  # id should be present
        assert data['attributes']['name'] == 'New Test Chat'
        assert 'created_at' in data['attributes']

    def test_create_chat_missing_name(self):
        """Test chat creation with missing name"""
        response = jsonapi_post(self.client, '/api/chats', 'chats', {})

        assert response.status_code == 400
        body = json.loads(response.data)
        assert 'errors' in body
        assert 'name is required' in body['errors'][0]['detail'].lower()

    def test_list_chats_empty(self):
        """Test listing chats when none exist"""
        response = self.client.get('/api/chats')

        assert response.status_code == 200
        data = get_jsonapi_data(response)
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_chats_with_data(self):
        """Test listing chats with existing data"""
        jsonapi_post(self.client, '/api/chats', 'chats', {'name': 'Test Chat 1'})
        jsonapi_post(self.client, '/api/chats', 'chats', {'name': 'Test Chat 2'})

        response = self.client.get('/api/chats')
        assert response.status_code == 200
        data = get_jsonapi_data(response)
        assert isinstance(data, list)
        assert len(data) == 2

        # Check structure
        for chat in data:
            assert chat['type'] == 'chats'
            assert 'id' in chat
            assert 'name' in chat['attributes']
            assert 'is_favorite' in chat['attributes']
            assert 'message_count' in chat['attributes']
            assert 'created_at' in chat['attributes']

    def test_get_chat_messages_success(self):
        """Test retrieving messages for a specific chat"""
        create_response = jsonapi_post(self.client, '/api/chats', 'chats', {'name': 'Test Chat'})
        chat_id = get_jsonapi_id(create_response)

        response = self.client.get(f'/api/chats/{chat_id}/messages')
        assert response.status_code == 200
        data = get_jsonapi_data(response)
        assert isinstance(data, list)

    def test_get_chat_messages_not_found(self):
        """Test retrieving messages for non-existent chat"""
        response = self.client.get('/api/chats/non-existent-chat/messages')

        assert response.status_code == 404
        body = json.loads(response.data)
        assert 'errors' in body
        assert 'not found' in body['errors'][0]['detail'].lower()

    def test_delete_chat_success(self):
        """Test successful chat deletion"""
        create_response = jsonapi_post(self.client, '/api/chats', 'chats', {'name': 'Test Chat'})
        chat_id = get_jsonapi_id(create_response)

        response = self.client.delete(f'/api/chats/{chat_id}')
        assert response.status_code == 204

        # Verify it's gone
        list_response = self.client.get('/api/chats')
        list_data = get_jsonapi_data(list_response)
        assert len(list_data) == 0

    def test_delete_chat_not_found(self):
        """Test deleting non-existent chat"""
        response = self.client.delete('/api/chats/non-existent-chat')

        assert response.status_code == 404
        body = json.loads(response.data)
        assert 'errors' in body
        assert 'not found' in body['errors'][0]['detail'].lower()

    def test_update_chat_name(self):
        """Test updating chat name"""
        create_response = jsonapi_post(self.client, '/api/chats', 'chats', {'name': 'Original Name'})
        chat_id = get_jsonapi_id(create_response)

        # Update the name
        response = jsonapi_patch(self.client, f'/api/chats/{chat_id}', 'chats', chat_id, {'name': 'Updated Name'})
        assert response.status_code == 200
        attrs = get_jsonapi_attrs(response)
        assert attrs['name'] == 'Updated Name'

        # Verify the update
        list_response = self.client.get('/api/chats')
        list_data = get_jsonapi_data(list_response)
        chat = next(c for c in list_data if c['id'] == chat_id)
        assert chat['attributes']['name'] == 'Updated Name'

    def test_update_chat_favorite(self):
        """Test updating chat favorite status"""
        create_response = jsonapi_post(self.client, '/api/chats', 'chats', {'name': 'Test Chat'})
        chat_id = get_jsonapi_id(create_response)

        # Update to favorite
        response = jsonapi_patch(self.client, f'/api/chats/{chat_id}', 'chats', chat_id, {'is_favorite': True})
        assert response.status_code == 200
        attrs = get_jsonapi_attrs(response)
        assert attrs['is_favorite'] is True

        # Verify the update
        list_response = self.client.get('/api/chats')
        list_data = get_jsonapi_data(list_response)
        chat = next(c for c in list_data if c['id'] == chat_id)
        assert chat['attributes']['is_favorite'] is True

        # Update to unfavorite
        response = jsonapi_patch(self.client, f'/api/chats/{chat_id}', 'chats', chat_id, {'is_favorite': False})
        assert response.status_code == 200
        attrs = get_jsonapi_attrs(response)
        assert attrs['is_favorite'] is False

        # Verify the update
        list_response = self.client.get('/api/chats')
        list_data = get_jsonapi_data(list_response)
        chat = next(c for c in list_data if c['id'] == chat_id)
        assert chat['attributes']['is_favorite'] is False

    def test_update_chat_not_found(self):
        """Test updating non-existent chat"""
        response = jsonapi_patch(self.client, '/api/chats/non-existent-chat', 'chats', 'non-existent-chat', {'name': 'New Name'})

        assert response.status_code == 404
        body = json.loads(response.data)
        assert 'errors' in body
        assert 'not found' in body['errors'][0]['detail'].lower()
