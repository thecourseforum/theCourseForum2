"""
Django management command to fetch data from SIS API and convert it into a CSV file.
"""

import csv
import json
import os

import backoff
import requests
from django.core.management.base import BaseCommand
from tqdm import tqdm

COURSE_DATA_DIR = "tcf_website/management/commands/semester_data/sis_csv/"
SEASON_NUMBERS = {"fall": 8, "summer": 6, "spring": 2, "january": 1}


class Command(BaseCommand):
    """
    Command to fetch data from SIS API for the specified semester and save it to a CSV file.

    Usage:
    docker exec -it tcf_django python3 manage.py fetch_data "<year>_<season>"

    Example:
    docker exec -it tcf_django python3 manage.py fetch_data "2023_spring"
    """

    help = "Fetches data from SIS API for the specified semester and saves it to a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "semester", type=str, help='<year>_<season>(e.g., "2023_spring")'
        )

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    )
    def handle(self, *args, **kwargs):
        year, season = kwargs["semester"].split("_")
        season = season.lower()
        year_code = str(year)[-2:]
        sem_code = f"1{year_code}{SEASON_NUMBERS.get(season)}"  # 1 represents 21st century in querying

        self.stdout.write(f"Fetching course data for {year} {season}...")

        filename = f"{year}_{season}.csv"
        csv_path = os.path.join(COURSE_DATA_DIR, filename)
        if os.path.exists(csv_path):
            os.remove(csv_path)

        semester_url = (
            f"https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/"
            f"WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?"
            f"institution=UVA01&term={sem_code}&page="
        )

        all_classes = []
        page = 1
        while True:
            self.stdout.write(f"\nFetching page {page}...")
            page_url = semester_url + str(page)
            try:
                response = requests.get(page_url, timeout=300)
                page_data = json.loads(response.text)
            except requests.exceptions.RequestException as e:
                self.stderr.write(f"An error occurred: {e}")
                break

            if not page_data:
                break

            for course in tqdm(page_data):
                class_data = self.compile_course_data(
                    course["class_nbr"], sem_code
                )
                if class_data:
                    all_classes.append(class_data)
            self.write_to_csv(all_classes, csv_path)
            all_classes = []
            page += 1

        self.stdout.write(self.style.SUCCESS("Data fetching complete."))

    @staticmethod
    def compile_course_data(course_number, sem_code):
        """
        Compiles course data from SIS API response.

        :param course_number: The course number.
        :param sem_code: The semester code.
        :return: Dictionary containing course information.
        """
        url = (
            f"https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/"
            f"WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassDetails?"
            f"institution=UVA01&term={sem_code}&class_nbr={course_number}"
        )

        try:
            response = requests.get(url, timeout=300)
        except requests.exceptions.RequestException:
            return None

        data = json.loads(response.text)
        if not data:
            return None

        class_details = data["section_info"]["class_details"]
        meetings = {0: None, 1: None, 2: None, 3: None}

        for index, meeting in enumerate(data["section_info"]["meetings"]):
            if index > 3:
                break
            meetings[index] = meeting

        class_availability = data["section_info"]["class_availability"]

        course_dictionary = {
            "ClassNumber": course_number,
            "Mnemonic": class_details["subject"],
            "Number": class_details["catalog_nbr"],
            "Section": class_details["class_section"],
            "Type": {
                "LEC": "Lecture",
                "DIS": "Discussion",
                "LAB": "Laboratory",
            }.get(class_details["component"], class_details["component"]),
            "Units": class_details["units"][
                0 : class_details["units"].find("units") - 1
            ],
            "Instructor1": (
                ", ".join(
                    instructor["name"]
                    for instructor in meetings.get(0)["instructors"]
                    if instructor["name"] != "-"
                )
                if meetings.get(0)
                else ""
            ),
            "Days1": (
                meetings.get(0)["meets"]
                if meetings.get(0)["meets"] != "-"
                else "TBA"
            ),
            "Room1": (
                meetings.get(0)["room"]
                if meetings.get(0)["room"] != "-"
                else "TBA"
            ),
            "MeetingDates1": (
                meetings.get(0)["date_range"] if meetings.get(0) else ""
            ),
            "Instructor2": (
                ", ".join(
                    instructor["name"]
                    for instructor in meetings.get(1)["instructors"]
                    if instructor["name"] != "-"
                )
                if meetings.get(1)
                else ""
            ),
            "Days2": meetings.get(1)["meets"] if meetings.get(1) else "",
            "Room2": meetings.get(1)["room"] if meetings.get(1) else "",
            "MeetingDates2": (
                meetings.get(1)["date_range"] if meetings.get(1) else ""
            ),
            "Instructor3": (
                ", ".join(
                    instructor["name"]
                    for instructor in meetings.get(2)["instructors"]
                    if instructor["name"] != "-"
                )
                if meetings.get(2)
                else ""
            ),
            "Days3": meetings.get(2)["meets"] if meetings.get(2) else "",
            "Room3": meetings.get(2)["room"] if meetings.get(2) else "",
            "MeetingDates3": (
                meetings.get(2)["date_range"] if meetings.get(2) else ""
            ),
            "Instructor4": (
                ", ".join(
                    instructor["name"]
                    for instructor in meetings.get(3)["instructors"]
                    if instructor["name"] != "-"
                )
                if meetings.get(3)
                else ""
            ),
            "Days4": meetings.get(3)["meets"] if meetings.get(3) else "",
            "Room4": meetings.get(3)["room"] if meetings.get(3) else "",
            "MeetingDates4": (
                meetings.get(3)["date_range"] if meetings.get(3) else ""
            ),
            "Title": class_details["course_title"],
            "Topic": class_details["topic"],
            "Status": class_details["status"],
            "Enrollment": class_availability["enrollment_total"],
            "EnrollmentLimit": class_availability["class_capacity"],
            "Waitlist": class_availability["wait_list_total"],
            "Description": data["section_info"]["catalog_descr"][
                "crse_catalog_description"
            ]
            .replace("\n", " ")
            .replace("\r", " "),
        }
        return course_dictionary

    @staticmethod
    def write_to_csv(course_list, csv_path):
        """
        Writes course data to a CSV file.

        :param course_list: List of dictionaries containing course information.
        :param csv_path: Path to the CSV file.
        """
        fieldnames = list(course_list[0].keys())
        with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()
            for course in course_list:
                writer.writerow(course)
