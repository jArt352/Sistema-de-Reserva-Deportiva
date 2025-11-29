# backend/core/routers.py
from rest_framework.routers import DefaultRouter
from core.views import CompanyViewSet, CourtViewSet, ReservationViewSet

# Creamos el router principal
router = DefaultRouter()

# Registramos las rutas (Endpoints)
# El primer argumento es la URL (ej: /api/companies/)
# El segundo es el ViewSet que maneja la lógica
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'courts', CourtViewSet, basename='court')
router.register(r'reservations', ReservationViewSet, basename='reservation')
# A futuro agregarás aquí:
# router.register(r'reservations', ReservationViewSet)
# router.register(r'payments', PaymentViewSet)

# OJO: No necesitamos exportar nada explícitamente, 
# la variable 'router' ya es accesible al importar este archivo.