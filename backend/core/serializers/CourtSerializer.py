from rest_framework import serializers
from core.models import Court, CourtType, CourtTypePrice, TimeSlot

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'name', 'start_time', 'end_time']

class CourtTypePriceSerializer(serializers.ModelSerializer):
    time_slot = TimeSlotSerializer(read_only=True)
    class Meta:
        model = CourtTypePrice
        fields = ['id', 'time_slot', 'price']

class CourtTypeSerializer(serializers.ModelSerializer):
    prices = serializers.SerializerMethodField()
    class Meta:
        model = CourtType
        fields = ['id', 'name', 'prices']

    def get_prices(self, obj):
        # Nota: Aquí usamos obj.court_type_prices si configuraste related_name
        # o el filtro directo como hicimos antes:
        prices = CourtTypePrice.objects.filter(court_type=obj, company=obj.company)
        return CourtTypePriceSerializer(prices, many=True).data

class CourtSerializer(serializers.ModelSerializer):
    court_type = CourtTypeSerializer(read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    class Meta:
        model = Court
        fields = ['id', 'name', 'company_name', 'court_type', 'is_active']