"""
This script downloads data from SIS API and converts it into
a usable CSV file. However, in its current state we have to
manually hardcode the year/season of the semester(s) we want to
download.

Potential todo: create a cron job that runs this script and
`load_semester` every now and then so we don't have to do this.
"""

# Classes intended stream finds each department, from there make a query to find each class in the department,
# however, this initial query is less detailed, so we would take this data to form queries for each class seperately
# using the course_nbr variable. Then this data is written to a csv.

# format -ClassNumber,Mnemonic,Number,Section,Type,Units,Instructor1,Days1,Room1,MeetingDates1,Instructor2,Days2,Room2,MeetingDates2,Instructor3,Days3,Room3,MeetingDates3,Instructor4,Days4,Room4,MeetingDates4,Title,Topic,Status,Enrollment,EnrollmentLimit,Waitlist,Description
# example call url
# -https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassDetails?institution=UVA01&term=1242&class_nbr=16634&
import requests
import json

# url to find all courses in department for a semester to update semester Replace 1228 with the appropriate term.
# The formula is “1” + [2 digit year] + [2 for Spring, 8 for Fall]. So, 1228 is Fall 2022.
# todo find out which is used for j term/summer probably 0,4, or 6?
# https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01&term=1228&subject=CS&page=1

# finds all departments in a term:
# https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearchOptions?institution=UVA01&term=1228


def find_all_subjects(semester='1238'):
    """
    input: semester using the formula  “1” + [2 digit year] + [2 for Spring, 8 for Fall]. So, 1228 is Fall 2022.
    output: set of all the different departments
    functionality: connects with sis API and pulls all the departments from a semester and converts that data into a
        list of subjects which can be used to find all the classes in a dept
    """
    url = ('https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.'
           'FieldFormula.IScript_ClassSearchOptions?institution=UVA01&term') + semester
    subjects_set = set({})
    try:
        # getting data
        apiResponse = requests.get(url)
        data = json.loads(apiResponse.text)

        # cleaning data
        list_of_departments = data['subjects']
        for department in list_of_departments:
            subjects_set.add(department['subject'])
        return subjects_set
    except Exception as e:
        print(e)


def find_all_classes_in_subject(semester):  # this function will be incredibly slow
    all_subjects = find_all_subjects(semester)
    all_class_nums = []
    for subject in all_subjects:
        page = 1
        while True:
            url = (
                'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.'
                'IScript_ClassSearch?institution=UVA01&term=1228&subject=' +
                subject +
                '&page=' +
                str(page))
            try:
                apiResponse = requests.get(url)
                data = json.loads(apiResponse.text)
                if data == []:
                    break
                print(data)
            except Exception as e:
                print(e)
                break
            for course in data:
                all_class_nums.append(course['class_nbr'])
            page += 1


def compile_all_class_data(semester):
    pass


def make_class_request(url):
    """
    input: url
    output: json object of filtered class data
    functionality: connects with sis API
    """
    try:
        apiResponse = requests.get(url)
        data = json.loads(apiResponse.text)

        print(data)
    except Exception as e:
        print(e)


def write_csv(list_of_classes):
    pass
# make_class_request(
#     'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.'
#     'FieldFormula.IScript_ClassDetails?institution=UVA01&term=1242&class_nbr=16634')
