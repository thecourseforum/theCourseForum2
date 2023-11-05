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


def find_all_class_numbers(semester):  # this function will be incredibly slow
    """
    input: semester using the formula  “1” + [2 digit year] + [2 for Spring, 8 for Fall]. So, 1228 is Fall 2022.
    output: set of all course numbers
    functionality: connects with sis API and uses the given list of all subjects to look at all classes each
        department offers to find all the unique course numbers. This will be used when querying each class
        individually.
    """

    all_classes = []
    page = 1
    while True:
        url = (
            'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.' +
            'FieldFormula.IScript_ClassSearch?institution=UVA01&term=' + semester + '&page=' + page)
        try:
            apiResponse = requests.get(url)
            data = json.loads(apiResponse.text)
            if data == []:
                break
        except Exception as e:
            print(e)
            break
        for course in data:
            all_classes.append(compile_class_data(course['class_nbr']))
        page += 1
    return all_classes

def compile_class_data(course_number, semester):
    """
        input: course number, semester 
        output: course dictionaries to be used for file writing
        functionality: request and organize course data in dictionaries to be able to write to a csv file.
    """
    url = f"https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassDetails?institution=UVA01&term={semester}&class_nbr={course_number}"
    
    try:
        apiResponse = requests.get(url)
        data = json.loads(apiResponse.text)
        if data == []:
            break
    except Exception as e:
        print(e)
        break

    class_details = data["section_info"]["class_details"]
    course_dictionary = {
        "ClassNumber": course_number,
        "Mnemonic": class_details["subject"],
        "Number": class_details["catalog_nbr"],
        "Section": class_details["class_section"],
        # For Type, Parser needs to be updated to use abbriveation instead of full word (LEC instead of Lecture)
        "Type": 
        switch(class_details["component"]) {
            case "LEC": "Lecture";
            case "DIS": "Discussion";
            case "LAB": "Laboratory";
            default: class_details["component"];
        },
        # "units": "1 - 12 units" to "1 - 12", "units": "3 units" to "3"
        "Units": class_details["units"][0:class_details["units"].find("u") - 1],
        "Instructor1": ,"Days1","Room1","MeetingDates1",Instructor2,Days2,Room2,MeetingDates2,Instructor3,Days3,Room3,MeetingDates3,Instructor4,Days4,Room4,MeetingDates4,Title,Topic,Status,Enrollment,EnrollmentLimit,Waitlist,Description

    }
    return course_dictionary


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
