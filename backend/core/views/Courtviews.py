from rest_framework import viewsets
from core.models import Court
from core.serializers import CourtSerializer
from rest_framework.decorators import action
from django.utils.dateparse import parse_date
from core.models import Court, Reservation
from rest_framework.response import Response

class CourtViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Court.objects.filter(is_active=True).select_related('court_type', 'company')
    serializer_class = CourtSerializer

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Devuelve las reservas existentes para una fecha específica.
        Uso: GET /api/courts/1/availability/?date=2023-11-28
        """
        court = self.get_object()
        date_str = request.query_params.get('date')

        if not date_str:
            return Response(
                {"error": "El parámetro 'date' (YYYY-MM-DD) es obligatorio."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        target_date = parse_date(date_str)
        if not target_date:
            return Response(
                {"error": "Formato de fecha inválido."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Buscamos reservas para esa cancha en ese día (Rango de 00:00 a 23:59)
        # Filtramos las que NO estén canceladas o anuladas (voided)
        reservations = Reservation.objects.filter(
            court=court,
            start_time__date=target_date,
            status__in=['pending', 'confirmed', 'completed']
        ).values('start_time', 'end_time', 'status')

        # 2. Formateamos la respuesta para que el Frontend la entienda fácil
        booked_slots = []
        for res in reservations:
            booked_slots.append({
                "start": res['start_time'].strftime('%H:%M'),
                "end": res['end_time'].strftime('%H:%M'),
                "status": res['status']
            })

        # 3. Obtenemos el horario de atención de la empresa para ese día de la semana
        # weekday(): Lunes=0, Domingo=6
        day_of_week = target_date.weekday() 
        business_hours = court.company.business_hours.filter(weekday=day_of_week).first()

        response_data = {
            "court_id": court.id,
            "date": date_str,
            "business_hours": {
                "open": business_hours.open_time.strftime('%H:%M') if business_hours else None,
                "close": business_hours.close_time.strftime('%H:%M') if business_hours else None,
                "is_open": business_hours is not None
            },
            "booked_slots": booked_slots
        }

        return Response(response_data)