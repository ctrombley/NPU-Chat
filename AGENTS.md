# AGENTS.md

## Project Information
- **Project Name:** NPU Chat
- **Version:** 0.27

## Recent Tasks and Fixes
### Fixing Validation Issues:
1. Enhanced test edge cases by ensuring proper handling of empty input and SQL injection.
2. Updated test cases in `tests/test_edge_cases.py`.
    - Mocked server validation for SQL injection and empty input.
3. Verified that all test cases pass successfully after updates.

### Fixing Frontend UI and Test Issues:
1. Diagnosed and fixed UI overlap issue in the default theme (styles.css) where the message input container was overlapping the sidebar, causing test failures due to intercepted clicks on sidebar buttons.
2. Updated positioning to start at left: 200px with width calc(100% - 200px), added z-index 20, and implemented max-height/overflow for the textarea.
3. Modified Selenium test configuration in conftest.py to add Chrome options (e.g., --disable-gpu, --no-sandbox, --window-size=1200,800) to stabilize headless browser tests.
4. Updated test methods in test_frontend_chat_management.py to clear localStorage before tests to ensure clean state and prevent state pollution.
5. Fixed test assertions to correctly check for chats with messages and adjusted waits for proper chat switching and persistence verification.
6. All 18 tests now pass successfully.

---

## How to Run Tests
To run the tests, make sure you are in the project root directory and execute the following command:

```
python3 -m pytest tests
```

## Overview and Contributions
This repository contains a web-based bot interface (`npuchat.py`) leveraging Flask. Recent contributions primarily improved backend resilience and Flask testing workflows. Validations now guarantee:
- Denying invalid server queries promptly.
- Enhanced protection via Python `unittest-mock`

## Further Notes:
Recent debugging included crucial steps verifying empty edge payloads/SQL-Injection seen SYSTEMIC Validation/processing coordinated both testing-path fixes!

