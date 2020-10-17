"""DRF Serializers"""
from rest_framework import serializers
from ..models import Department, School


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
