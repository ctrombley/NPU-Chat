import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
from npuchat import create_app, BINDING_ADDRESS, BINDING_PORT

pytest.skip('Skipping Selenium frontend tests in CI', allow_module_level=True)

@pytest.fixture(scope='session')
def server():
    app = create_app()
    def run_app():
        app.run(host=BINDING_ADDRESS, port=BINDING_PORT, debug=False, use_reloader=False)
    server_thread = threading.Thread(target=run_app)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # Wait for server to start
    yield

class TestFrontendChatManagement:
    """Test class for frontend chat management functionality"""

    def test_new_chat_creation(self, driver):
        """Test creating a new chat"""
        driver.get(f"http://{BINDING_ADDRESS}:{BINDING_PORT}/")
        driver.execute_script("localStorage.clear();")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "new-chat-button"))
        )

        # Get initial chat count
        chat_list = driver.find_element(By.ID, "chat-list")
        initial_chats = chat_list.find_elements(By.TAG_NAME, "li")

        # Click new chat button
        new_chat_button = driver.find_element(By.ID, "new-chat-button")
        new_chat_button.click()

        # Wait for new chat to appear
        WebDriverWait(driver, 5).until(
            lambda d: len(d.find_element(By.ID, "chat-list").find_elements(By.TAG_NAME, "li")) > len(initial_chats)
        )

        # Verify new chat was created
        updated_chats = chat_list.find_elements(By.TAG_NAME, "li")
        assert len(updated_chats) == len(initial_chats) + 1

        # Verify chat messages area is empty for new chat
        chat_messages = driver.find_element(By.ID, "chat-messages")
        assert chat_messages.text.strip() == ""

    def test_chat_switching(self, driver):
        """Test switching between chats"""
        driver.get(f"http://{BINDING_ADDRESS}:{BINDING_PORT}/")
        driver.execute_script("localStorage.clear();")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "new-chat-button"))
        )

        # Create first chat and send a message
        new_chat_button = driver.find_element(By.ID, "new-chat-button")
        new_chat_button.click()

        input_box = driver.find_element(By.ID, "input_text")
        send_button = driver.find_element(By.CLASS_NAME, "send-button")

        input_box.send_keys("Message in first chat")
        send_button.click()

        # Wait for message to appear
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "message"))
        )

        # Create second chat
        new_chat_button.click()

        # Send different message in second chat
        input_box.send_keys("Message in second chat")
        send_button.click()

        # Wait for message to appear
        WebDriverWait(driver, 5).until(
            lambda d: "Message in second chat" in d.find_element(By.ID, "chat-messages").text
        )

        # Switch back to first chat
        chat_list = driver.find_element(By.ID, "chat-list")
        chats = chat_list.find_elements(By.TAG_NAME, "li")
        chats[1].click()  # Click first created chat

        # Wait for chat to switch
        WebDriverWait(driver, 5).until(
            lambda d: "Message in first chat" in d.find_element(By.ID, "chat-messages").text
        )

        # Verify we're back to first chat's messages
        current_messages = driver.find_element(By.ID, "chat-messages").text
        assert "Message in first chat" in current_messages
        assert "Message in second chat" not in current_messages

    def test_local_storage_persistence(self, driver):
        """Test that chats persist in localStorage"""
        driver.get(f"http://{BINDING_ADDRESS}:{BINDING_PORT}/")
        driver.execute_script("localStorage.clear();")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "new-chat-button"))
        )

        # Create a chat and send a message
        new_chat_button = driver.find_element(By.ID, "new-chat-button")
        new_chat_button.click()

        input_box = driver.find_element(By.ID, "input_text")
        send_button = driver.find_element(By.CLASS_NAME, "send-button")

        input_box.send_keys("Test persistence message")
        send_button.click()

        # Wait for message to appear
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "message"))
        )

        # Check that chats are stored in localStorage
        stored_chats = driver.execute_script("return localStorage.getItem('chats');")
        assert stored_chats is not None

        chats_data = driver.execute_script("return JSON.parse(localStorage.getItem('chats'));")
        assert isinstance(chats_data, dict)
        assert len(chats_data) > 0

        # Verify message content is stored
        chats_with_messages = {k: v for k, v in chats_data.items() if len(v) > 0}
        assert len(chats_with_messages) > 0
        first_chat_id = list(chats_with_messages.keys())[0]
        messages = chats_with_messages[first_chat_id]
        assert len(messages) > 0
        assert messages[0]["text"] == "Test persistence message"
        assert messages[0]["type"] == "sent"

    def test_chat_persistence_across_page_reload(self, driver):
        """Test that chats persist across page reloads"""
        driver.get(f"http://{BINDING_ADDRESS}:{BINDING_PORT}/")
        driver.execute_script("localStorage.clear();")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "new-chat-button"))
        )

        # Create a chat and send a message
        new_chat_button = driver.find_element(By.ID, "new-chat-button")
        new_chat_button.click()

        input_box = driver.find_element(By.ID, "input_text")
        send_button = driver.find_element(By.CLASS_NAME, "send-button")

        input_box.send_keys("Persistent message")
        send_button.click()

        # Wait for message
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "message"))
        )

        # Reload the page
        driver.refresh()

        # Wait for page to reload and check chats are restored
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "chat-list"))
        )

        # Check that the chat list is populated
        chat_list = driver.find_element(By.ID, "chat-list")
        chats = chat_list.find_elements(By.TAG_NAME, "li")
        assert len(chats) > 0

        # Click on the restored chat
        chats[1].click()

        # Wait for messages to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "message"))
        )

        # Verify message content is restored
        chat_messages = driver.find_element(By.ID, "chat-messages")
        assert "Persistent message" in chat_messages.text

