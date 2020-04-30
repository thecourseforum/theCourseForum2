import os
import pandas as pd

from django.core.management.base import BaseCommand, CommandError
from tcf_website.models import *
from tqdm import tqdm



class Command(BaseCommand):
    help = 'Imports grade data from CSVs into PostgresSQL database'

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
            self.load_semester_file(f"{semester.lower()}.csv")

    def clean(self, df):
        return df.dropna(
            subset=['Course GPA', 'Total'])

    def load_semester_file(self, file):
        year, semester = file.split('.')[0].split('_')
        year = int(year)
        season = semester.upper()

        print(year, season)

        df = self.clean(pd.read_csv(os.path.join(self.data_dir, file)))

        print(f"{df.size} sections")

        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            # print(str(row).encode('ascii', 'ignore').decode('ascii'))
            self.load_section_row(semester, row)
            # break

    def load_section_row(self, semester, row):
        try:
            first_name = row['Instructor First Name']
            middle_name = row['Instructor Middle Name']
            last_name = row['Instructor Last Name']
            email = row['Instructor Email']
            subdepartment = row['Subject']
            number = re.sub('[^0-9]', '', str(row['Course Number']))
            section_number = row['Section Number']
            title = row['Title']
            gpa = row['Course GPA']
            a_plus = row['A+']
            a = row['A']
            a_minus = row['A-']
            b_plus = row['B+']
            b = row['B']
            b_minus = row['B-']
            c_plus = row['C+']
            c = row['C']
            c_minus = row['C-']
            d_plus = row['D+']
            d = row['D']
            d_minus = row['D-']
            f = row['F']
            ot = row['OT']
            drop = row['DR']
            withdraw = row['W']
            # credit
            # general_credit
            # no_credit
            total_enrolled = row['Total']

        except TypeError as e:
            print(row)
            print(e)
            raise e

        