from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import unittest
import sys

class SeleniumTests(unittest.TestCase):
    def setUp(self):
        # WebDriverWait
        # wait = new
        # WebDriverWait(webDriver, timeoutInSeconds);
        # wait.until(ExpectedConditions.visibilityOfElementLocated(By.id < locator >));
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')

        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        self.driver.get(self.local_host)
        thank_you_button = self.driver.find_elements_by_id("thankYouButton")
        if len(thank_you_button) == 1:
            thank_you_button.click()


    def test_navigate_to_browse_from_landing(self):
        self.driver.find_element_by_id("browse").click()

    def tearDown(self):
        self.driver.quit()


if __name__ == "__main__":
    # Default Arguments
    SeleniumTests.headless = True
    SeleniumTests.local_host = "localhost:8000"

    # Can specify one or both arguments
    if len(sys.argv) == 2:
        if sys.argv[1] == "show":
            SeleniumTests.headless = False
            sys.argv.pop()
        else:
            SeleniumTests.local_host = sys.argv.pop()
    elif len(sys.argv) == 3:
        if str(sys.argv[2]) == "show":
            SeleniumTests.headless = False
            sys.argv.pop()
        SeleniumTests.local_host = sys.argv.pop()

    unittest.main()