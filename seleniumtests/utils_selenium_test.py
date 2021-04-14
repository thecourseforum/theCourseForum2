"""Common testing utilities."""

import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from webdriver_manager.chrome import ChromeDriverManager

def configure_driver(obj):
    """Configure Web Driver with correct settings from command line"""

    obj.headless = True
    obj.local_host = "http://localhost:8000/"

    # Instructions:
    # -After ./precommit.sh you can specify 1, 2, or no arguments
    # -To have browser appear: ./precommit show
    # -To specify different local host: ./precommit <local host>
    # -To specify both: ./precommit show <url>
    # -Default values: local host = "http://localhost:8000/", headless = True (order does not matter)
    if len(sys.argv) == 2:
        if sys.argv[1] == "show":
            obj.headless = False
            sys.argv.pop()
        else:
            obj.local_host = sys.argv.pop()

    elif len(sys.argv) == 3:
        if str(sys.argv[2]) == "show":
            obj.headless = False
            sys.argv.pop()
            obj.local_host = sys.argv.pop()
        elif str(sys.argv[1]) == "show":
            obj.headless = False
            obj.local_host = sys.argv.pop()
            sys.argv.pop()

    chrome_options = Options()
    if obj.headless: # Headless means the browser does not appear
        chrome_options.add_argument('--headless')

    obj.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

def setup(obj):
    """Navigate to url and get rid of welcome modal"""
    obj.driver.get(obj.local_host)
    thank_you_button = obj.driver.find_elements_by_id("thankYouButton")
    if len(thank_you_button) == 1:
        thank_you_button[0].click()