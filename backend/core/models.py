from decimal import Decimal
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

# ==========================================
# 1. CORE Y MULTI-TENANCY
# ==========================================

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField("Teléfono", max_length=20, blank=True)
    document_number = models.CharField("DNI/ID", max_length=20, blank=True)
    managed_company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='managers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

class License(models.Model):
    LICENSE_TYPE_CHOICES = [
        ('free', 'Gratis (3 meses)'),
        ('monthly', 'Mensual'),
        ('annual', 'Anual'),
    ]
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('expired', 'Vencida'),
        ('suspended', 'Suspendida'),
    ]

    license_key = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPE_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    start_date = models.DateField()
    end_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    def is_valid(self):
        today = timezone.now().date()
        return self.status == 'active' and self.start_date <= today <= self.end_date

class Company(models.Model):
    name = models.CharField("Nombre Comercial", max_length=200)
    license = models.OneToOneField(License, on_delete=models.PROTECT, related_name='company')
    
    # --- SECCIÓN ELIMINADA: Políticas de cancelación y reembolso ---
    
    # Configuración de Pagos
    advance_payment_percentage = models.PositiveIntegerField(
        "Porcentaje de Seña",
        default=50,
        validators=[MaxValueValidator(100)],
        help_text="Porcentaje mínimo para confirmar reserva."
    )

    address = models.CharField(max_length=300, blank=True)
    latitude = models.DecimalField(max_digits=18, decimal_places=15, null=True, blank=True)
    longitude = models.DecimalField(max_digits=18, decimal_places=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class BusinessHour(models.Model):
    WEEKDAYS = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'),
        (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo')
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='business_hours')
    weekday = models.IntegerField(choices=WEEKDAYS)
    open_time = models.TimeField()
    close_time = models.TimeField()

    class Meta:
        unique_together = ('company', 'weekday')
        ordering = ['weekday']

# ==========================================
# 2. INVENTARIO Y PRECIOS
# ==========================================

class CourtType(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='court_types')
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Court(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='courts')
    court_type = models.ForeignKey(CourtType, on_delete=models.PROTECT, related_name='courts')
    name = models.CharField("Nombre de Cancha", max_length=150)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.name} - {self.court_type.name}"

class TimeSlot(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='time_slots')
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    class Meta:
        ordering = ['start_time']

class CourtTypePrice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    court_type = models.ForeignKey(CourtType, on_delete=models.CASCADE)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    class Meta:
        unique_together = ('court_type', 'time_slot')

class AddOn(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='addons')
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

# ==========================================
# 3. TRANSACCIONAL (Flujo Simplificado)
# ==========================================

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente de Pago'),
        ('confirmed', 'Confirmada'),
        ('completed', 'Completada'),
        ('voided', 'Anulada por Admin'), # Mantenemos solo para anulación manual administrativa, sin lógica de reembolso
    ]

    court = models.ForeignKey(Court, on_delete=models.PROTECT, related_name='reservations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    
    subtotal_court = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal_addons = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_pending = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_time']

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Hora fin debe ser mayor a inicio.")

    def save(self, *args, **kwargs):
        self.total_price = self.subtotal_court + self.subtotal_addons
        self.amount_pending = self.total_price - self.amount_paid
        
        # Lógica automática de confirmación
        if self.status == 'pending':
            required_advance = (self.total_price * self.court.company.advance_payment_percentage) / 100
            # Confirmamos si cubre la seña y el precio no es cero
            if self.amount_paid >= required_advance and self.total_price > 0:
                self.status = 'confirmed'
                
        super().save(*args, **kwargs)

    @property
    def duration_hours(self):
        diff = self.end_time - self.start_time
        return diff.total_seconds() / 3600

class ReservationAddOn(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='addon_items')
    addon = models.ForeignKey(AddOn, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        if not self.price_snapshot:
            self.price_snapshot = self.addon.price
        super().save(*args, **kwargs)
        self.update_reservation_totals()

    def update_reservation_totals(self):
        total_addons = sum(item.quantity * item.price_snapshot for item in self.reservation.addon_items.all())
        self.reservation.subtotal_addons = total_addons
        self.reservation.save()

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('transfer', 'Transferencia/Yape/Plin'),
        ('card', 'Tarjeta Crédito/Débito'),
        ('cash', 'Efectivo'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pendiente revisión'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]

    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    proof_image = models.ImageField(upload_to='payments/', null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def approve(self, user):
        """Aprueba pago e impacta en la reserva."""
        self.status = 'approved'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
        
        self.reservation.amount_paid += self.amount
        self.reservation.save()

# --- MODELO Refund ELIMINADO ---

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.profile.save()