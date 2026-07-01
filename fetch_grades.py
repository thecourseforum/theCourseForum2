#!/usr/bin/env python3
"""
Fetch Grade Data from UVA FOIA Grade Distribution Website

This script scrapes grade distribution data from UVA's FOIA Qlik application
and outputs a CSV file compatible with theCourseForum's load_grades command.

INSTALLATION:
    uv sync   # installs selenium (dev group) and pandas from uv.lock

REQUIREMENTS:
    - Chrome browser installed
    - ChromeDriver (auto-managed by selenium 4.6+)

USAGE:
    uv run python fetch_grades.py 2024_fall              # Scrape all sections
    uv run python fetch_grades.py 2024_fall --limit 10   # Scrape only 10 sections (testing)
    uv run python fetch_grades.py 2024_fall --resume     # Resume interrupted scrape

OUTPUT:
    Creates: tcf_website/management/commands/grade_data/csv/<year>_<season>.csv
"""

import argparse
import os
import re
import sys
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ============================================================================
# CONFIGURATION
# ============================================================================

TARGET_URL = "https://qlksnpn-apprd01.eservices.virginia.edu/extensions/FOIAGradeDistribution/FOIAGradeDistribution.html"

# CSS selectors for Qlik filter interface
BTN_TERM = "div[data-testid='collapsed-title-Term']"
BTN_CLASS_NUM = "div[data-testid='collapsed-title-Class Num']"
INPUT_SEARCH = "input[data-testid='search-input-field']"
BTN_CONFIRM = "button[data-testid='actions-toolbar-confirm']"
BTN_CLEAR = "button[data-testid='actions-toolbar-clear']"

# Directory paths (relative to repo root)
SEMESTER_DATA_DIR = "tcf_website/management/commands/semester_data/csv"
GRADE_DATA_DIR = "tcf_website/management/commands/grade_data/csv"

# Season mapping
SEASON_NAMES = {
    "fall": "Fall",
    "spring": "Spring",
    "summer": "Summer",
    "january": "January"
}

# Output CSV columns (must match load_grades.py expectations)
OUTPUT_COLUMNS = [
    "Term Desc", "Subject", "Catalog Number", "Class Title", "Course ID",
    "Primary Instructor Name", "Class Section", "Class Num",
    "Class Academic Group", "Course GPA", "# of Students",
    "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "DFW"
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_text(text: str) -> str:
    """Normalize whitespace in text."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()


def format_instructor_name(name: str) -> str:
    """
    Takes a string of names (potentially multiple) and returns only
    the first name in "Last,First" format.

    Example: "John Smith, Jane Doe" -> "Smith,John"
    """
    if not name or name == "To Be Announced" or pd.isna(name):
        return "..."

    # 1. Split by comma to handle multiple instructors
    # "First1 Last1, First2 Last2" -> ["First1 Last1", " First2 Last2"]
    name_parts = str(name).split(',')

    # 2. Take only the first name in the list
    first_instructor = name_parts[0].strip()

    # 3. Apply the "Last,First" logic to that single name
    parts = first_instructor.split()

    if len(parts) < 2:
        # Still returns placeholder if the first name is incomplete
        return "..."

    last_name = parts[-1]
    first_middle = " ".join(parts[:-1])

    return f"{last_name},{first_middle}"


def init_driver() -> webdriver.Chrome:
    """Initialize a headless Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=options)
    return driver


