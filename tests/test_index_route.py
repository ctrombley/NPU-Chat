import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Configure Selenium to use a headless Chrome browser
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

try:
    # Navigate to the index route of the Flask server
    url = "http://192.168.50.20:8088/"  # Verify Flask server is running here
    driver.get(url)

    # Wait for the page to load
    time.sleep(2)

    # Validate key elements on the index page
    chat_container = driver.find_element(By.CLASS_NAME, "chat-container")
    assert chat_container.is_displayed(), "Chat container is not visible on the page."

    input_box = driver.find_element(By.ID, "input_text")
    assert input_box.is_displayed(), "Input text box is not visible on the page."

    send_button = driver.find_element(By.CLASS_NAME, "send-button")
    assert send_button.is_displayed(), "Send button is not visible on the page."

    print("Test Passed: All key elements on the index page are visible and rendered correctly.")

except Exception as e:
    print(f"Test Failed: {e}")

finally:
    # Close the browser
    driver.quit()

