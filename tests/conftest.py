import json
import os
import sys

import pytest

# Ensure project root is on sys.path so tests can import npuchat
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from npuchat import create_app

# Try to import selenium; if not available, we'll skip webdriver tests
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
except Exception:
    webdriver = None
    Options = None

@pytest.fixture(scope='function')
def driver():
    """
    Pytest fixture to initialize and teardown Selenium WebDriver.
    Skips the fixture if selenium is not available in the environment.
    """
    if webdriver is None or Options is None:
        pytest.skip("selenium not available, skipping webdriver tests")

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
    app = create_app(run_migrations=False)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# --- JSON:API test helpers ---

JSONAPI_CONTENT_TYPE = 'application/vnd.api+json'

def jsonapi_post(client, url, type_, attrs):
    """POST a JSON:API resource and return the response."""
    return client.post(
        url,
        data=json.dumps({'data': {'type': type_, 'attributes': attrs}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )

def jsonapi_patch(client, url, type_, id_, attrs):
    """PATCH a JSON:API resource and return the response."""
    return client.patch(
        url,
        data=json.dumps({'data': {'type': type_, 'id': id_, 'attributes': attrs}}),
        content_type=JSONAPI_CONTENT_TYPE,
    )

def get_jsonapi_data(response):
    """Parse JSON:API response and return the 'data' field."""
    return json.loads(response.data)['data']

def get_jsonapi_attrs(response):
    """Parse a single-resource JSON:API response and return its attributes."""
    data = get_jsonapi_data(response)
    if isinstance(data, list):
        return data[0]['attributes']
    return data['attributes']

def get_jsonapi_id(response):
    """Parse a single-resource JSON:API response and return its id."""
    data = get_jsonapi_data(response)
    if isinstance(data, list):
        return data[0]['id']
    return data['id']