def set_filter(driver, btn_selector: str, value: str, use_search: bool = False) -> bool:
    """
    Set a filter value in the Qlik interface.

    Args:
        driver: Selenium WebDriver
        btn_selector: CSS selector for the filter button
        value: Value to select
        use_search: Whether to use the search box (for Class Num)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Click the filter button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, btn_selector))
        ).click()

        # If searchable, type in the search box
        if use_search:
            search_box = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, INPUT_SEARCH))
            )
            search_box.clear()
            search_box.send_keys(value)
            time.sleep(1.5)  # Wait for search results

        # Click the matching item
        item_xpath = f"//div[@role='presentation']//span[normalize-space(text())='{value}']"
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, item_xpath))
        ).click()

        # Confirm selection
        try:
            driver.find_element(By.CSS_SELECTOR, BTN_CONFIRM).click()
        except Exception:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()

        time.sleep(1)
        return True

    except Exception:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        return False


def clear_class_filter(driver) -> None:
    """Clear the Class Num filter."""
    try:
        driver.find_element(By.CSS_SELECTOR, BTN_CLASS_NUM).click()
        WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, BTN_CLEAR))
        ).click()
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
    except Exception:
        pass


def clear_term_filter(driver) -> None:
    """Clear the Term filter."""
    try:
        driver.find_element(By.CSS_SELECTOR, BTN_TERM).click()
        WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, BTN_CLEAR))
        ).click()
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
    except Exception:
        pass


def clear_all_filters(driver) -> None:
    """Clear both Class Num and Term filters."""
    clear_class_filter(driver)
    clear_term_filter(driver)


def scrape_section(driver, term: str, class_num: str, instructor: str) -> dict:
    """
    Scrape grade data for a single section.

    Args:
        driver: Selenium WebDriver (already filtered to the section)
        term: Term description (e.g., "2024 Fall")
        class_num: Class number
        instructor: Instructor name in "Last,First" format

    Returns:
        Dictionary with all grade data fields
    """
    data = {
        "Term Desc": term,
        "Class Num": class_num,
        "Subject": "",
        "Catalog Number": "",
        "Class Title": "",
        "Class Section": "",
        "Class Academic Group": "",
        "Course ID": "",  # Not available from FOIA; left empty
        "Primary Instructor Name": instructor,
        "Course GPA": "",
        "# of Students": "",
        "A+": 0, "A": 0, "A-": 0,
        "B+": 0, "B": 0, "B-": 0,
        "C+": 0, "C": 0, "C-": 0,
        "DFW": 0
    }

    try:
        # 1. Scrape table data
        cells = driver.find_elements(By.CSS_SELECTOR, "tr.qv-st-data-row td")
        cell_texts = [clean_text(c.get_attribute("textContent")) for c in cells]

        if len(cell_texts) >= 7:
            data["Class Academic Group"] = cell_texts[0]
            data["Subject"] = cell_texts[1]
            data["Catalog Number"] = cell_texts[2]
            data["Class Section"] = cell_texts[3]
            data["Class Title"] = cell_texts[5]
            data["# of Students"] = cell_texts[6]

        # 2. Scrape GPA from KPI element
        try:
            kpi_label = driver.find_element(
                By.XPATH, "//*[contains(text(), 'Average Course GPA')]"
            )
            kpi_box = kpi_label.find_element(By.XPATH, "./../../..")
            kpi_text = kpi_box.get_attribute("textContent")
            match = re.search(r'(\d\.\d{2})', kpi_text)
            data["Course GPA"] = match.group(1) if match else ""
        except Exception:
            pass

        # 3. Scrape grade distribution from bar chart
        grades_elements = driver.find_elements(
            By.CSS_SELECTOR, "svg[data-key='bar-axis'] text"
        )
        grades_list = [clean_text(el.get_attribute("textContent")) for el in grades_elements]

        counts_elements = driver.find_elements(
            By.CSS_SELECTOR, "svg[data-key='bar-labels'] text"
        )
        counts_list = [clean_text(el.get_attribute("textContent")) for el in counts_elements]

        # Pair grades with counts
        for grade, count in zip(grades_list, counts_list, strict=False):
            if grade in data:
                try:
                    data[grade] = int(count) if count else 0
                except ValueError:
                    data[grade] = 0

        return data

    except Exception as e:
        print(f"    Error scraping section: {e}")
        return None


# ============================================================================
# MAIN LOGIC
# ============================================================================

def load_semester_data(semester_csv: str) -> list[dict]:
    """
    Load section data from semester CSV.

    Skips Independent Study (IND) and Discussion sections, plus
    any zero-credit section.

    Also skips sections the FOIA grade site suppresses and therefore
    has no data for: undergraduate (catalog number < 5000) sections
    with fewer than 10 students, and non-undergraduate sections with
    fewer than 5 students.

    Returns list of dicts with 'class_num' and 'instructor' keys.
    """
    df = pd.read_csv(semester_csv)

    sections = []
    for _, row in df.iterrows():
        section_type = str(row.get("Type", "")).strip()
        units = str(row.get("Units", "")).strip()

        if section_type in ("IND", "Discussion"):
            continue
        if units == "0":
            continue

        try:
            number = int(str(row.get("Number", "")).strip())
        except ValueError:
            number = 0
        try:
            enrollment = int(row.get("Enrollment", 0))
        except (ValueError, TypeError):
            enrollment = 0

        is_undergrad = number < 5000
        if is_undergrad and enrollment < 10:
            continue
        if not is_undergrad and enrollment < 5:
            continue

        class_num = str(row["ClassNumber"])
        instructor_raw = row.get("Instructor1", "")
        instructor = format_instructor_name(instructor_raw) if instructor_raw else ""

        sections.append({
            "class_num": class_num,
            "instructor": instructor
        })

    return sections


def main():
    parser = argparse.ArgumentParser(
        description="Fetch grade data from UVA FOIA Grade Distribution website"
    )
    parser.add_argument(
        "semester",
        help="Semester in format: <year>_<season> (e.g., 2024_fall)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of sections to scrape (for testing)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume scraping, skipping already-scraped Class Nums"
    )

    args = parser.parse_args()

    # Parse and validate semester
    parts = args.semester.split("_")
    if len(parts) != 2:
        print(f"Error: Invalid semester format '{args.semester}'")
        print("Expected format: <year>_<season> (e.g., 2024_fall)")
        sys.exit(1)

    year, season = parts
    season = season.lower()

    if not year.isdigit() or len(year) != 4:
        print(f"Error: Invalid year '{year}'")
        sys.exit(1)

    if season not in SEASON_NAMES:
        print(f"Error: Invalid season '{season}'")
        print(f"Valid options: {', '.join(SEASON_NAMES.keys())}")
        sys.exit(1)

    term = f"{year} {SEASON_NAMES[season]}"

    # Check semester data file exists
    semester_csv = os.path.join(SEMESTER_DATA_DIR, f"{year}_{season}.csv")
    if not os.path.exists(semester_csv):
        print(f"Error: Semester data file not found: {semester_csv}")
        sys.exit(1)

    # Load sections from semester data
    print(f"Loading sections from {semester_csv}...")
    sections = load_semester_data(semester_csv)
    print(f"Found {len(sections)} sections")

    # Handle resume mode
    output_csv = os.path.join(GRADE_DATA_DIR, f"{year}_{season}.csv")
    existing_class_nums = set()

    if args.resume and os.path.exists(output_csv):
        existing_df = pd.read_csv(output_csv)
        existing_class_nums = set(existing_df["Class Num"].astype(str).tolist())
        print(f"Resume mode: {len(existing_class_nums)} sections already scraped")

    # Filter sections
    if args.resume:
        sections = [s for s in sections if s["class_num"] not in existing_class_nums]

    if args.limit:
        sections = sections[:args.limit]
        print(f"Limiting to {args.limit} sections")

    print(f"{len(sections)} sections to scrape")

    if not sections:
        print("No sections to scrape. Done.")
        return

    # Initialize browser
    print("\nInitializing Chrome driver...")
    driver = init_driver()
    results = []

    try:
        print(f"Navigating to {TARGET_URL}...")
        driver.get(TARGET_URL)
        time.sleep(5)  # Wait for Qlik app to load

        for i, section in enumerate(sections):
            class_num = section["class_num"]
            instructor = section["instructor"]

            print(f"[{i+1}/{len(sections)}] Class Num {class_num}...", end=" ", flush=True)

            # Reset all filters before each section
            clear_all_filters(driver)

            # Set class number filter
            if not set_filter(driver, BTN_CLASS_NUM, class_num, use_search=True):
                print("Class Num NOT FOUND")
                continue

            # Set term filter
            if not set_filter(driver, BTN_TERM, term, use_search=False):
                print("Class Num NOT FOUND for term")
                continue

            time.sleep(2)  # Wait for data to load

            # Scrape data
            row_data = scrape_section(driver, term, class_num, instructor)

            if row_data and row_data.get("Subject"):
                results.append(row_data)
                print(f"OK - {row_data['Subject']} {row_data['Catalog Number']} (GPA: {row_data['Course GPA']})")
            else:
                print("NO DATA")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving partial results...")
    except Exception as e:
        print(f"\n\nCRITICAL ERROR: {e}")
        print("Saving partial results...")
    finally:
        driver.quit()

    # Write results
    if results:
        df = pd.DataFrame(results)

        # Ensure all columns exist and are in correct order
        for col in OUTPUT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[OUTPUT_COLUMNS]

        # Create output directory if needed
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)

        # Write (append if resuming)
        if args.resume and os.path.exists(output_csv):
            df.to_csv(output_csv, mode='a', header=False, index=False)
        else:
            df.to_csv(output_csv, index=False)

        print(f"\nSaved {len(results)} rows to {output_csv}")
    else:
        print("\nNo results to save.")


if __name__ == "__main__":
    main()
