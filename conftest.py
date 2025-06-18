import pytest
import asyncio
import allure
from datetime import datetime
import os

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def test_environment_setup():
    """Setup test environment information for Allure reports"""
    # Environment info is set via environment.properties file in allure-results
    pass

def pytest_configure(config):
    """Configure pytest with custom settings"""
    # Ensure allure results directory exists
    allure_dir = config.getoption("--alluredir")
    if allure_dir:
        os.makedirs(allure_dir, exist_ok=True)
        
        # Create environment.properties file for Allure
        env_file = os.path.join(allure_dir, "environment.properties")
        with open(env_file, "w") as f:
            f.write("Browser=Chromium\n")
            f.write("OS=MacOS\n")
            f.write("Python.Version=3.12+\n")
            f.write("LLM=GPT-4o\n")
            f.write("Browser-Use=0.2.0\n")
            f.write("Test.Framework=Pytest + Browser-Use + Allure\n")
            f.write(f"Test.Date={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach screenshot on test failure"""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        # Test failed, screenshot should already be captured in test
        allure.attach(
            f"Test failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            name="failure_timestamp",
            attachment_type=allure.attachment_type.TEXT
        )
