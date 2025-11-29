import mercadopago
import os
import hashlib
import hmac
import urllib.parse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import HttpRequest # Necesaria para obtener la URL completa

from core.models import Reservation, Payment
from decimal import Decimal

# --- LÓGICA DE SEGURIDAD HMAC ---
def validate_signature(request: HttpRequest, secret_key):
    """
    Valida la firma HMAC SHA256 que Mercado Pago envía en el header x-signature.
    Retorna True si la firma es válida.
    """
    xSignature = request.headers.get("x-signature")
    xRequestId = request.headers.get("x-request-id")
    
    if not xSignature or not xRequestId:
        print("❌ VALIDACIÓN FALLIDA: Faltan headers X-Signature o X-Request-Id")
        return False

    # 1. Obtener Query params (Django usa request.GET)
    queryParams = request.GET.dict()
    dataID = queryParams.get("data.id")

    # 2. Extraer ts y v1 del header x-signature
    parts = xSignature.split(",")
    ts = None
    hash_v1 = None

    for part in parts:
        keyValue = part.split("=", 1)
        if len(keyValue) == 2:
            key = keyValue[0].strip()
            value = keyValue[1].strip()
            if key == "ts":
                ts = value
            elif key == "v1":
                hash_v1 = value
    
    if not ts or not hash_v1 or not dataID:
        print("❌ VALIDACIÓN FALLIDA: Datos incompletos en el header/query.")
        return False

    # 3. Generar el template: id:[data.id_url];request-id:[x-request-id_header];ts:[ts_header];
    manifest = f"id:{dataID};request-id:{xRequestId};ts:{ts};"

    # 4. Crear la contraclave (HMAC SHA256)
    hmac_obj = hmac.new(secret_key.encode(), msg=manifest.encode(), digestmod=hashlib.sha256)
    sha_calculated = hmac_obj.hexdigest()

    # 5. Comparar la clave calculada con la que envió MP
    if sha_calculated == hash_v1:
        return True
    else:
        print(f"❌ VALIDACIÓN FALLIDA: Firma no coincide.")
        return False
# --- FIN LÓGICA DE SEGURIDAD ---


class MercadoPagoWebhookView(APIView):
    def post(self, request):
        # 1. Obtener tipo y ID del body o query params
        event_type = request.data.get('type') or request.query_params.get('topic')
        data_id = request.data.get('data', {}).get('id') or request.query_params.get('id')
        
        # 2. Validar Origen (Seguridad)
        secret_key = os.getenv("MP_WEBHOOK_SECRET")
        
        if secret_key and not validate_signature(request, secret_key):
             # Si no pasa la validación de firma, ignoramos (para prevenir fraude)
             print("🚨 ALERTA DE SEGURIDAD: Webhook con firma inválida ignorado.")
             return Response(status=status.HTTP_200_OK)
        
        print(f"🔔 WEBHOOK RECIBIDO: Tipo={event_type}, ID={data_id}")
        
        if event_type == 'payment' and data_id:
            return self.handle_payment(data_id)
        
        # Siempre responder 200 OK para evitar que Mercado Pago reintente (Regla de los 22s)
        return Response(status=status.HTTP_200_OK)

    def handle_payment(self, payment_id):
        """ Lógica para consultar el SDK y actualizar la BD. """
        try:
            sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
            payment_info = sdk.payment().get(payment_id)
            
            if payment_info["status"] != 200:
                print(f"❌ Pago ID {payment_id} no encontrado en MP.")
                return Response(status=status.HTTP_200_OK)

            payment_data = payment_info["response"]
            
            # Extraer datos clave
            external_ref = payment_data.get("external_reference") 
            status_mp = payment_data.get("status") 
            transaction_amount = payment_data.get("transaction_amount")

            if not external_ref:
                return Response(status=status.HTTP_200_OK)

            # Actualizar la Reserva en nuestra BD (Transacción Atómica)
            with transaction.atomic():
                reservation = Reservation.objects.select_for_update().get(id=external_ref)
                
                # Idempotencia: Si ya procesamos este ID, no hacemos nada
                if Payment.objects.filter(transaction_id=str(payment_id)).exists():
                    return Response(status=status.HTTP_200_OK)

                # Creamos el registro del pago
                Payment.objects.create(
                    reservation=reservation,
                    amount=transaction_amount,
                    payment_method='gateway',
                    status='approved' if status_mp == 'approved' else 'rejected',
                    transaction_id=str(payment_id)
                )

                # Si está aprobado, confirmamos la reserva
                if status_mp == 'approved':
                    reservation.amount_paid += Decimal(str(transaction_amount))
                    reservation.save()
                    print(f"   ✅ ¡RESERVA CONFIRMADA! Saldo pagado: {reservation.amount_paid}")

        except Exception as e:
            print(f"Error interno webhook: {e}")
        
        return Response(status=status.HTTP_200_OK)