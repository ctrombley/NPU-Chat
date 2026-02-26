import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from npuchat import create_app

@pytest.fixture(scope='function')
def driver(server):
    """
    Pytest fixture to initialize and teardown Selenium WebDriver.
    """
    # Configure Selenium WebDriver with Headless Chrome
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument('--window-size=1200,800')

    driver = webdriver.Chrome(options=options)
    yield driver  # Provide the fixture to tests
    driver.quit()  # Ensure the browser quits after tests

@pytest.fixture(scope='function')
def client():
    """
    Pytest fixture to provide a Flask test client.
    """
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

