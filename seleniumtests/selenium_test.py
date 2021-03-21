from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import unittest


class SeleniumTests(unittest.TestCase):
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    def test_one(self):
        self.driver.get("https://thecourseforum.com/")
        self.driver.quit()
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
