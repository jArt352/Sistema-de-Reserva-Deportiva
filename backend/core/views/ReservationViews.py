from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
import dateutil.parser
import datetime
from django.utils import timezone

# Modelos y Serializers (Ajustado)
from core.models import Reservation, Court, CourtTypePrice
from core.serializers.ReservationSerializer import ReservationSerializer, QuoteSerializer # Asumimos 'reservation.py'

# Servicios (Para Mercado Pago)
from core.services import create_payment_preference

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        
        try:
            court_id = data.get('court')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            
            with transaction.atomic():
                court = get_object_or_404(Court, pk=court_id)
                
                # ... (Validación de Disponibilidad y Precios - sin cambios) ...
                start_dt = dateutil.parser.parse(start_time)
                end_dt = dateutil.parser.parse(end_time)
                
                if timezone.is_naive(start_dt): start_dt = timezone.make_aware(start_dt)
                if timezone.is_naive(end_dt): end_dt = timezone.make_aware(end_dt)

                total_price, _ = self.calculate_complex_price(court, start_dt, end_dt)
                
                # C. Definir el usuario
                user = request.user if request.user.is_authenticated else None
                if not user:
                    from django.contrib.auth.models import User
                    user = User.objects.first()
                    if not user:
                         user = User.objects.create_user(username='invitado', email='invitado@test.com')

                reservation = Reservation.objects.create(
                    court=court, user=user, start_time=start_dt, end_time=end_dt,
                    subtotal_court=total_price, total_price=total_price,
                    status='pending', amount_paid=0
                )
                
                # D. INTEGRACIÓN MERCADO PAGO: Llamada al servicio
                mp_result = create_payment_preference(reservation)
                
                # E. Si el servicio devolvió None, significa que falló en MP
                if mp_result is None:
                     raise Exception("Fallo en la pasarela de pago (Verificar logs de MP en Django).")

                # Respuesta con los datos de MP
                response_data = ReservationSerializer(reservation).data
                response_data['preference_id'] = mp_result.get("id")
                response_data['payment_url'] = mp_result.get("sandbox_init_point")
                
                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Ahora el error se propagará con el mensaje que generamos
            print(f"❌ ERROR FATAL AL CREAR RESERVA: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # =========================================================
    # 2. MÉTODO QUOTE (Calculadora de Precios)
    # =========================================================
    @action(detail=False, methods=['post'])
    def quote(self, request):
        serializer = QuoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        court = get_object_or_404(Court, pk=data['court_id'])
        start_dt = data['start_time']
        end_dt = data['end_time']

        total_price, breakdown = self.calculate_complex_price(court, start_dt, end_dt)

        return Response({
            "court_name": court.name,
            "total_price": total_price,
            "currency": "PEN",
            "duration_hours": (end_dt - start_dt).total_seconds() / 3600,
            "breakdown": breakdown
        })

    # =========================================================
    # 3. LÓGICA INTERNA DE PRECIOS
    # =========================================================
    def calculate_complex_price(self, court, start_dt, end_dt):
        total = Decimal('0.00')
        breakdown = []

        type_prices = CourtTypePrice.objects.filter(
            court_type=court.court_type, 
            company=court.company
        ).select_related('time_slot')

        req_start_time = start_dt.time()
        req_end_time = end_dt.time()

        for tp in type_prices:
            slot = tp.time_slot
            price_per_hour = tp.price

            overlap_start = max(req_start_time, slot.start_time)
            overlap_end = min(req_end_time, slot.end_time)

            if overlap_start < overlap_end:
                dummy_date = datetime.date(2000, 1, 1)
                dt1 = datetime.datetime.combine(dummy_date, overlap_start)
                dt2 = datetime.datetime.combine(dummy_date, overlap_end)
                
                duration_hours = Decimal((dt2 - dt1).total_seconds() / 3600)
                cost = duration_hours * price_per_hour
                total += cost

                breakdown.append({
                    "slot_name": slot.name,
                    "price_per_hour": price_per_hour,
                    "hours": round(duration_hours, 2),
                    "subtotal": round(cost, 2)
                })

        return total, breakdown