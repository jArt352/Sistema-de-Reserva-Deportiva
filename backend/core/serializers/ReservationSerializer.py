from rest_framework import serializers
from core.models import Reservation, Court

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ('total_price', 'amount_pending', 'status', 'user')

class QuoteSerializer(serializers.Serializer):
    """
    Serializer simple solo para validar los datos de la cotización.
    No guarda nada en la BD.
    """
    court_id = serializers.IntegerField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    
    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("La hora de inicio debe ser anterior a la de fin.")
        return data