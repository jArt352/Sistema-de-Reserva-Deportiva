import mercadopago
import os
from django.conf import settings

def create_payment_preference(reservation):
    """
    Crea la preferencia de pago incluyendo las URLs de retorno.
    """
    sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

    # Definimos la URL base de tu Frontend (Next.js)
    # En producción esto debería venir de os.getenv('FRONTEND_URL')
    frontend_url = "http://localhost:3000"
    
    webhook_base_url = "https://cyclopedically-electroosmotic-ursula.ngrok-free.dev"

    preference_data = {
        "items": [
            {
                "title": f"Reserva: {reservation.court.name}",
                "quantity": 1,
                "currency_id": "PEN",
                "unit_price": float(reservation.total_price)
            }
        ],
        "payer": {
            "email": reservation.user.email if reservation.user.email else "test_user@test.com"
        },
        
        # --- AQUÍ ESTÁ LA CONFIGURACIÓN NUEVA ---
        "back_urls": {
            # Cuando el pago es EXITOSO, Mercado Pago redirige aquí:
            "success": f"{frontend_url}/checkout/status",
            
            # Cuando falla (tarjeta rechazada):
            "failure": f"{frontend_url}/checkout/status",
            
            # Cuando es diferido (Pago Efectivo/Offline) o está procesando:
            "pending": f"{frontend_url}/checkout/status"
        },
        
        # Redirección automática (sin que el usuario tenga que dar clic en "Volver")
        "auto_return": "approved",
        # ----------------------------------------

        "external_reference": str(reservation.id),
        

        "notification_url": f"{webhook_base_url}/api/webhooks/mercadopago/",
    }

    preference_response = sdk.preference().create(preference_data)
    return preference_response["response"]