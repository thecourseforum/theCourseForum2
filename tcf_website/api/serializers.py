"""DRF Serializers"""

from rest_framework import serializers

from ..models import (
    Course,
    Department,
    Instructor,
    School,
    Semester,
    Subdepartment,
)


class SemesterSerializer(serializers.ModelSerializer):
    """DRF Serializer for Semester"""

    season = serializers.SerializerMethodField()

    def get_season(self, obj):
        """Change the `season` field to TitleCase (or PascalCase)"""
        return obj.season.title()

    class Meta:
        model = Semester
        fields = "__all__"


class SchoolSerializer(serializers.ModelSerializer):
    """DRF Serializer for School"""

    class Meta:
        model = School
        fields = "__all__"


class DepartmentSerializer(serializers.ModelSerializer):
    """DRF Serializer for Department"""

    school = SchoolSerializer(read_only=True)

    class Meta:
        model = Department
        fields = "__all__"


class SubdepartmentSerializer(serializers.ModelSerializer):
    """DRF Serializer for Subdepartment"""

    class Meta:
        model = Subdepartment
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    """DRF Serializer for Course"""

    subdepartment = SubdepartmentSerializer(read_only=True)

    class Meta:
        model = Course
        fields = "__all__"


class CourseSimpleStatsSerializer(CourseSerializer):
    """DRF Serializer for Course including some review statistics"""

    semester_last_taught = SemesterSerializer(read_only=True)
    average_rating = serializers.FloatField(allow_null=True)
    average_difficulty = serializers.FloatField(allow_null=True)
    average_gpa = serializers.FloatField(allow_null=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "number",
            "subdepartment",
            "semester_last_taught",
            "average_rating",
            "average_difficulty",
            "average_gpa",
            "is_recent",
        ]


class CourseAllStatsSerializer(CourseSimpleStatsSerializer):
    """DRF Serializer for Course including all review statistics"""

    # ratings
    average_instructor = serializers.FloatField(allow_null=True)
    average_fun = serializers.FloatField(allow_null=True)
    average_recommendability = serializers.FloatField(allow_null=True)
    # workload
    average_hours_per_week = serializers.FloatField(allow_null=True)
    average_amount_reading = serializers.FloatField(allow_null=True)
    average_amount_writing = serializers.FloatField(allow_null=True)
    average_amount_group = serializers.FloatField(allow_null=True)
    average_amount_homework = serializers.FloatField(allow_null=True)
    # grades
    a_plus = serializers.IntegerField(allow_null=True)
    a = serializers.IntegerField(allow_null=True)
    a_minus = serializers.IntegerField(allow_null=True)
    b_plus = serializers.IntegerField(allow_null=True)
    b = serializers.IntegerField(allow_null=True)
    b_minus = serializers.IntegerField(allow_null=True)
    c_plus = serializers.IntegerField(allow_null=True)
    c = serializers.IntegerField(allow_null=True)
    c_minus = serializers.IntegerField(allow_null=True)
    dfw = serializers.IntegerField(allow_null=True)
    total_enrolled = serializers.IntegerField(allow_null=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "number",
            "subdepartment",
            "semester_last_taught",
            "is_recent",
            # ratings
            "average_rating",
            "average_instructor",
            "average_fun",
            "average_recommendability",
            "average_difficulty",
            # workload
            "average_hours_per_week",
            "average_amount_reading",
            "average_amount_writing",
            "average_amount_group",
            "average_amount_homework",
            # grades
            "a_plus",
            "a",
            "a_minus",
            "b_plus",
            "b",
            "b_minus",
            "c_plus",
            "c",
            "c_minus",
            "dfw",
            "total_enrolled",
            "average_gpa",
        ]


class InstructorSerializer(serializers.ModelSerializer):
    """DRF Serializer for Instructor"""

    class Meta:
        model = Instructor
        fields = "__all__"
