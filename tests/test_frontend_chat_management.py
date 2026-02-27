import threading
import time

import pytest
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import Config
from npuchat import create_app

config = Config()
BINDING_ADDRESS = '127.0.0.1'
BINDING_PORT = config.BINDING_PORT


def setup_function():
    # Ensure a clean DB and chat files before each test
    import glob
    import os

    # Remove DB file
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chats.db')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    # Remove all chat JSON files
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    for f in glob.glob(os.path.join(data_dir, 'chat-*.json')):
        try:
            os.remove(f)
        except Exception:
            pass

@pytest.fixture(scope='session', autouse=True)
def server():
    app = create_app()
    def run_app():
        app.run(host=BINDING_ADDRESS, port=BINDING_PORT, debug=False, use_reloader=False)
    server_thread = threading.Thread(target=run_app)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(5)  # Wait for server to start
    yield

class TestFrontendChatManagement:
    """Test class for frontend chat management functionality"""

    def test_new_chat_creation(self, driver):
        """Test creating a new chat"""
        driver.get(f"http://{BINDING_ADDRESS}:{BINDING_PORT}/")
        driver.execute_script("localStorage.clear();")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[text()='New Chat']"))
        )

        # Get initial chat count
        chat_list = driver.find_element(By.CSS_SELECTOR, "ul")
        initial_chats = chat_list.find_elements(By.TAG_NAME, "li")

        # Click new chat button
        new_chat_button = driver.find_element(By.XPATH, "//button[text()='New Chat']")
        new_chat_button.click()

        # Handle the prompt
        alert = WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert.send_keys("Test Chat")
        alert.accept()

        # Wait for new chat to appear
        WebDriverWait(driver, 5).until(
            lambda d: len(d.find_element(By.CSS_SELECTOR, "ul").find_elements(By.TAG_NAME, "li")) > len(initial_chats)
        )

        # Verify new chat was created
        updated_chats = chat_list.find_elements(By.TAG_NAME, "li")
        assert len(updated_chats) == len(initial_chats) + 1

        # Verify chat messages area is empty for new chat
        chat_messages = driver.find_element(By.CSS_SELECTOR, ".chat-messages")
        assert chat_messages.text.strip() == ""

    def test_chat_switching(self, driver):
        """Test switching between chats"""
        driver.get(f"http://{BINDING_ADDRESS}:{BINDING_PORT}/")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[text()='New Chat']"))
        )

        # Create first chat and send a message
        new_chat_button = driver.find_element(By.XPATH, "//button[text()='New Chat']")
        new_chat_button.click()

        alert = WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert.send_keys("First Chat")
        alert.accept()

        input_box = driver.find_element(By.CSS_SELECTOR, "textarea[name='input_text']")
        send_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        input_box.click()
        input_box.send_keys("Message in first chat")
        WebDriverWait(driver, 5).until(
            lambda d: not d.find_element(By.CSS_SELECTOR, "button[type='submit']").get_attribute("disabled")
        )
        send_button.click()

        # Wait for message to appear
        WebDriverWait(driver, 5).until(
            lambda d: "Message in first chat" in d.find_element(By.CSS_SELECTOR, ".chat-messages").text
        )

        # Create second chat
        new_chat_button.click()

        alert = WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert.send_keys("Second Chat")
        alert.accept()

        # Re-find elements after DOM update
        input_box = driver.find_element(By.CSS_SELECTOR, "textarea[name='input_text']")
        send_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        # Send different message in second chat
        input_box.send_keys("Message in second chat")
        send_button.click()

        # Wait for message to appear
        WebDriverWait(driver, 5).until(
            lambda d: "Message in second chat" in d.find_element(By.CSS_SELECTOR, ".chat-messages").text
        )

        # Switch back to first chat
        chat_list = driver.find_element(By.CSS_SELECTOR, "ul")
        chats = chat_list.find_elements(By.TAG_NAME, "li")
        chats[0].click()  # Click first created chat

        # Wait for chat to switch
        WebDriverWait(driver, 5).until(
            lambda d: "Message in first chat" in d.find_element(By.CSS_SELECTOR, ".chat-messages").text
        )

        # Verify we're back to first chat's messages
        current_messages = driver.find_element(By.CSS_SELECTOR, ".chat-messages").text
        assert "Message in first chat" in current_messages
        assert "Message in second chat" not in current_messages

    def test_local_storage_persistence(self, driver):
        """Test that chats persist in localStorage"""
        # Note: Since we switched to server-side, this test may need adjustment or removal
        pytest.skip("Test needs update for server-side persistence")

    def test_chat_persistence_across_page_reload(self, driver):
        """Test that chats persist across page reloads"""
        driver.get(f"http://{BINDING_ADDRESS}:{BINDING_PORT}/")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[text()='New Chat']"))
        )

        # Create a chat and send a message
        new_chat_button = driver.find_element(By.XPATH, "//button[text()='New Chat']")
        new_chat_button.click()

        alert = WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert.send_keys("Persistent Chat")
        alert.accept()

        input_box = driver.find_element(By.CSS_SELECTOR, "textarea[name='input_text']")
        send_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        input_box.send_keys("Persistent message")
        send_button.click()

        # Wait for message
        WebDriverWait(driver, 5).until(
            lambda d: "Persistent message" in d.find_element(By.CSS_SELECTOR, ".chat-messages").text
        )

        # Reload the page
        driver.refresh()

        # Wait for page to reload and check chats are restored
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul"))
        )

        # Check that the chat list is populated
        chat_list = driver.find_element(By.CSS_SELECTOR, "ul")
        chats = chat_list.find_elements(By.TAG_NAME, "li")
        assert len(chats) > 0

        # Click on the restored chat
        chats[0].click()

        # Wait for messages to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "message"))
        )

        # Verify message content is restored
        chat_messages = driver.find_element(By.CSS_SELECTOR, ".chat-messages")
        assert "Persistent message" in chat_messages.text

