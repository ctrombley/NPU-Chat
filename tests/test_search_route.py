import requests

# Define the Flask server URL and the search endpoint
URL = "http://192.168.50.20:8088/search"

# Valid data payload
valid_payload = {
    "input_text": "What is the capital of France?"
}

# Invalid data payload (missing input_text field)
invalid_payload = {}

try:
    # Test 1: Valid data
    response = requests.post(URL, data=valid_payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "Paris" in response.text or "content" in response.json()['content'], "Valid response did not include expected content."
    print("Test Passed: Valid POST data handled correctly.")

    # Test 2: Invalid data
    response = requests.post(URL, data=invalid_payload)
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert "Invalid or missing input" in response.text or "Invalid" in response.json()['content'], "Invalid response did not return proper error message."
    print("Test Passed: Invalid POST data handled with proper error response.")

except Exception as e:
    print(f"Test Failed: {e}")

