from tcf_website.models import Course

courses = Course.objects.all()

for c in courses:
    print(c.prerequisite)
