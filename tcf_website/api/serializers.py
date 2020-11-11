"""DRF Serializers"""
from rest_framework import serializers
from ..models import (Course, Department, School, Instructor, Semester,
                      Subdepartment)


class SemesterSerializer(serializers.ModelSerializer):
    """DRF Serializer for Semester"""
    class Meta:
        model = Semester
        fields = '__all__'


class SchoolSerializer(serializers.ModelSerializer):
    """DRF Serializer for School"""
    class Meta:
        model = School
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    """DRF Serializer for Department"""
    school = SchoolSerializer(read_only=True)

    class Meta:
        model = Department
        fields = '__all__'


class SubdepartmentSerializer(serializers.ModelSerializer):
    """DRF Serializer for Subdepartment"""
    class Meta:
        model = Subdepartment
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    """DRF Serializer for Course"""
    subdepartment = SubdepartmentSerializer(read_only=True)

    class Meta:
        model = Course
        fields = '__all__'


class CourseWithStatsSerializer(CourseSerializer):
    """DRF Serializer for Course including review statistics"""
    semester_last_taught = SemesterSerializer(read_only=True)
    average_rating = serializers.FloatField(allow_null=True)
    average_difficulty = serializers.FloatField(allow_null=True)
    average_gpa = serializers.FloatField(allow_null=True)
    a_plus = serializers.IntegerField(allow_null=True)
    a = serializers.IntegerField(allow_null=True)
    a_minus = serializers.IntegerField(allow_null=True)
    b_plus = serializers.IntegerField(allow_null=True)
    b = serializers.IntegerField(allow_null=True)
    b_minus = serializers.IntegerField(allow_null=True)
    c_plus = serializers.IntegerField(allow_null=True)
    c = serializers.IntegerField(allow_null=True)
    c_minus = serializers.IntegerField(allow_null=True)
    d_plus = serializers.IntegerField(allow_null=True)
    d = serializers.IntegerField(allow_null=True)
    d_minus = serializers.IntegerField(allow_null=True)
    f = serializers.IntegerField(allow_null=True)
    ot = serializers.IntegerField(allow_null=True)
    drop = serializers.IntegerField(allow_null=True)
    withdraw = serializers.IntegerField(allow_null=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'number', 'subdepartment',
                  'semester_last_taught', 'average_rating',
                  'a_plus', 'a', 'a_minus', 'b_plus', 'b', 'b_minus',
                  'c_plus', 'c', 'c_minus', 'd_plus', 'd', 'd_minus',
                  'f', 'ot', 'drop', 'withdraw',
                  'average_difficulty', 'average_gpa', 'is_recent']


class InstructorSerializer(serializers.ModelSerializer):
    """DRF Serializer for Instructor"""
    class Meta:
        model = Instructor
        fields = '__all__'
