"""Tests for Browse page."""

import unittest

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from utils_selenium_test import *

class BrowseTests(unittest.TestCase):
    """Tests for Browse page."""

    def setUp(self):
        setup(self)

    def test_navigate_to_browse_from_landing(self):
        """Test to ensure navigation to Browse page is successful."""

        # Click browse button from landing page
        self.driver.find_element_by_id("browse").click()

        # Wait until browse page shows up (max time 3 seconds)
        timeout = 3
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(
                (By.ID, "browse-title")))

        # Ensure title is correct
        title = self.driver.find_element_by_id("browse-title")
        self.assertEqual(title.text, "Browse by Department")

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    configure_driver(BrowseTests)
    unittest.main()