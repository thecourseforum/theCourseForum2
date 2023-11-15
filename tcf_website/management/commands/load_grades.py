# pylint: disable=fixme,invalid-name
"""
Loads grade data from CSV files into database
"""
import os
import re

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from tqdm import tqdm

from tcf_website.models import (
    Course,
    CourseGrade,
    CourseInstructorGrade,
    Instructor,
)

# Location of our grade data CSVs
DATA_DIR = "tcf_website/management/commands/grade_data/csv/"


class Command(BaseCommand):
    """
    How To Use: Run python3 manage.py load_grades ALL_DANGEROUS to load all grades
    in the tcf_website/management/commands/grade_data/csv/ directory.
    This should take less than a minute to load all the grades
    """

    help = "Imports FOIAed grade data files into PostgreSQL database"

    def __init__(
        self, stdout=None, stderr=None, no_color=False, force_color=False
    ):
        super().__init__(stdout, stderr, no_color, force_color)

        # Initialize some variables that get used everywhere

        # Dict mapping instructor first/last name to their ID in our database
        # We used to be able to include email, but the UVA dataset doesn't include it!
        # This is pretty risky if instructors have the exact same name, so yikes
        # TODO: figure out how to differentiate (maybe by classes taught?)
        self.instructors = {
            (obj["first_name"], obj["last_name"]): obj["id"]
            for obj in Instructor.objects.values(
                "id", "first_name", "last_name"
            )
        }

        # Dict mapping course mnemonic in a tuple to its ID in our database
        self.courses = {
            (obj["subdepartment__mnemonic"], obj["number"]): obj["id"]
            for obj in Course.objects.values(
                "id", "number", "subdepartment__mnemonic"
            )
        }

        # Default level of verbosity
        self.verbosity = 0

        # Whether to suppress tqdm
        self.suppress_tqdm = False

        self.course_grades = {}
        self.course_instructor_grades = {}

    def add_arguments(self, parser):
        """Standard Django function implementation - defines command-line parameters"""
        # The only required argument at the moment
        # A previous author wrote that reloading all semesters can be dangerous
        # Not sure why, but requiring `ALL_DANGEROUS` to honor the help text
        parser.add_argument(
            "semester",
            help=(
                'Semester to update grades (e.g. "2019_FALL").\nIf you wish'
                " to reload all semesters (potentially dangerous!) then put "
                '"ALL_DANGEROUS" as the value of this argument.\nNote that '
                "only a single semester is allowed."
            ),
            type=str,
        )

        parser.add_argument(
            "--suppress-tqdm",
            action="store_true",
            help="Suppress the tqdm loading bars",
        )

        parser.add_argument(
            "--log-missing-instructors",
            action="store_true",
            help="Create a .txt file with missing instructors",
        )

    def handle(self, *args, **options):
        """Standard Django function implementation - runs when this command is executed."""
        self.verbosity = options["verbosity"]
        self.suppress_tqdm = options["suppress_tqdm"]

        if self.verbosity > 0:
            print("Step 1: Fetch Course and Instructor data for later use")
        semester = options["semester"]
        if semester == "ALL_DANGEROUS":
            # ALL_DANGEROUS removes all existing data
            CourseGrade.objects.all().delete()
            CourseInstructorGrade.objects.all().delete()

            # Loads every data CSV file in /grade_data/csv with exceptions
            for file in sorted(os.listdir(DATA_DIR)):
                if self.verbosity == 3:
                    print("Loading data from", file)
                # Ignore temp files (start with '~' on Windows, '.' otherwise) and test data
                if file[0] not in (".", "~") and ".csv" in file:
                    self.load_semester_file(file)
        else:
            self.load_semester_file(f"{semester.lower()}.csv")
        self.load_dict_into_models()

    def clean(self, df):
        """Cleans data.
        Because of FERPA redactions (see wiki for details), there are 3 types of usable rows:
        1. Contains both average/total enrolled and distribution (counts of A, B, C, etc.)
        2. Contains only average/total enrolled, with distribution deleted
        3. Contains only distribution, with no average.

        The only case we drop is when there is no data in any relevant column.
        """
        df.replace("-", np.NaN, inplace=True)

        df.dropna(
            how="all",
            subset=[
                "A+",
                "A",
                "A-",
                "B+",
                "B",
                "B-",
                "C+",
                "C",
                "C-",
                "DFW",
                "# of Students",
                "Course GPA",
            ],
            inplace=True,
        )

        df.fillna(0, inplace=True)

        # Not quite sure how much data this actually applies to,
        # as UVA data is much more reliable than the old VAGrades data
        # Filter out data with missing instructor (represented by ...)
        return df[df["Primary Instructor Name"] != "..."]

    def load_semester_file(self, file):
        """Given a file name, cleans + loads its data into the global grade data dicts."""
        df = self.clean(pd.read_csv(os.path.join(DATA_DIR, file)))
        if self.verbosity > 0:
            print(f"Found {df.size} sections in {file}")

        for _, row in tqdm(
            df.iterrows(), total=df.shape[0], disable=self.suppress_tqdm
        ):
            if self.verbosity == 3:
                print(str(row).encode("ascii", "ignore").decode("ascii"))
            self.load_row_into_dict(row)
        if self.verbosity > 0:
            print(f"Done loading {file}")

    def load_row_into_dict(self, row):
        """
        Loads data from a given row into the global dicts
        course_grades and course_instructor_grades
        """
        # Columns are processed left to right, with one exception

        # 'Term Desc' column is unused because we only care about aggregate across semesters
        # Might want to display semester-by-semester metrics too? Would have to change this

        subdepartment = row["Subject"]
        # `Catalog Number` is handled with all other numerical data in the try block below

        title = row["Class Title"]
        # Key assumption: names are in the format `LAST,FIRST MIDDLE`
        try:
            last_name, first_and_middle = row["Primary Instructor Name"].split(
                ","
            )
            first_name = first_and_middle.split(" ")[0]
        except ValueError as e:
            # Script should stop if name that doesn't fit this pattern is given
            if self.verbosity > 0:
                print(f"full name is {row['Primary Instructor Name']}")
            raise ValueError(
                f"{row['Primary Instructor Name']} doesn't meet our assumption "
                f"about instructor name format."
            ) from e

        # 'Class Section' column is unused
        try:
            number = int(re.sub("[^0-9]", "", str(row["Catalog Number"])))

            semester_grades = [
                int(x)
                for x in [
                    row["A+"],
                    row["A"],
                    row["A-"],
                    row["B+"],
                    row["B"],
                    row["B-"],
                    row["C+"],
                    row["C"],
                    row["C-"],
                    row["DFW"],
                ]
            ]

            # With no redactions, tracking these aggregate data would be unnecessary, but
            # we need these because DFW is vague and small class distributions are deleted.
            # We also need to handle the edge case where these fields are empty, which
            # clean() fills as 0.
            average = float(row["Course GPA"])
            total_enrolled = max(
                int(row["# of Students"]), sum(semester_grades)
            )

            # Add aggregate stats to end of array
            semester_grades.append(total_enrolled)
            semester_grades.append(average)

        except (TypeError, ValueError) as e:
            if self.verbosity > 0:
                print(row)
                print(e)
            raise e
        # No error casting values to float/int, so continue
        # Identifiers are tuple keys to grade data dictionaries
        course_identifier = (subdepartment, number, title)
        course_instructor_identifier = (
            subdepartment,
            number,
            first_name,
            last_name,
        )

        # Helper function because we basically do the same thing twice
        def add_entry(data_dict, identifier):
            # Load this semester into dictionary
            if identifier in data_dict:
                # Average needs to be computed separately instead of incrementing
                prev_data = data_dict[identifier]
                prev_total_enrolled = prev_data[-2]
                prev_average = prev_data[-1]

                # If both are not zero, then update with weighted formula
                if prev_average and average:
                    new_average = (
                        prev_average * prev_total_enrolled
                        + average * total_enrolled
                    ) / (prev_total_enrolled + total_enrolled)
                    data_dict[identifier][-1] = new_average
                # If only old average is zero, then set it to new average
                elif average:
                    data_dict[identifier][-1] = average
                # Any situation where new average is None, do nothing to average
                # The distribution itself can be incremented normally in all cases
                data_dict[identifier][-2] += total_enrolled
                for i in range(len(semester_grades) - 2):
                    data_dict[identifier][i] += semester_grades[i]
            else:
                data_dict[identifier] = semester_grades.copy()

        add_entry(self.course_grades, course_identifier)
        add_entry(self.course_instructor_grades, course_instructor_identifier)

    def load_dict_into_models(self):
        """Converts dictionaries to real instances of CourseGrade and CourseInstructorGrade.

        Given a course or course-instructor pair and its corresponding grade distribution,
        calculates weighted GPA average and total enrolled students and then uses all of those
        as parameters to create new CourseGrade and CourseInstructorGrade instances.
        """
        if self.verbosity > 0:
            print("Step 2: Bulk-create CourseGrade instances")

        # Load course_grades data from dicts and create model instances
        unsaved_cg_instances = []
        for row in tqdm(self.course_grades, disable=self.suppress_tqdm):
            course_grade_params = self.set_grade_params(
                row, is_instructor_grade=False
            )
            unsaved_cg_instance = CourseGrade(**course_grade_params)
            unsaved_cg_instances.append(unsaved_cg_instance)

        # bulk_create is much more efficient than creating them separately
        CourseGrade.objects.bulk_create(unsaved_cg_instances)
        if self.verbosity > 0:
            print("Done creating CourseGrade instances")
            print("Step 3: Bulk-create CourseInstructorGrade instances")

        # Load course_instructor_grades data from dicts and create model instances
        unsaved_cig_instances = []
        for row in tqdm(
            self.course_instructor_grades, disable=self.suppress_tqdm
        ):
            course_instructor_grade_params = self.set_grade_params(
                row, is_instructor_grade=True
            )
            unsaved_cig_instance = CourseInstructorGrade(
                **course_instructor_grade_params
            )
            unsaved_cig_instances.append(unsaved_cig_instance)
        CourseInstructorGrade.objects.bulk_create(unsaved_cig_instances)
        if self.verbosity > 0:
            print("Done creating CourseInstructorGrade instances")

    def set_grade_params(self, row, is_instructor_grade):
        """Creates dict of params to be used as parameters
        in creating CourseGrade/CourseInstructorGrade instances.
        Helper function for load_dict_into_models()"""
        if is_instructor_grade:
            data = self.course_instructor_grades[row]
        else:
            data = self.course_grades[row]

        course_grade_params = {
            "course_id": self.courses.get(row[:2]),
            "a_plus": data[0],
            "a": data[1],
            "a_minus": data[2],
            "b_plus": data[3],
            "b": data[4],
            "b_minus": data[5],
            "c_plus": data[6],
            "c": data[7],
            "c_minus": data[8],
            "dfw": data[9],
            "total_enrolled": data[10],
            "average": data[11] if data[11] > 0 else None,
        }

        if is_instructor_grade:
            course_grade_params["instructor_id"] = self.instructors.get(row[2:])
        return course_grade_params
