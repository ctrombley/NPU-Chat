import json
from npuchat import create_app

# Test data
TEST_SESSION_ID = "test-session-123"
TEST_CHAT_DATA = {
    "name": "Test Chat",
    "messages": [
        {"type": "sent", "text": "Hello", "timestamp": 1640995200000},
        {"type": "received", "text": "Hi there!", "timestamp": 1640995260000}
    ]
}

class TestChatManagement:
    """Test class for chat management functionality"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        # Clear global CONTEXTS to ensure test isolation
        from npuchat import CONTEXTS
        CONTEXTS.clear()

    def test_create_chat_success(self):
        """Test successful chat creation"""
        response = self.client.post('/chats',
                                   data=json.dumps({
                                       "name": "New Test Chat"
                                   }),
                                   content_type='application/json')

        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert "chat_id" in response_data
        assert "name" in response_data
        assert response_data["name"] == "New Test Chat"
        assert "created_at" in response_data

    def test_create_chat_missing_name(self):
        """Test chat creation with missing name"""
        response = self.client.post('/chats',
                                   data=json.dumps({}),
                                   content_type='application/json')

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert "name is required" in response_data["error"].lower()

    def test_list_chats_empty(self):
        """Test listing chats when none exist"""
        response = self.client.get('/chats')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert isinstance(response_data, list)
        assert len(response_data) == 0

    def test_list_chats_with_data(self):
        """Test listing chats with existing data"""
        # Create a chat first
        self.client.post('/chats',
                        data=json.dumps({"name": "Test Chat 1"}),
                        content_type='application/json')
        self.client.post('/chats',
                        data=json.dumps({"name": "Test Chat 2"}),
                        content_type='application/json')

        response = self.client.get('/chats')
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert isinstance(response_data, list)
        assert len(response_data) == 2

        # Check structure
        for chat in response_data:
            assert "id" in chat
            assert "name" in chat
            assert "message_count" in chat
            assert "created_at" in chat

    def test_get_chat_messages_success(self):
        """Test retrieving messages for a specific chat"""
        # Create a chat
        create_response = self.client.post('/chats',
                                          data=json.dumps({"name": "Test Chat"}),
                                          content_type='application/json')
        chat_id = json.loads(create_response.data)["chat_id"]

        response = self.client.get(f'/chats/{chat_id}/messages')
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "messages" in response_data
        assert isinstance(response_data["messages"], list)

    def test_get_chat_messages_not_found(self):
        """Test retrieving messages for non-existent chat"""
        response = self.client.get('/chats/non-existent-chat/messages')

        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert "not found" in response_data["error"].lower()

    def test_delete_chat_success(self):
        """Test successful chat deletion"""
        # Create a chat first
        create_response = self.client.post('/chats',
                                          data=json.dumps({"name": "Test Chat"}),
                                          content_type='application/json')
        chat_id = json.loads(create_response.data)["chat_id"]

        response = self.client.delete(f'/chats/{chat_id}')
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "message" in response_data
        assert "deleted" in response_data["message"].lower()

        # Verify it's gone
        list_response = self.client.get('/chats')
        list_data = json.loads(list_response.data)
        assert len(list_data) == 0

    def test_delete_chat_not_found(self):
        """Test deleting non-existent chat"""
        response = self.client.delete('/chats/non-existent-chat')

        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert "not found" in response_data["error"].lower()

    def test_switch_chat_success(self):
        """Test switching to an existing chat"""
        # Create a chat first
        create_response = self.client.post('/chats',
                                          data=json.dumps({"name": "Test Chat"}),
                                          content_type='application/json')
        chat_id = json.loads(create_response.data)["chat_id"]

        response = self.client.post(f'/chats/{chat_id}/switch')
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "message" in response_data
        assert "switched" in response_data["message"].lower()

    def test_switch_chat_not_found(self):
        """Test switching to non-existent chat"""
        response = self.client.post('/chats/non-existent-chat/switch')

        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert "not found" in response_data["error"].lower()

    def test_update_chat_name(self):
        """Test updating chat name"""
        # Create a chat first
        create_response = self.client.post('/chats',
                                          data=json.dumps({"name": "Original Name"}),
                                          content_type='application/json')
        chat_id = json.loads(create_response.data)["chat_id"]

        # Update the name
        response = self.client.put(f'/chats/{chat_id}',
                                  data=json.dumps({"name": "Updated Name"}),
                                  content_type='application/json')
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "name" in response_data
        assert response_data["name"] == "Updated Name"

        # Verify the update
        list_response = self.client.get('/chats')
        list_data = json.loads(list_response.data)
        chat = next(c for c in list_data if c["id"] == chat_id)
        assert chat["name"] == "Updated Name"

    def test_update_chat_not_found(self):
        """Test updating non-existent chat"""
        response = self.client.put('/chats/non-existent-chat',
                                  data=json.dumps({"name": "New Name"}),
                                  content_type='application/json')

        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert "error" in response_data
        assert "not found" in response_data["error"].lower()

