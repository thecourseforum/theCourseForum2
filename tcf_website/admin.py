from django.contrib import admin

# Register your models here.
from .models import School, Department, Subdepartment, User, Student, Instructor, Semester, Course, Section, Review, Vote


admin.site.register(School)
admin.site.register(Department)
admin.site.register(Subdepartment)
admin.site.register(Student)
admin.site.register(Instructor)
admin.site.register(Semester)
admin.site.register(Course)
admin.site.register(Section)
admin.site.register(Review)
admin.site.register(Vote)
