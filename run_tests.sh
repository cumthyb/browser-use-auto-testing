#!/bin/bash
echo "Installing requirements..."
pip install -r requirements.txt

echo "Installing Playwright browsers..."
playwright install chromium

# rm -rf allure-report allure-results
# mkdir allure-report allure-results

echo "Running tests..."
pytest test_spacex.py --alluredir=allure-results -v

# echo "Generating Allure report..."
allure generate allure-results --clean -o allure-report

# echo "Opening Allure report..."
allure open allure-report