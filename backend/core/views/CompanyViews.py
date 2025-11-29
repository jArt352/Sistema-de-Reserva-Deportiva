from rest_framework import viewsets
from core.models import Company
from core.serializers import CompanySerializer

class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer