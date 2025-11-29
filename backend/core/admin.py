from django.contrib import admin
from .models import (
    UserProfile, License, Company, BusinessHour, 
    CourtType, Court, TimeSlot, CourtTypePrice, 
    AddOn, Reservation, ReservationAddOn, Payment
)

# --- 1. CONFIGURACIÓN DE USUARIOS Y EMPRESAS ---

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'is_company_admin')
    search_fields = ('user__username', 'user__email', 'phone')
    
    def is_company_admin(self, obj):
        return obj.managed_company.name if obj.managed_company else "Cliente Final"
    is_company_admin.short_description = "Empresa"

class BusinessHourInline(admin.TabularInline):
    model = BusinessHour
    extra = 7 # Para mostrar los 7 días de una vez

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_status', 'created_at')
    inlines = [BusinessHourInline] # Permite editar horarios dentro de la empresa
    
    def license_status(self, obj):
        return obj.license.status

@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ('license_key', 'company_name', 'status', 'end_date')
    list_filter = ('status', 'license_type')
    
    def company_name(self, obj):
        # Manejo de error por si la licencia aun no tiene empresa asignada
        return obj.company.name if hasattr(obj, 'company') else "-"

# --- 2. INVENTARIO Y PRECIOS ---

class CourtTypePriceInline(admin.TabularInline):
    model = CourtTypePrice
    extra = 1

@admin.register(CourtType)
class CourtTypeAdmin(admin.ModelAdmin):
    inlines = [CourtTypePriceInline] # Ver precios al editar el tipo
    list_display = ('name', 'company')

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'start_time', 'end_time')
    list_filter = ('company',)

@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('name', 'court_type', 'company', 'is_active')
    list_filter = ('company', 'court_type')

@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'price', 'stock_quantity')

# --- 3. GESTIÓN DE RESERVAS Y PAGOS ---

class ReservationAddOnInline(admin.TabularInline):
    model = ReservationAddOn
    extra = 0
    readonly_fields = ('price_snapshot',) # Para que nadie altere el precio histórico

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'court', 'start_time', 'total_price', 'amount_pending', 'status_colored')
    list_filter = ('status', 'start_time', 'court__company')
    search_fields = ('user__username', 'user__email', 'id')
    inlines = [ReservationAddOnInline, PaymentInline]
    readonly_fields = ('total_price', 'subtotal_court', 'subtotal_addons', 'amount_pending')
    
    # Colorear el estado para verlo rápido visualmente
    def status_colored(self, obj):
        from django.utils.html import format_html
        colors = {
            'pending': 'orange',
            'confirmed': 'green',
            'completed': 'blue',
            'cancelled': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_colored.short_description = 'Estado'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'reservation', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method')
    actions = ['approve_payments']

    def approve_payments(self, request, queryset):
        for payment in queryset:
            payment.approve(request.user)
    approve_payments.short_description = "Aprobar pagos seleccionados"