from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Configure Selenium to use a headless Chrome browser
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--disable-setuid-sandbox")
options.add_argument("--ignore-certificate-errors")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")
driver = webdriver.Chrome(options=options)

try:
    # Navigate to the Flask server's URL
    url = "http://192.168.50.20:8088"  # Replace with the appropriate Flask server URL
    driver.get(url)

    # Wait for the page to load
    time.sleep(1)

    # Locate the input box by its ID
    input_box = driver.find_element(By.ID, "input_text")

    # Send a test query to the input box
    input_box.send_keys("Hello, how are you?")
    input_box.send_keys(Keys.RETURN)

    # Wait for the response to appear in the chat-messages div
    time.sleep(3)  # Adjust the wait time if necessary

    # Verify the response is displayed in the chat-messages container
    chat_messages = driver.find_element(By.ID, "chat-messages")
    assert "Hello, how are you?" in chat_messages.text

    print("Test Passed: UI interaction verified successfully.")

except Exception as e:
    print(f"Test Failed: {e}")

finally:
    # Close the browser
    driver.quit()

