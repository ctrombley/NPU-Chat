import json

from conftest import (
    JSONAPI_CONTENT_TYPE,
    get_jsonapi_attrs,
    get_jsonapi_data,
    get_jsonapi_id,
    jsonapi_patch,
    jsonapi_post,
)


class TestChatManagement:
    """Test class for chat management functionality"""

    def test_create_chat_success(self, client):
        """Test successful chat creation"""
        response = jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'New Test Chat'})

        assert response.status_code == 201
        data = get_jsonapi_data(response)
        assert data['type'] == 'chats'
        assert data['id']  # id should be present
        assert data['attributes']['name'] == 'New Test Chat'
        assert 'created_at' in data['attributes']

    def test_create_chat_missing_name(self, client):
        """Test chat creation with missing name"""
        response = jsonapi_post(client, '/api/v1/chats', 'chats', {})

        assert response.status_code == 400
        body = json.loads(response.data)
        assert 'errors' in body

    def test_list_chats_empty(self, client):
        """Test listing chats when none exist"""
        response = client.get('/api/v1/chats')

        assert response.status_code == 200
        data = get_jsonapi_data(response)
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_chats_with_data(self, client):
        """Test listing chats with existing data"""
        jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Test Chat 1'})
        jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Test Chat 2'})

        response = client.get('/api/v1/chats')
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

    def test_list_chats_pagination_meta(self, client):
        """Test that list chats returns pagination meta."""
        jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Chat 1'})
        jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Chat 2'})

        response = client.get('/api/v1/chats')
        assert response.status_code == 200
        body = json.loads(response.data)
        assert 'meta' in body
        assert body['meta']['total'] == 2
        assert body['meta']['page'] == 1

    def test_get_chat_messages_success(self, client):
        """Test retrieving messages for a specific chat"""
        create_response = jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Test Chat'})
        chat_id = get_jsonapi_id(create_response)

        response = client.get(f'/api/v1/chats/{chat_id}/messages')
        assert response.status_code == 200
        data = get_jsonapi_data(response)
        assert isinstance(data, list)

    def test_get_chat_messages_not_found(self, client):
        """Test retrieving messages for non-existent chat"""
        response = client.get('/api/v1/chats/non-existent-chat/messages')

        assert response.status_code == 404
        body = json.loads(response.data)
        assert 'errors' in body
        assert 'not found' in body['errors'][0]['detail'].lower()

    def test_delete_chat_success(self, client):
        """Test successful chat deletion"""
        create_response = jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Test Chat'})
        chat_id = get_jsonapi_id(create_response)

        response = client.delete(f'/api/v1/chats/{chat_id}')
        assert response.status_code == 204

        # Verify it's gone
        list_response = client.get('/api/v1/chats')
        list_data = get_jsonapi_data(list_response)
        assert len(list_data) == 0

    def test_delete_chat_not_found(self, client):
        """Test deleting non-existent chat"""
        response = client.delete('/api/v1/chats/non-existent-chat')

        assert response.status_code == 404
        body = json.loads(response.data)
        assert 'errors' in body
        assert 'not found' in body['errors'][0]['detail'].lower()

    def test_update_chat_name(self, client):
        """Test updating chat name"""
        create_response = jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Original Name'})
        chat_id = get_jsonapi_id(create_response)

        # Update the name
        response = jsonapi_patch(client, f'/api/v1/chats/{chat_id}', 'chats', chat_id, {'name': 'Updated Name'})
        assert response.status_code == 200
        attrs = get_jsonapi_attrs(response)
        assert attrs['name'] == 'Updated Name'

        # Verify the update
        list_response = client.get('/api/v1/chats')
        list_data = get_jsonapi_data(list_response)
        chat = next(c for c in list_data if c['id'] == chat_id)
        assert chat['attributes']['name'] == 'Updated Name'

    def test_update_chat_favorite(self, client):
        """Test updating chat favorite status"""
        create_response = jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Test Chat'})
        chat_id = get_jsonapi_id(create_response)

        # Update to favorite
        response = jsonapi_patch(client, f'/api/v1/chats/{chat_id}', 'chats', chat_id, {'is_favorite': True})
        assert response.status_code == 200
        attrs = get_jsonapi_attrs(response)
        assert attrs['is_favorite'] is True

        # Verify the update
        list_response = client.get('/api/v1/chats')
        list_data = get_jsonapi_data(list_response)
        chat = next(c for c in list_data if c['id'] == chat_id)
        assert chat['attributes']['is_favorite'] is True

        # Update to unfavorite
        response = jsonapi_patch(client, f'/api/v1/chats/{chat_id}', 'chats', chat_id, {'is_favorite': False})
        assert response.status_code == 200
        attrs = get_jsonapi_attrs(response)
        assert attrs['is_favorite'] is False

        # Verify the update
        list_response = client.get('/api/v1/chats')
        list_data = get_jsonapi_data(list_response)
        chat = next(c for c in list_data if c['id'] == chat_id)
        assert chat['attributes']['is_favorite'] is False

    def test_update_chat_not_found(self, client):
        """Test updating non-existent chat"""
        response = jsonapi_patch(client, '/api/v1/chats/non-existent-chat', 'chats', 'non-existent-chat', {'name': 'New Name'})

        assert response.status_code == 404
        body = json.loads(response.data)
        assert 'errors' in body
        assert 'not found' in body['errors'][0]['detail'].lower()
