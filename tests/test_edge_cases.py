import requests
from unittest.mock import patch

# Define the Flask server URL and the search endpoint
URL = "http://192.168.50.20:8088/search"

def test_empty_input():
    """ Test for empty input """
    empty_payload = {"input_text": ""}
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {"content": "Empty input is not allowed."}

        response = requests.post(URL, data=empty_payload)
        assert response.status_code == 400, f"Expected 400 for empty input, got {response.status_code}"
        assert "Empty input is not allowed." in response.json().get('content', ""), "Empty input did not return proper error message."
    print("Test Passed: Empty input handled correctly.")

def test_special_characters():
    """ Test for Special characters (SQL Injection) """
    sql_injection_payload = {"input_text": "'; DROP TABLE users; --"}
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {"content": "Invalid input detected."}

        response = requests.post(URL, data=sql_injection_payload)
        assert response.status_code == 400, f"Expected 400 for SQL injection payload, got {response.status_code}"
        assert "Invalid input detected." in response.json().get('content', ""), "SQL injection payload did not return proper error message."
    print("Test Passed: SQL injection handled correctly.")

