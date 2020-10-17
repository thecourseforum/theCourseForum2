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
    class Meta:
        model = Course
        fields = '__all__'


class InstructorSerializer(serializers.ModelSerializer):
    """DRF Serializer for Instructor"""
    class Meta:
        model = Instructor
        fields = '__all__'
