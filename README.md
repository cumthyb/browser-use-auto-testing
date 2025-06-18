# Browser-Use Auto Testing

This repository contains automated browser testing scripts using the `browser-use` framework, `pytest`, and `allure` for reporting. The tests are designed to interact with web pages, extract data, and validate results using custom actions.

## Project Structure

### Key Files

- **`test_spacex.py`**: Contains the main test for SpaceX website interactions.
- **`src/test_browser_use_base.py`**: Defines the base browser test class.
- **`src/test_browser_use_hooks.py`**: Implements hooks for capturing screenshots and attaching artifacts to Allure reports.
- **`src/test_utils.py`**: Utility functions for setting up directories, saving agent history, and attaching logs to Allure.
- **`pytest.ini`**: Configuration for pytest, including custom markers and Allure settings.
- **`conftest.py`**: Pytest fixtures and hooks for test environment setup.
- **`run_tests.sh`**: Script to install dependencies, run tests, and generate Allure reports.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd browser-use-auto-testing
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
```
playwright install chromium

```

## Running Tests
```
./run_test.sh
```
