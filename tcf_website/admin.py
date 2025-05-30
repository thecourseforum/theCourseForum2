# pylint: disable=missing-class-docstring, wildcard-import

"""TCF Django Admin."""

from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(User)
admin.site.register(Review)
admin.site.register(Vote)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Schedule)
admin.site.register(ScheduledCourse)


class SchoolAdmin(admin.ModelAdmin):
    ordering = ["name"]
    search_fields = ["name"]


class SubdepartmentAdmin(admin.ModelAdmin):
    ordering = ["name"]
    search_fields = ["name"]


class DepartmentAdmin(admin.ModelAdmin):
    ordering = ["name"]
    search_fields = ["name"]


class SemesterAdmin(admin.ModelAdmin):
    ordering = ["-number"]
    search_fields = ["season", "year"]


class DisciplineAdmin(admin.ModelAdmin):
    ordering = ["name"]
    search_fields = ["name"]


class CourseAdmin(admin.ModelAdmin):
    ordering = ["subdepartment__mnemonic", "number", "title"]
    search_fields = ["subdepartment__mnemonic", "number"]


class InstructorAdmin(admin.ModelAdmin):
    ordering = ["last_name", "first_name"]
    search_fields = ["first_name", "last_name"]


class SectionAdmin(admin.ModelAdmin):
    search_fields = [
        "course__subdepartment__mnemonic",
        "course__number",
        "course__title",
    ]
    autocomplete_fields = ["instructors"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related("instructors")
        return qs


class SectionTimeAdmin(admin.ModelAdmin):
    list_display = ["section", "get_days_display", "start_time", "end_time"]
    list_filter = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "start_time",
        "end_time",
    ]
    search_fields = [
        "section__course__subdepartment__mnemonic",
        "section__course__number",
        "section__course__title",
    ]
    autocomplete_fields = ["section"]

    def get_days_display(self, obj):
        """Return formatted string of meeting days."""
        days = []
        if getattr(obj, "monday", False):
            days.append("MON")
        if getattr(obj, "tuesday", False):
            days.append("TUE")
        if getattr(obj, "wednesday", False):
            days.append("WED")
        if getattr(obj, "thursday", False):
            days.append("THU")
        if getattr(obj, "friday", False):
            days.append("FRI")
        return ", ".join(days)

    get_days_display.short_description = "Days"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("section__course__subdepartment")


class SectionEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        "section",
        "enrollment_taken",
        "enrollment_limit",
        "waitlist_taken",
        "waitlist_limit",
    ]
    search_fields = [
        "section__course__subdepartment__mnemonic",
        "section__course__number",
        "section__course__title",
    ]
    list_filter = ["section__semester"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("section__course__subdepartment", "section__semester")


class CourseGradeAdmin(admin.ModelAdmin):
    ordering = ["course__subdepartment", "course__number", "course__title"]
    search_fields = ["course__subdepartment", "course__number"]


class CourseInstructorGradeAdmin(admin.ModelAdmin):
    ordering = ["instructor__last_name", "instructor__first_name"]
    search_fields = ["instructor__first_name", "instructor__last_name"]


class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ["course", "last_update"]
    search_fields = [
        "course__subdepartment__mnemonic",
        "course__number",
        "course__title",
    ]
    list_filter = ["last_update"]
    readonly_fields = ["last_update"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("course__subdepartment")


class ClubAdmin(admin.ModelAdmin):
    ordering = ["name"]
    search_fields = ["name"]


class ClubCategoryAdmin(admin.ModelAdmin):
    ordering = ["name"]
    search_fields = ["name"]


admin.site.register(Section, SectionAdmin)
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Subdepartment, SubdepartmentAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(CourseGrade, CourseGradeAdmin)
admin.site.register(CourseInstructorGrade, CourseInstructorGradeAdmin)
admin.site.register(SectionTime, SectionTimeAdmin)
admin.site.register(SectionEnrollment, SectionEnrollmentAdmin)
admin.site.register(CourseEnrollment, CourseEnrollmentAdmin)
admin.site.register(Club, ClubAdmin)
admin.site.register(ClubCategory, ClubCategoryAdmin)
