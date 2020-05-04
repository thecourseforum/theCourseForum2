import os
import pandas as pd
import re

from django.core.management.base import BaseCommand, CommandError
from tcf_website.models import CourseGrade
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from tqdm import tqdm



class Command(BaseCommand):
    help = 'Imports grade data from VAGrades CSVs into PostgresSQL database'

    global course_grades
    global course_instructor_grades

    course_grades = {}
    course_instructor_grades = {}

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

    def handle(self, *args, **options):

        self.verbose = options['verbose']

        self.data_dir = 'tcf_website/management/commands/grade_data/csv/'

        semester = options['semester']

        if semester == 'ALL_DANGEROUS':
            for file in sorted(os.listdir(self.data_dir)):
                self.load_semester_file(file)
        else:
            self.load_semester_file(f"{semester.lower()}.xlsx")

    def clean(self, df):
        return df.dropna(how="all",
            subset=['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F'])

    def load_semester_file(self, file):
        year, semester = file.split('.')[0].split('_')
        year = int(year)
        season = semester.upper()

        print(year, season)

        df = self.clean(pd.read_excel(os.path.join(self.data_dir, file)))

        print(f"{df.size} sections")

        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            # print(str(row).encode('ascii', 'ignore').decode('ascii'))
            self.load_row_into_dicts(row)
            # break
        
        self.load_dict_into_models()

    def load_row_into_dicts(self, row):
        try:
            first_name = row['Instructor First Name']
            middle_name = row['Instructor Middle Name']
            last_name = row['Instructor Last Name']
            email = row['Instructor Email']
            subdepartment = row['Subject']
            number = re.sub('[^0-9]', '', str(row['Course Number']))
            section_number = row['Section Number'] # not used
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

            course_identifier = (subdepartment, number, title)
            course_instructor_identifier = (subdepartment, number, first_name, middle_name, last_name, email)

            if course_identifier not in course_grades:
                course_grades[course_identifier] = [
                    a_plus,
                    a,
                    a_minus,
                    b_plus,
                    b,
                    b_minus,
                    c_plus,
                    c,
                    c_minus,
                    d_plus,
                    d,
                    d_minus,
                    f,
                    ot,
                    drop,
                    withdraw
                ]
            else:
                course_grades[course_identifier] = [
                    course_grades[course_identifier][0] + a_plus,
                    course_grades[course_identifier][1] + a,
                    course_grades[course_identifier][2] + a_minus,
                    course_grades[course_identifier][3] + b_plus,
                    course_grades[course_identifier][4] + b,
                    course_grades[course_identifier][5] + b_minus,
                    course_grades[course_identifier][6] + c_plus,
                    course_grades[course_identifier][7] + c,
                    course_grades[course_identifier][8] + c_minus,
                    course_grades[course_identifier][9] + d_plus,
                    course_grades[course_identifier][10] + d,
                    course_grades[course_identifier][11] + d_minus,
                    course_grades[course_identifier][12] + f,
                    course_grades[course_identifier][13] + ot,
                    course_grades[course_identifier][14] + drop,
                    course_grades[course_identifier][15] + withdraw
                ]

            if course_instructor_identifier not in course_instructor_grades:
                course_instructor_grades[course_instructor_identifier] = [
                    a_plus,
                    a,
                    a_minus,
                    b_plus,
                    b,
                    b_minus,
                    c_plus,
                    c,
                    c_minus,
                    d_plus,
                    d,
                    d_minus,
                    f,
                    ot,
                    drop,
                    withdraw
                ]
            else:
                course_instructor_grades[course_instructor_identifier] = [
                    course_instructor_grades[course_instructor_identifier][0] + a_plus,
                    course_instructor_grades[course_instructor_identifier][1] + a,
                    course_instructor_grades[course_instructor_identifier][2] + a_minus,
                    course_instructor_grades[course_instructor_identifier][3] + b_plus,
                    course_instructor_grades[course_instructor_identifier][4] + b,
                    course_instructor_grades[course_instructor_identifier][5] + b_minus,
                    course_instructor_grades[course_instructor_identifier][6] + c_plus,
                    course_instructor_grades[course_instructor_identifier][7] + c,
                    course_instructor_grades[course_instructor_identifier][8] + c_minus,
                    course_instructor_grades[course_instructor_identifier][9] + d_plus,
                    course_instructor_grades[course_instructor_identifier][10] + d,
                    course_instructor_grades[course_instructor_identifier][11] + d_minus,
                    course_instructor_grades[course_instructor_identifier][12] + f,
                    course_instructor_grades[course_instructor_identifier][13] + ot,
                    course_instructor_grades[course_instructor_identifier][14] + drop,
                    course_instructor_grades[course_instructor_identifier][15] + withdraw
                ]

        except TypeError as e:
            print(row)
            print(e)
            raise e

    def load_dict_into_models(self):

        grade_weights = [4.0, 4.0, 3.7, 3.3, 3.0, 2.7, 2.3, 2.0, 1.7, 1.3, 1.0, 0.7, 0.0, 0.0, 0.0, 0.0]

        for row in course_grades:
            total_enrolled = 0
            for grade_count in course_grades[row]:
                total_enrolled += grade_count
            
            total_weight = 0
            for i in range(len(course_grades[row])):
                total_weight += (course_grades[row][i] * grade_weights[i])

            gpa = (total_weight) / total_enrolled

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
