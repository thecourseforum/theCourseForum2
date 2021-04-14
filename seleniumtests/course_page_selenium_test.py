"""Tests for Course page."""

import unittest

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from utils_selenium_test import *

class CoursePageTests(unittest.TestCase):
    """Tests for Course page."""

    def setUp(self):
        setup(self)

    def test_navigate_to_be_course(self):
        """Test to ensure navigation to Course page is successful."""

        # Put CS 2150 in search bar
        search = self.driver.find_element_by_name("q")
        search.send_keys("CS 2150")
        search_button = self.driver.find_element_by_id("search-button")
        search_button.click()

        # Wait until results appear (max time 5 seconds)
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "li.list-group-item")))

        # Choose top result
        results = self.driver.find_elements_by_css_selector("li.list-group-item")
        results[0].click()

        # Wait until Course Page appears (max time 5 seconds)
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(
                (By.ID, "course-code")))

        # Ensure Course code is correct
        pneumonic = self.driver.find_element_by_id("course-code")
        self.assertEqual(pneumonic.text, "CS 2150")

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    configure_driver(CoursePageTests)
    unittest.main()