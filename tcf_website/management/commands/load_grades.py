import os
import pandas as pd
import re

from django.core.management.base import BaseCommand, CommandError
from tcf_website.models import *
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from tqdm import tqdm


class Command(BaseCommand):
    """
    How To Use: Run python3 manage.py load_grades to load all grades
    in the tcf_website/management/commands/grade_data/excel/ directory.
    This should take ~20 min to run to load all the grades
    """
    help = 'Imports grade data from VAGrades Excel Spreadsheets into PostgresSQL database'

    global course_grades
    global course_instructor_grades

    course_grades = {}
    course_instructor_grades = {}

    '''
    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output',
        )

        parser.add_argument(
            'semester',
            help='Semester to update grades (e.g. "2019_FALL").\nIf you wish to reload all semesters (potentially dangerous!) then put "ALL_DANGEROUS" as the value of this argument.',
            type=str
        )
    '''

    def handle(self, *args, **options):

        # self.verbose = options['verbose']

        self.data_dir = 'tcf_website/management/commands/grade_data/excel/'

        # semester = options['semester']

        [self.load_semester_file(file) for file in sorted(
            os.listdir(self.data_dir)) if not file.startswith('.')]

        '''
        if semester == 'ALL_DANGEROUS':
            # ignores temporary files
            [self.load_semester_file(file) for file in sorted(os.listdir(self.data_dir)) if not file.startswith('.')]
        else:
            self.load_semester_file(f"{semester.lower()}.xlsx")
        '''

    def clean(self, df):
        CourseGrade.objects.all().delete()  # deletes CourseGrade table
        # deletes CourseInstructorGrade table
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

        print(year, season)

        df = self.clean(pd.read_excel(os.path.join(self.data_dir, file)))

        print(f"{df.size} sections")

        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            # print(str(row).encode('ascii', 'ignore').decode('ascii'))
            self.load_row_into_dict(row)
            # break

        self.load_dict_into_models()

    def load_row_into_dict(self, row):
        try:
            # parsing fields of excel

            first_name = row['Instructor First Name']
            middle_name = row['Instructor Middle Name']
            last_name = row['Instructor Last Name']
            email = row['Instructor Email']
            subdepartment = row['Subject']
            number = re.sub('[^0-9]', '', str(row['Course Number']))
            section_number = row['Section Number']  # not used
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
            # credit
            # general_credit
            # no_credit
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
            if course_identifier not in course_grades:
                course_grades[course_identifier] = this_semesters_grades
            else:
                for i in range(len(course_grades[course_identifier])):
                    course_grades[course_identifier][i] += this_semesters_grades[i]

            # load this semester into course instructor dictionary
            if course_instructor_identifier not in course_instructor_grades:
                course_instructor_grades[course_instructor_identifier] = this_semesters_grades
            else:
                for i in range(
                        len(course_instructor_grades[course_instructor_identifier])):
                    course_instructor_grades[course_instructor_identifier][i] += this_semesters_grades[i]

        except TypeError as e:
            print(row)
            print(e)
            raise e

    def load_dict_into_models(self):
        # used for gpa calculation
        grade_weights = [4.0, 4.0, 3.7,
                         3.3, 3.0, 2.7,
                         2.3, 2.0, 1.7,
                         1.3, 1.0, 0.7,
                         0.0,
                         0.0, 0.0, 0.0]

        # load course grades
        for row in course_grades:
            total_enrolled = 0
            for grade_count in course_grades[row]:
                total_enrolled += grade_count

            total_weight = 0
            for i in range(len(course_grades[row])):
                total_weight += (course_grades[row][i] * grade_weights[i])

            # calculate gpa without including ot/drop/withdraw in
            # total_enrolled
            total_enrolled_filtered = total_enrolled - \
                course_grades[row][13] - course_grades[row][14] - course_grades[row][15]
            # check divide by 0
            if total_enrolled_filtered != 0:
                gpa = (total_weight) / (total_enrolled_filtered)
            else:
                gpa = 0.0

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
                if total_enrolled_gpa != 0 and existing_total_enrolled_filtered != 0:
                    gpa = (
                        (gpa * total_enrolled_filtered) + (
                            existing_course_grade.average * existing_total_enrolled_filtered)) / (
                        total_enrolled_filtered + existing_total_enrolled_filtered)
                else:
                    gpa = 0.0

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
                    'average': gpa,
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

                course_grade = CourseGrade(**course_grade_params)

                course_grade.save()

        # load course instructor grades
        for row in course_instructor_grades:
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
            if total_enrolled_filtered != 0:
                gpa = (total_weight) / (total_enrolled_filtered)
            else:
                gpa = 0.0

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
                if total_enrolled_gpa != 0 and existing_total_enrolled_filtered != 0:
                    gpa = (
                        (gpa * total_enrolled_filtered) + (
                            existing_instructor_grade.average * existing_total_enrolled_filtered)) / (
                        total_enrolled_filtered + existing_total_enrolled_filtered)
                else:
                    gpa = 0.0

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
                    'average': gpa,
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

                course_instructor_grade = CourseInstructorGrade(
                    **course_instructor_grade_params)

                course_instructor_grade.save()
