# apps/bookings/admin.py
# CORRECTED ADMIN - Session 26

from django.contrib import admin
from .models import (
    Traveller, Booking, AirBooking, AirSegment, 
    AccommodationBooking, CarHireBooking, Invoice, ServiceFee
)


# ============================================================================
# INLINE ADMINS (for showing related objects)
# ============================================================================

class AirSegmentInline(admin.TabularInline):
    model = AirSegment
    extra = 0
    fields = ['segment_number', 'airline_iata_code', 'airline_name', 'flight_number', 
              'origin_airport_iata_code', 'destination_airport_iata_code', 
              'departure_date', 'departure_time', 'distance_km', 'carbon_emissions_kg']
    readonly_fields = ['distance_km', 'carbon_emissions_kg']


class AirBookingInline(admin.TabularInline):
    """Show air bookings within a main Booking"""
    model = AirBooking
    extra = 0
    fields = ['trip_type', 'travel_class', 'origin_airport_iata_code', 
              'destination_airport_iata_code', 'ticket_number', 'total_fare']
    show_change_link = True  # Allows clicking to see full air booking with segments


class AccommodationBookingInline(admin.TabularInline):
    """Show accommodation bookings within a main Booking"""
    model = AccommodationBooking
    extra = 0
    fields = ['hotel_name', 'city', 'country', 'check_in_date', 
              'check_out_date', 'number_of_nights', 'nightly_rate']


class CarHireBookingInline(admin.TabularInline):
    """Show car hire bookings within a main Booking"""
    model = CarHireBooking
    extra = 0
    fields = ['rental_company', 'vehicle_type', 'pickup_city', 'country',
              'pickup_date', 'dropoff_date', 'number_of_days', 'daily_rate']


class ServiceFeeInline(admin.TabularInline):
    """Show service fees within a main Booking"""
    model = ServiceFee
    extra = 0
    fields = ['fee_type', 'fee_date', 'fee_amount', 'booking_channel']


# ============================================================================
# MAIN MODEL ADMINS
# ============================================================================

@admin.register(Traveller)
class TravellerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'organization', 'employee_id', 'is_active']
    list_filter = ['organization', 'is_active', 'department']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'user')
        }),
        ('Organization', {
            'fields': ('organization', 'employee_id', 'department', 'cost_center')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # FIXED: Removed 'booking_type' from list_display and list_filter
    list_display = ['agent_booking_reference', 'supplier_reference', 'traveller', 
                    'organization', 'travel_date', 'total_amount', 'currency', 'status']
    list_filter = ['status', 'organization', 'travel_date', 'policy_compliant']  # Removed booking_type
    search_fields = ['agent_booking_reference', 'supplier_reference', 
                     'traveller__first_name', 'traveller__last_name']
    date_hierarchy = 'travel_date'
    
    # NEW: Show all component bookings as inlines
    inlines = [
        AirBookingInline,
        AccommodationBookingInline,
        CarHireBookingInline,
        ServiceFeeInline,
    ]
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('agent_booking_reference', 'supplier_reference', 'status'),
            'description': 'Master booking reference (e.g., GPT001)'
        }),
        ('Parties', {
            'fields': ('organization', 'traveller', 
                      'travel_arranger', 'travel_arranger_text',
                      'travel_consultant', 'travel_consultant_text')
        }),
        ('Dates', {
            'fields': ('booking_date', 'travel_date', 'return_date')
        }),
        ('Financial', {
            'fields': ('currency', 'total_amount', 'base_fare', 'taxes', 'fees'),
            'description': 'Total amount = sum of all air bookings + hotels + cars + fees'
        }),
        ('Currency Conversion', {
            'fields': ('total_amount_base', 'exchange_rate', 'exchange_rate_date'),
            'classes': ('collapse',)
        }),
        ('Compliance', {
            'fields': ('policy_compliant', 'advance_booking_days')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AirBooking)
class AirBookingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'trip_type', 'travel_class', 'origin_airport_iata_code', 
                    'destination_airport_iata_code', 'ticket_number', 'total_fare']
    list_filter = ['trip_type', 'travel_class', 'primary_airline_iata_code']
    search_fields = ['booking__agent_booking_reference', 'ticket_number', 
                    'origin_airport_iata_code', 'destination_airport_iata_code']
    
    inlines = [AirSegmentInline]
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Flight Details', {
            'fields': ('trip_type', 'travel_class', 'ticket_number', 'total_fare')
        }),
        ('Route', {
            'fields': ('origin_airport_iata_code', 'destination_airport_iata_code')
        }),
        ('Airline', {
            'fields': ('primary_airline_iata_code', 'primary_airline_name')
        }),
        ('Compliance', {
            'fields': ('lowest_fare_available', 'lowest_fare_currency', 'potential_savings'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AirSegment)
class AirSegmentAdmin(admin.ModelAdmin):
    list_display = ['air_booking', 'segment_number', 'airline_iata_code', 'flight_number',
                    'origin_airport_iata_code', 'destination_airport_iata_code', 
                    'departure_date', 'distance_km', 'carbon_emissions_kg']
    list_filter = ['airline_iata_code', 'departure_date']
    search_fields = ['air_booking__booking__agent_booking_reference', 'flight_number',
                    'origin_airport_iata_code', 'destination_airport_iata_code']
    readonly_fields = ['distance_km', 'carbon_emissions_kg']
    
    fieldsets = (
        ('Air Booking', {
            'fields': ('air_booking', 'segment_number')
        }),
        ('Flight', {
            'fields': ('airline_iata_code', 'airline_name', 'flight_number')
        }),
        ('Route', {
            'fields': ('origin_airport_iata_code', 'destination_airport_iata_code')
        }),
        ('Schedule', {
            'fields': ('departure_date', 'departure_time', 'arrival_date', 'arrival_time')
        }),
        ('Booking Details', {
            'fields': ('booking_class', 'fare_basis')
        }),
        ('Calculated Fields', {
            'fields': ('distance_km', 'carbon_emissions_kg'),
            'description': 'Auto-calculated on save'
        }),
    )


@admin.register(AccommodationBooking)
class AccommodationBookingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'hotel_name', 'city', 'country', 
                    'check_in_date', 'number_of_nights', 'nightly_rate', 'currency']
    list_filter = ['country', 'city', 'hotel_chain']
    search_fields = ['booking__agent_booking_reference', 'hotel_name', 'city']
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Hotel', {
            'fields': ('hotel_name', 'hotel_chain')
        }),
        ('Location', {
            'fields': ('city', 'country', 'address')
        }),
        ('Stay Details', {
            'fields': ('check_in_date', 'check_out_date', 'number_of_nights', 'room_type')
        }),
        ('Rate', {
            'fields': ('nightly_rate', 'currency', 'nightly_rate_base', 'total_amount_base')
        }),
    )


