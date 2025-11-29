from django.urls import path, include
from .routers import router

# --- AGREGAR ESTA IMPORTACIÓN ---
# OJO: Respetando las mayúsculas de tu archivo WebHookViews.py
from core.views.WebHookViews import MercadoPagoWebhookView

urlpatterns = [
    # 1. Aquí se cargan todas las rutas del router (reservations, courts, etc.)
    path('', include(router.urls)),

    # 2. --- AGREGAR ESTA RUTA MANUAL ---
    # Esta es la dirección que le diste a Ngrok y a Mercado Pago
    path('webhooks/mercadopago/', MercadoPagoWebhookView.as_view(), name='mp-webhook'),
]