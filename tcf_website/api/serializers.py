"""DRF Serializers"""
from rest_framework import serializers
from ..models import School


class SchoolSerializer(serializers.ModelSerializer):
    """DRF Serializer for School"""
    class Meta:
        model = School
        fields = '__all__'
