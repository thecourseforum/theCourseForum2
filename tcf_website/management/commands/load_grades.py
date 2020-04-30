import os
import pandas as pd

from django.core.management.base import BaseCommand, CommandError
from tcf_website.models import *
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Imports grade data from CSVs into PostgresSQL database'

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

    def load_semester_file(self, file):
        year, semester = file.split('.')[0].split('_')
        year = int(year)
        season = semester.upper()

        print(year, season)

        df = pd.read_csv(os.path.join(self.data_dir, file))

        print(f"{df.size} sections")

        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            print(str(row).encode('ascii', 'ignore').decode('ascii'))
            # self.load_section_row(semester, row)
            # break