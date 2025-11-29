from rest_framework import serializers
from core.models import Company

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'address', 'latitude', 'longitude']