import os
import pandas as pd
import re

from django.core.management.base import BaseCommand
from tcf_website.models import *
from django.core.exceptions import ObjectDoesNotExist

from tqdm import tqdm


class Command(BaseCommand):
    """
    How To Use: Run python3 manage.py load_grades to load all grades
    in the tcf_website/management/commands/grade_data/csv/ directory.
    This should take ~20 min to run to load all the grades
    """
    help = 'Imports grade data from VAGrades CSV files into PostgresSQL database'

    # Not a good practice but declared as global for readability & convenience?
    global course_grades
    global course_instructor_grades

    course_grades = {}
    course_instructor_grades = {}

    def add_arguments(self, parser):
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

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.data_dir = 'tcf_website/management/commands/grade_data/csv/'
        semester = options['semester']
        if semester == 'ALL_DANGEROUS':
            # ignores temporary files ('~' on Windows, '.' otherwise)
            for file in sorted(os.listdir(self.data_dir)):
                if file[0] not in ('.', '~'):
                    self.load_semester_file(file)
        else:
            self.load_semester_file(f"{semester.lower()}.csv")

    def clean(self, df):
        # Truncate existing tables
        CourseGrade.objects.all().delete()
        CourseInstructorGrade.objects.all().delete()
        
        return df.dropna(
            how="all",
            subset=['A+', 'A', 'A-',
                    'B+', 'B', 'B-',
                    'C+', 'C', 'C-',
                    'D+', 'D', 'D-',
                    'F']
        )

    def load_semester_file(self, file):
        year, semester = file.split('.')[0].split('_')
        year = int(year)
        season = semester.upper()

        df = self.clean(pd.read_csv(os.path.join(self.data_dir, file)))
        if self.verbosity > 0:
            print(f"Found {df.size} sections in {file}")

        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            if self.verbosity == 3:
                print(str(row).encode('ascii', 'ignore').decode('ascii'))
            self.load_row_into_dict(row)
        if self.verbosity > 0:
            print('Done with loading CSV files')

        self.load_dict_into_models()

    def load_row_into_dict(self, row):
        try:
            # parsing fields of the CSV file
            first_name = row['Instructor First Name']
            middle_name = row['Instructor Middle Name']
            last_name = row['Instructor Last Name']
            email = row['Instructor Email']
            subdepartment = row['Subject']
            number = re.sub('[^0-9]', '', str(row['Course Number']))
            # row['Section Number'] is not used
            title = row['Title']
            gpa = float(row['Course GPA'])
            a_plus = int(row['A+'])
            a = int(row['A'])
            a_minus = int(row['A-'])
            b_plus = int(row['B+'])
            b = int(row['B'])
            b_minus = int(row['B-'])
            c_plus = int(row['C+'])
            c = int(row['C'])
            c_minus = int(row['C-'])
            d_plus = int(row['D+'])
            d = int(row['D'])
            d_minus = int(row['D-'])
            f = int(row['F'])
            ot = int(row['OT'])
            drop = int(row['DR'])
            withdraw = int(row['W'])
            total_enrolled = int(row['Total'])

            # identifiers are tuple keys to dictionaries
            course_identifier = (subdepartment, number, title)
            course_instructor_identifier = (
                subdepartment, number, first_name, middle_name, last_name, email)

            # value of dictionaries (incremented onto value if key already
            # exists)
            this_semesters_grades = [a_plus, a, a_minus,
                                     b_plus, b, b_minus,
                                     c_plus, c, c_minus,
                                     d_plus, d, d_minus,
                                     f,
                                     ot, drop, withdraw]

            # load this semester into course dictionary
            if course_identifier in course_grades:
                for i in range(len(course_grades[course_identifier])):
                    course_grades[course_identifier][i] += this_semesters_grades[i]
            else:
                course_grades[course_identifier] = this_semesters_grades

            # load this semester into course instructor dictionary
            if course_instructor_identifier in course_instructor_grades:
                for i in range(
                        len(course_instructor_grades[course_instructor_identifier])):
                    course_instructor_grades[course_instructor_identifier][i] += this_semesters_grades[i]
            else:
                course_instructor_grades[course_instructor_identifier] = this_semesters_grades

        except TypeError as e:
            if self.verbosity > 0:
                print(row)
                print(e)
            raise e

    def load_dict_into_models(self):
        # used for gpa calculation
        grade_weights = [4.0, 4.0, 3.7,
                         3.3, 3.0, 2.7,
                         2.3, 2.0, 1.7,
                         1.3, 1.0, 0.7,
                         0,
                         0, 0, 0]

        # load course grades
        for row in tqdm(course_grades):
            total_enrolled = sum(course_grades[row])
            total_weight = sum(a*b for a, b in
                               zip(course_grades[row], grade_weights))

            # calculate gpa excluding ot/drop/withdraw in total_enrolled
            total_enrolled_filtered = total_enrolled - \
                sum(course_grades[row][i] for i in (13, 14, 15))
            # check divide by 0
            if total_enrolled_filtered == 0:
                total_enrolled_gpa = 0
            else:
                total_enrolled_gpa = (total_weight) / (total_enrolled_filtered)

            try:
                # check if the course is already in CourseGrade
                # if so, calculate weighted average with new gpa, and add that
                # into the model
                existing_course_grade = CourseGrade.objects.get(
                    subdepartment=row[0],
                    number=row[1],
                    title=row[2],
                )

                # disregard ot/drop/withdraw
                existing_total_enrolled_filtered = existing_course_grade.total_enrolled - \
                    existing_course_grade.ot - existing_course_grade.drop - existing_course_grade.withdraw
                # check divide by 0
                if total_enrolled_gpa == 0 or existing_total_enrolled_filtered == 0:
                    gpa = 0
                else:
                    gpa = (
                        (gpa * total_enrolled_filtered) + (
                            existing_course_grade.average * existing_total_enrolled_filtered)) / (
                        total_enrolled_filtered + existing_total_enrolled_filtered)

                # set gpa field
                existing_course_grade.average = gpa
                # increment counts for grades and total enrolled
                existing_course_grade.a_plus += course_grades[row][0]
                existing_course_grade.a += course_grades[row][1]
                existing_course_grade.a_minus += course_grades[row][2]
                existing_course_grade.b_plus += course_grades[row][3]
                existing_course_grade.b += course_grades[row][4]
                existing_course_grade.b_minus += course_grades[row][5]
                existing_course_grade.c_plus += course_grades[row][6]
                existing_course_grade.c += course_grades[row][7]
                existing_course_grade.c_minus += course_grades[row][8]
                existing_course_grade.d_plus += course_grades[row][9]
                existing_course_grade.d += course_grades[row][10]
                existing_course_grade.d_minus += course_grades[row][11]
                existing_course_grade.f += course_grades[row][12]
                existing_course_grade.ot += course_grades[row][13]
                existing_course_grade.drop += course_grades[row][14]
                existing_course_grade.withdraw += course_grades[row][15]
                existing_course_grade.total_enrolled += total_enrolled

                existing_course_grade.save()
            except ObjectDoesNotExist:
                # if course not in CourseGrade, create a new object
                course_grade_params = {
                    'subdepartment': row[0],
                    'number': row[1],
                    'title': row[2],
                    'average': total_enrolled_gpa,
                    'a_plus': course_grades[row][0],
                    'a': course_grades[row][1],
                    'a_minus': course_grades[row][2],
                    'b_plus': course_grades[row][3],
                    'b': course_grades[row][4],
                    'b_minus': course_grades[row][5],
                    'c_plus': course_grades[row][6],
                    'c': course_grades[row][7],
                    'c_minus': course_grades[row][8],
                    'd_plus': course_grades[row][9],
                    'd': course_grades[row][10],
                    'd_minus': course_grades[row][11],
                    'f': course_grades[row][12],
                    'ot': course_grades[row][13],
                    'drop': course_grades[row][14],
                    'withdraw': course_grades[row][15],
                    'total_enrolled': total_enrolled
                }
                CourseGrade.objects.create(**course_grade_params)
        if self.verbosity > 0:
            print('Done loading CourseGrade models')

        # load course instructor grades
        for row in tqdm(course_instructor_grades):
            total_enrolled = 0
            for grade_count in course_instructor_grades[row]:
                total_enrolled += grade_count

            total_weight = 0
            for i in range(len(course_instructor_grades[row])):
                total_weight += (
                    course_instructor_grades[row][i] *
                    grade_weights[i])

            # calculate gpa without including ot/drop/withdraw in
            # total_enrolled
            total_enrolled_filtered = total_enrolled - \
                course_instructor_grades[row][13] - course_instructor_grades[row][14] - course_instructor_grades[row][15]
            if total_enrolled_filtered == 0:
                total_enrolled_gpa = 0
            else:
                total_enrolled_gpa = (total_weight) / (total_enrolled_filtered)

            try:
                # check if the course instructor is already in CourseInstructorGrade
                # if so, calculate weighted average with new gpa, and add that
                # into the model
                existing_instructor_grade = CourseInstructorGrade.objects.get(
                    subdepartment=row[0],
                    number=row[1],
                    first_name=row[2],
                    middle_name=row[3],
                    last_name=row[4],
                    email=row[5],
                )

                # disregard ot/drop/withdraw
                existing_total_enrolled_filtered = existing_instructor_grade.total_enrolled - \
                    existing_instructor_grade.ot - existing_instructor_grade.drop - existing_instructor_grade.withdraw
                # check divide by 0
                if total_enrolled_gpa == 0 or existing_total_enrolled_filtered == 0:
                    gpa = 0
                else:
                    gpa = (
                        (gpa * total_enrolled_filtered) + (
                            existing_instructor_grade.average * existing_total_enrolled_filtered)) / (
                        total_enrolled_filtered + existing_total_enrolled_filtered)

                # set gpa field
                existing_instructor_grade.average = gpa
                # increment counts for grades and total enrolled
                existing_instructor_grade.a_plus += course_instructor_grades[row][0]
                existing_instructor_grade.a += course_instructor_grades[row][1]
                existing_instructor_grade.a_minus += course_instructor_grades[row][2]
                existing_instructor_grade.b_plus += course_instructor_grades[row][3]
                existing_instructor_grade.b += course_instructor_grades[row][4]
                existing_instructor_grade.b_minus += course_instructor_grades[row][5]
                existing_instructor_grade.c_plus += course_instructor_grades[row][6]
                existing_instructor_grade.c += course_instructor_grades[row][7]
                existing_instructor_grade.c_minus += course_instructor_grades[row][8]
                existing_instructor_grade.d_plus += course_instructor_grades[row][9]
                existing_instructor_grade.d += course_instructor_grades[row][10]
                existing_instructor_grade.d_minus += course_instructor_grades[row][11]
                existing_instructor_grade.f += course_instructor_grades[row][12]
                existing_instructor_grade.ot += course_instructor_grades[row][13]
                existing_instructor_grade.drop += course_instructor_grades[row][14]
                existing_instructor_grade.withdraw += course_instructor_grades[row][15]
                existing_instructor_grade.total_enrolled += total_enrolled

                existing_instructor_grade.save()
            except ObjectDoesNotExist:
                # if course not in CourseInstructorGrade, create a new object
                course_instructor_grade_params = {
                    'subdepartment': row[0],
                    'number': row[1],
                    'first_name': row[2],
                    'middle_name': row[3],
                    'last_name': row[4],
                    'email': row[5],
                    'average': total_enrolled_gpa,
                    'a_plus': course_instructor_grades[row][0],
                    'a': course_instructor_grades[row][1],
                    'a_minus': course_instructor_grades[row][2],
                    'b_plus': course_instructor_grades[row][3],
                    'b': course_instructor_grades[row][4],
                    'b_minus': course_instructor_grades[row][5],
                    'c_plus': course_instructor_grades[row][6],
                    'c': course_instructor_grades[row][7],
                    'c_minus': course_instructor_grades[row][8],
                    'd_plus': course_instructor_grades[row][9],
                    'd': course_instructor_grades[row][10],
                    'd_minus': course_instructor_grades[row][11],
                    'f': course_instructor_grades[row][12],
                    'ot': course_instructor_grades[row][13],
                    'drop': course_instructor_grades[row][14],
                    'withdraw': course_instructor_grades[row][15],
                    'total_enrolled': total_enrolled
                }
                CourseInstructorGrade.objects.create(
                    **course_instructor_grade_params)
        if self.verbosity > 0:
            print('Done loading CourseInstructorGrade models')
