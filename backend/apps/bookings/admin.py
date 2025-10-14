from django.contrib import admin
from .models import Traveller, Booking


@admin.register(Traveller)
class TravellerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'organization', 'department', 'cost_center', 'is_active']
    list_filter = ['organization', 'is_active', 'department']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_reference', 'traveller', 'organization', 'booking_type', 'travel_date', 'total_amount', 'status']
    list_filter = ['booking_type', 'status', 'organization']
    search_fields = ['booking_reference']
    readonly_fields = ['created_at', 'updated_at']