@admin.register(CarHireBooking)
class CarHireBookingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'rental_company', 'vehicle_type', 
                    'pickup_city', 'country', 'pickup_date', 'number_of_days', 'daily_rate']
    list_filter = ['country', 'rental_company', 'vehicle_type']
    search_fields = ['booking__agent_booking_reference', 'rental_company', 'pickup_city']
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Rental Company & Vehicle', {
            'fields': ('rental_company', 'vehicle_type', 'vehicle_category', 'vehicle_make_model')
        }),
        ('Pickup', {
            'fields': ('pickup_location', 'pickup_city', 'pickup_date', 'pickup_time')
        }),
        ('Dropoff', {
            'fields': ('dropoff_location', 'dropoff_city', 'dropoff_date', 'dropoff_time')
        }),
        ('Location', {
            'fields': ('country',)
        }),
        ('Rate', {
            'fields': ('number_of_days', 'daily_rate', 'currency', 'daily_rate_base', 'total_amount_base')
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    # FIXED: Changed 'invoice_amount' to 'total_amount'
    list_display = ['invoice_number', 'organization', 'invoice_date', 
                    'due_date', 'total_amount', 'payment_status']
    list_filter = ['payment_status', 'organization', 'invoice_date']
    search_fields = ['invoice_number', 'organization__name']
    date_hierarchy = 'invoice_date'
    
    fieldsets = (
        ('Invoice Details', {
            'fields': ('invoice_number', 'invoice_date', 'due_date')
        }),
        ('Related', {
            'fields': ('organization', 'booking')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'gst_amount', 'total_amount', 'currency')
        }),
        ('Payment', {
            'fields': ('payment_status', 'payment_date')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ServiceFee)
class ServiceFeeAdmin(admin.ModelAdmin):
    # FIXED: Changed 'amount' to 'fee_amount'
    list_display = ['fee_type', 'organization', 'traveller', 
                    'fee_date', 'fee_amount', 'booking_channel']
    list_filter = ['fee_type', 'organization', 'booking_channel', 'fee_date']
    search_fields = ['organization__name', 'traveller__first_name', 'traveller__last_name']
    date_hierarchy = 'fee_date'
    
    fieldsets = (
        ('Fee Details', {
            'fields': ('fee_type', 'fee_date', 'fee_amount', 'currency')
        }),
        ('Related', {
            'fields': ('booking', 'organization', 'traveller')
        }),
        ('Channel', {
            'fields': ('booking_channel',)
        }),
        ('Import Tracking', {
            'fields': ('import_batch',),
            'classes': ('collapse',)
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Make import_batch optional for manual entries"""
        form = super().get_form(request, obj, **kwargs)
        if 'import_batch' in form.base_fields:
            form.base_fields['import_batch'].required = False
        return form