import json
import csv
import requests

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Fetches data from SIS API for the specified semester and saves it to a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('semester', type=str, help='Semester code (e.g., "1232")')

    def handle(self, *args, **kwargs):
        semester = kwargs['semester']
        self.stdout.write(f"Fetching data for semester {semester}...")

        semester_url = (
            'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.'
            f'FieldFormula.IScript_ClassSearch?institution=UVA01&term={semester}&page='
        )

        all_classes = []
        page = 1
        while True:
            print(page)
            page_url = semester_url + str(page)
            try:
                response = requests.get(page_url)
                page_data = json.loads(response.text)
            except requests.exceptions.RequestException as e:
                self.stderr.write(f'An error occurred: {e}')
                break

            if not page_data:
                break

            for course in page_data:
                class_data = self.compile_course_data(course['class_nbr'], semester)
                if class_data:
                    all_classes.append(class_data)
            self.write_to_csv(all_classes, f"SIS_{semester}")
            all_classes = []
            page += 1

        self.stdout.write(self.style.SUCCESS("Data fetching complete."))

    @staticmethod
    def compile_course_data(course_number, semester):
        url = f"https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH." \
              f"FieldFormula.IScript_ClassDetails?institution=UVA01&term={semester}&class_nbr={course_number}"

        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            return None

        data = json.loads(response.text)
        if not data:
            return None

        class_details = data["section_info"]["class_details"]
        meetings = [None, None, None, None]
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
                "LAB": "Laboratory"
            }.get(class_details["component"], class_details["component"]),
            "Units": class_details["units"][0:class_details["units"].find("units") - 1],
            "Instructor1": ", ".join(
                instructor["name"] for instructor in meetings[0]["instructors"] if instructor["name"] != "-"
            ) if meetings[0] else "",
            "Days1": meetings[0]["meets"] if meetings[0]["meets"] != "-" else "TBA",
            "Room1": meetings[0]["room"] if meetings[0]["room"] != "-" else "TBA",
            "MeetingDates1": meetings[0]["date_range"] if meetings[0] else "",
            "Instructor2": ", ".join(
                instructor["name"] for instructor in meetings[1]["instructors"] if instructor["name"] != "-"
            ) if meetings[1] else "",
            "Days2": meetings[1]["meets"] if meetings[1] else "",
            "Room2": meetings[1]["room"] if meetings[1] else "",
            "MeetingDates2": meetings[1]["date_range"] if meetings[1] else "",
            "Instructor3": ", ".join(
                instructor["name"] for instructor in meetings[2]["instructors"] if instructor["name"] != "-"
            ) if meetings[2] else "",
            "Days3": meetings[2]["meets"] if meetings[2] else "",
            "Room3": meetings[2]["room"] if meetings[2] else "",
            "MeetingDates3": meetings[2]["date_range"] if meetings[2] else "",
            "Instructor4": ", ".join(
                instructor["name"] for instructor in meetings[3]["instructors"] if instructor["name"] != "-"
            ) if meetings[3] else "",
            "Days4": meetings[3]["meets"] if meetings[3] else "",
            "Room4": meetings[3]["room"] if meetings[3] else "",
            "MeetingDates4": meetings[3]["date_range"] if meetings[3] else "",
            "Title": class_details["course_title"],
            "Topic": class_details["topic"],
            "Status": class_details["status"],
            "Enrollment": class_availability["enrollment_total"],
            "EnrollmentLimit": class_availability["class_capacity"],
            "Waitlist": class_availability["wait_list_total"],
            "Description": data["section_info"]["catalog_descr"]["crse_catalog_description"]
                             .replace("\n", " ").replace("\r", " ")
        }
        return course_dictionary

    @staticmethod
    def write_to_csv(course_list, filename):
        fieldnames = list(course_list[0].keys())
        csv_filename = filename + ".csv"
        with open(csv_filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()
            for course in course_list:
                writer.writerow(course)
