import os
import re

from tqdm import tqdm
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from tcf_website.models import *



class Command(BaseCommand):
    help = 'Imports data from lous list csv\'s into default database'
    
    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output',
        )

        parser.add_argument(
            'semester',
            help='Semester to update (e.g. "2019_FALL").\nIf you wish to reload all semesters (potentially dangerous!) then put "ALL_DANGEROUS" as the value of this argument.\nMake sure that the new semester data is downloaded via `semester_data/fetch_data.py` before running this command.',
            type=str
        )

    def handle(self, *args, **options):

        self.verbose = options['verbose']

        self.UNKNOWN_SCHOOL, _ = School.objects.get_or_create(name='UNKNOWN')
        self.UNKNOWN_DEPT, _ = Department.objects.get_or_create(name='UNKNOWN', school = self.UNKNOWN_SCHOOL)
        self.STAFF, _ = Instructor.objects.get_or_create(last_name='Staff')

        self.data_dir = 'tcf_website/management/commands/semester_data/csv/'

        semester = options['semester']
        
        if semester == 'ALL_DANGEROUS':
            for file in sorted(os.listdir(self.data_dir)):
                self.load_semester_file(file)

        elif semester == 'FIX_LAST_TAUGHT_SEMESTERS':
            # This should be done automatically when loading a semester,
            # but run this command if you notice that it hasn't been done.
            sections = Section.objects.all()
            for section in tqdm(sections, total=sections.count()):
                if section.semester.is_after(section.course.semester_last_taught):
                    section.course.semester_last_taught = section.semester
                    section.course.save()
                    section.save()
        else:
            self.load_semester_file(f"{semester.lower()}.csv")
        
        print("Completed. Hooray!")

    
    def clean(self, df):
        return df.dropna(subset=['Mnemonic', 'ClassNumber', 'Number', 'Section'])
    
    def load_semester_file(self, file):
        year, semester = file.split('.')[0].split('_')
        year = int(year)
        season = semester.upper()

        print(year, season)

        df = self.clean(pd.read_csv(os.path.join(self.data_dir, file)))

        print(f"{df.size} sections")

        semester = self.load_semester(year, season)

        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            # print(row)
            self.load_section_row(semester, row)
            # break
    
    def load_semester(self, year, season):
        year_code = str(year)[-2:]
        season_code = {
            'FALL': 8,
            'SUMMER': 6,
            'SPRING': 2,
            'JANUARY': 1
        }[season]
        semester_code = f"1{year_code}{season_code}"

        sem, created = Semester.objects.get_or_create(
            year = year,
            season = season,
            number = semester_code,
        )

        if self.verbose:
            if created:
                print(f"Created {sem}")
            else:
                print(f"Retrieved {sem}")
            
        return sem
    
    def load_section_row(self, semester, row):
        try:
            mnemonic = row['Mnemonic'] # may NOT be missing
            sis_number = row['ClassNumber'] # may NOT be missing
            # strip out non-numeric characters.
            course_number = re.sub('[^0-9]','', str(row['Number'])) # may NOT be missing
            section_number = row['Section'] # may NOT be missing
            
            units = row['Units'] # may be empty/nan
            title = row['Title'] # may be empty/nan
            topic = row['Topic'] # may be empty/nan
            description = row['Description'] # may be empty/nan
            section_type = row['Type'] # may be empty/nan

            # may include staff, may be empty
            instructor_names = row[['Instructor1', 'Instructor2', 'Instructor3', 'Instructor4']].dropna().array
        except TypeError as e:
            print(row)
            print(e)
            raise e

        sd = self.load_subdepartment(mnemonic)
        course = self.load_course(title, description, semester, sd, course_number)
        instructors = self.load_instructors(instructor_names)
        section = self.load_section(sis_number, instructors, semester, course, topic, units, section_type)
    
    def load_subdepartment(self, mnemonic):

        try:
            sd = Subdepartment.objects.get(
                mnemonic = mnemonic,
            )
            if self.verbose:
                print(f"Retrieved {sd}")
        except ObjectDoesNotExist: # no SD
            sd = Subdepartment(mnemonic=mnemonic, department=self.UNKNOWN_DEPT)
            sd.save()
            if self.verbose:
                print(f"Created {sd}")
        return sd

    # TODO: how to handle special topics courses?
    # topic: section topic
    # description: course description!
    def load_course(self, title, description, semester, subdepartment, number):
        
        params = {}
        fields = {'title', 'description', 'subdepartment', 'number'}
        for k, v in locals().items():
            if k in fields and not pd.isnull(v):
                params[k] = v

        try:
            course = Course.objects.get(
                subdepartment=subdepartment,
                number=number
            )
            if self.verbose:
                print(f"Retrieved {course}")
        except ObjectDoesNotExist:
            # create new Course with title, description, subdepartment, number
            course = Course(**params)
            course.semester_last_taught = semester
            course.save()
            if self.verbose:
                print(f"Created {course}")

        # fill in blank info
        if not course.description and not pd.isnull(description):
            course.description = description
        if not course.title and not pd.isnull(title):
            course.description = title
        
        # update with new info if possible
        if semester.is_after(course.semester_last_taught):
            course.semester_last_taught = semester
            if not pd.isnull(description):
                course.description = description
            if not pd.isnull(title):
                course.title = title
        course.save()
        
        return course
    
    def load_instructors(self, instructor_names):
        if not instructor_names:
            return [self.STAFF]
        instructors = set()
        for name in instructor_names:
            if name in {'Staff', 'Faculty Staff', 'Faculty'} or name.isspace():
                instructors.add(self.STAFF)
            else:
                names = name.split()
                try:
                    first, last = names[0], names[-1]
                except IndexError as e:
                    print(f"Instructor named '{name}'")
                    print(e)
                    raise e

                instructor, created = Instructor.objects.get_or_create(
                    first_name = first,
                    last_name = last,
                )
                if self.verbose:
                    if created:
                        print(f"Created {instructor}")
                    else:
                        print(f"Retrieved {instructor}")
                instructors.add(instructor)
        return instructors

    def load_section(self, sis_section_number, instructors, semester, course, topic, units, section_type):
        
        params = {}
        fields = {'sis_section_number', 'semester', 'course', 'topic', 'units', 'section_type'}
        for k, v in locals().items():
            if k in fields and not pd.isnull(v):
                params[k] = v

        # print(locals())
        section, created = Section.objects.get_or_create(
            **params
        )

        for instructor in instructors:
            section.instructors.add(instructor)

        if self.verbose:
            if created:
                print(f"Created {section}")
            else:
                print(f"Retrieved {section}")
        
        return section