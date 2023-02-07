import os
import pandas as pd
import re

from django.core.management.base import BaseCommand
from tcf_website.models import *

from tqdm import tqdm


class Command(BaseCommand):
    """
    How To Use: Run python3 manage.py load_grades to load all grades
    in the tcf_website/management/commands/grade_data/csv/ directory.
    This should take ~20 min to run to load all the grades
    """
    help = 'Imports FOIAed grade data files into PostgreSQL database'

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        # Initialize some variables that get used everywhere

        # Dict mapping instructor first/last name to their ID in our database
        # We used to be able to include email, but the UVA dataset doesn't include it!
        # This is pretty risky if instructors have the exact same name, so yikes
        # TODO: figure out how to differentiate (maybe by classes taught?)
        self.instructors = {
            (obj['first_name'], obj['last_name']): obj['id']
            for obj in Instructor.objects.values('id', 'first_name',
                                                 'last_name')
        }

        # Dict mapping course mnemonic in a tuple to its ID in our database
        self.courses = {
            (obj['subject__mnemonic'], obj['number']): obj['id']
            for obj in Course.objects.values('id', 'number',
                                             'subject__mnemonic')
        }

        # Location of our grade data CSVs
        self.data_dir = 'tcf_website/management/commands/grade_data/csv/'

        # Default level of verbosity
        self.verbosity = 0

        # Whether or not to suppress tqdm
        self.suppress_tqdm = False

        self.course_grades = {}
        self.course_instructor_grades = {}

        # Set of instructors that are in the data but not in the database
        self.missing_instructors = set()

        # Whether or not to log those missing instructors in a txt
        self.log_missing_instructors = False

    def add_arguments(self, parser):
        """Standard Django function implementation - defines command-line parameters"""
        # The only required argument at the moment
        # A previous author wrote that reloading all semesters can be dangerous
        # Not sure why, but requiring `ALL_DANGEROUS` to honor the help text
        parser.add_argument(
            'semester',
            help=('Semester to update grades (e.g. "2019_FALL").\nIf you wish'
                  ' to reload all semesters (potentially dangerous!) then put '
                  '"ALL_DANGEROUS" as the value of this argument.\nNote that '
                  'only a single semester is allowed.'),
            type=str
        )

        parser.add_argument(
            '--suppress-tqdm',
            action='store_true',
            help='Suppress the tqdm loading bars'
        )

        parser.add_argument(
            '--log-missing-instructors',
            action='store_true',
            help='Create a .txt file with missing instructors'
        )

    def handle(self, *args, **options):
        """Standard Django function implementation - runs when this command is executed."""
        self.verbosity = options['verbosity']
        self.suppress_tqdm = options['suppress_tqdm']
        self.log_missing_instructors = options['log_missing_instructors']

        if self.verbosity > 0:
            print('Step 1: Fetch Course and Instructor data for later use')
        semester = options['semester']
        if semester == 'ALL_DANGEROUS':
            # ALL_DANGEROUS removes all existing data
            CourseGrade.objects.all().delete()
            CourseInstructorGrade.objects.all().delete()

            # Loads every data CSV file in /grade_data/csv with exceptions
            for file in sorted(os.listdir(self.data_dir)):
                if self.verbosity == 3:
                    print('Loading data from', file)
                # Ignore temp files (start with '~' on Windows, '.' otherwise) and test data
                if file[0] not in ('.', '~') and file != 'test_data.csv':
                    self.load_semester_file(file)
        else:
            self.load_semester_file(f"{semester.lower()}.csv")
        self.load_dict_into_models()

    def clean(self, df):
        """ Removes rows with incomplete data from dataframe"""
        # Note: some 'Course GPA' and '# of Students' entries are empty due to FERPA
        # (see wiki for more details) but we don't use those columns anyways

        # Filter out data with no grades
        df = df.dropna(
            how="all",
            subset=['A+', 'A', 'A-',
                    'B+', 'B', 'B-',
                    'C+', 'C', 'C-',
                    'DFW']
        )
        # Not quite sure how much data this actually applies to,
        # as UVA data is much more reliable than the old VAGrades data

        # Filter out data with missing instructor (represented by ...)
        return df[df['Primary Instructor Name'] != '...']

    def load_semester_file(self, file):
        """Given a file name, cleans + loads its data into the global grade data dicts."""
        df = self.clean(pd.read_csv(os.path.join(self.data_dir, file)))
        if self.verbosity > 0:
            print(f"Found {df.size} sections in {file}")

        for index, row in tqdm(df.iterrows(), total=df.shape[0], disable=self.suppress_tqdm):
            if self.verbosity == 3:
                print(str(row).encode('ascii', 'ignore').decode('ascii'))
            self.load_row_into_dict(row)
        if self.verbosity > 0:
            print(f'Done loading {file}')

    def load_row_into_dict(self, row):
        """
        Loads data from a given row into the global dicts
        course_grades and course_instructor_grades
        """
        # Columns are processed left to right, with one exception

        # 'Term Desc' column is unused because we only care about aggregate across semesters
        # Might want to display semester-by-semester metrics too? Would have to change this

        subject = row['Subject']
        # `Catalog Number` is handled with all other numerical data in the try block below

        title = row['Class Title']
        full_name = row['Primary Instructor Name']
        # Key assumption: names are in the format `LAST,FIRST MIDDLE`
        try:
            last_name, first_and_middle = full_name.split(',')
            first_name = first_and_middle.split(' ')[0]
        except ValueError:
            # Script should stop if name that doesn't fit this pattern is given
            if self.verbosity > 0:
                print('full name is', full_name)
            raise ValueError(
                f"{full_name=} doesn't meet our assumption about `Primary Instructor Name` format.")

        # 'Class Section' column is unused
        try:
            number = int(re.sub('[^0-9]', '', str(row['Catalog Number'])))
            # 'Course GPA' is unused because we manually calculate average between all semesters
            # '# of Students' is unused because we manually calculate it for all semesters
            a_plus = int(row['A+'])
            a = int(row['A'])
            a_minus = int(row['A-'])
            b_plus = int(row['B+'])
            b = int(row['B'])
            b_minus = int(row['B-'])
            c_plus = int(row['C+'])
            c = int(row['C'])
            c_minus = int(row['C-'])
            # UVA data doesn't contain D's or F's, just the DFW column
            # DFW combines Ds, Fs, and withdraws into one category
            dfw = int(row['DFW'])
        except (TypeError, ValueError) as e:
            if self.verbosity > 0:
                print(row)
                print(e)
            raise e
        # No error casting values to float/int, so continue
        # Identifiers are tuple keys to grade data dictionaries
        course_identifier = (subject, number, title)
        course_instructor_identifier = (
            subject, number, first_name, last_name)

        # Dictionary values (incremented onto value if key already exists)
        this_semesters_grades = [a_plus, a, a_minus,
                                 b_plus, b, b_minus,
                                 c_plus, c, c_minus,
                                 dfw]

        # Load this semester into course_grades dictionary
        if course_identifier in self.course_grades:
            for i in range(len(self.course_grades[course_identifier])):
                self.course_grades[course_identifier][i] += this_semesters_grades[i]
        else:
            self.course_grades[course_identifier] = this_semesters_grades.copy()

        # Load this semester into course_instructor_grades dictionary
        if course_instructor_identifier in self.course_instructor_grades:
            for i in range(len(self.course_instructor_grades[course_instructor_identifier])):
                self.course_instructor_grades[course_instructor_identifier][i] += this_semesters_grades[i]
        else:
            self.course_instructor_grades[course_instructor_identifier] = this_semesters_grades.copy(
            )

    def load_dict_into_models(self):
        """ Converts dictionaries to real instances of CourseGrade and CourseInstructorGrade.

        Given a course or course-instructor pair and its corresponding grade distribution,
        calculates weighted GPA average and total enrolled students and then uses all of those
        as parameters to create new CourseGrade and CourseInstructorGrade instances.
        """
        if self.verbosity > 0:
            print('Step 2: Bulk-create CourseGrade instances')
        # Used for GPA calculation
        grade_weights = [4.0, 4.0, 3.7,
                         3.3, 3.0, 2.7,
                         2.3, 2.0, 1.7,
                         0]  # DFW column removed in average calculation

        # Load course_grades data from dicts and create model instances
        unsaved_cg_instances = []
        for row in tqdm(self.course_grades, disable=self.suppress_tqdm):
            total_enrolled = sum(self.course_grades[row])
            total_weight = sum(a * b for a, b in
                               zip(self.course_grades[row], grade_weights))

            course_grade_params = self.set_grade_params(
                row, total_enrolled, total_weight, is_instructor_grade=False)
            unsaved_cg_instance = CourseGrade(**course_grade_params)
            unsaved_cg_instances.append(unsaved_cg_instance)

        # bulk_create is much more efficient than creating them separately
        CourseGrade.objects.bulk_create(unsaved_cg_instances)
        if self.verbosity > 0:
            print('Done creating CourseGrade instances')
            print('Step 3: Bulk-create CourseInstructorGrade instances')

        # Load course_instructor_grades data from dicts and create model instances
        unsaved_cig_instances = []
        for row in tqdm(self.course_instructor_grades, disable=self.suppress_tqdm):
            total_enrolled = 0
            for grade_count in self.course_instructor_grades[row]:
                total_enrolled += grade_count

            total_weight = 0
            for i in range(len(self.course_instructor_grades[row])):
                total_weight += (
                    self.course_instructor_grades[row][i] * grade_weights[i])

            course_instructor_grade_params = self.set_grade_params(
                row, total_enrolled, total_weight, is_instructor_grade=True)
            unsaved_cig_instance = CourseInstructorGrade(
                **course_instructor_grade_params)
            unsaved_cig_instances.append(unsaved_cig_instance)
        CourseInstructorGrade.objects.bulk_create(unsaved_cig_instances)
        if self.verbosity > 0:
            print('Done creating CourseInstructorGrade instances')

        if self.log_missing_instructors:
            print('Writing missing instructors to missing-instructors.txt')
            with open('missing-instructors.txt', 'w') as file:
                for instructor in self.missing_instructors:
                    file.write(instructor)

    def set_grade_params(self, row, total_enrolled, total_weight, is_instructor_grade):
        """Creates dict of params to be used as parameters
        in creating CourseGrade/CourseInstructorGrade instances.
        Helper function for load_dict_into_models()"""
        if is_instructor_grade:
            data = self.course_instructor_grades[row]
        else:
            data = self.course_grades[row]

        # Calculate gpa excluding DFW column. This will skew average GPAs above
        # what they actually are since DFW includes students with low scores, but
        # the skew is in a consistent direction for all classes so it's *probably* fine.
        total_enrolled_filtered = total_enrolled - data[9]
        # Check divide by 0
        if total_enrolled_filtered == 0:
            total_enrolled_gpa = 0
        else:
            total_enrolled_gpa = total_weight / total_enrolled_filtered
        course_grade_params = {
            'course_id': self.courses.get(row[:2]),
            'average': total_enrolled_gpa,
            'a_plus': data[0],
            'a': data[1],
            'a_minus': data[2],
            'b_plus': data[3],
            'b': data[4],
            'b_minus': data[5],
            'c_plus': data[6],
            'c': data[7],
            'c_minus': data[8],
            'dfw': data[9],
            'total_enrolled': total_enrolled
        }

        if is_instructor_grade:
            course_grade_params['instructor_id'] = self.instructors.get(row[2:])
            if self.log_missing_instructors and course_grade_params['instructor_id'] is None:
                self.missing_instructors.add(f'{row[2]} {row[3]}\n')
        return course_grade_params
