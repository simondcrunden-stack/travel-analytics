from django.contrib import admin
from .models import (
    Traveller, 
    Booking, 
    AirBooking, 
    AirSegment, 
    AccommodationBooking, 
    CarHireBooking,
    Invoice,
    ServiceFee
)


@admin.register(Traveller)
class TravellerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'organization', 'employee_id', 'cost_center', 'is_active']
    list_filter = ['is_active', 'organization', 'department']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'employee_id')
        }),
        ('Organization', {
            'fields': ('organization',)
        }),
        ('Department & Cost Center', {
            'fields': ('department', 'cost_center')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_reference', 'traveller', 'organization', 'booking_type', 
                    'travel_date', 'total_amount', 'currency', 'status']
    list_filter = ['booking_type', 'status', 'organization', 'booking_date', 'travel_date']
    search_fields = ['booking_reference', 'traveller__first_name', 'traveller__last_name']
    date_hierarchy = 'travel_date'
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_reference', 'booking_type', 'status')
        }),
        ('Traveller & Organization', {
            'fields': ('organization', 'traveller')
        }),
        ('Dates', {
            'fields': ('booking_date', 'travel_date', 'return_date')
        }),
        ('Financial', {
            'fields': ('currency', 'total_amount', 'base_fare', 'taxes', 'fees')
        }),
    )


@admin.register(AirBooking)
class AirBookingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'trip_type', 'travel_class', 'origin_airport_iata_code', 
                    'destination_airport_iata_code', 'ticket_number']
    list_filter = ['trip_type', 'travel_class', 'primary_airline_iata_code']
    search_fields = ['booking__booking_reference', 'ticket_number', 
                    'origin_airport_iata_code', 'destination_airport_iata_code']
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Flight Details', {
            'fields': ('trip_type', 'travel_class', 'ticket_number')
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


class AirSegmentInline(admin.TabularInline):
    model = AirSegment
    extra = 0
    fields = ['segment_number', 'airline_iata_code', 'flight_number', 
              'origin_airport_iata_code', 'destination_airport_iata_code', 
              'departure_date', 'departure_time']


@admin.register(AirSegment)
class AirSegmentAdmin(admin.ModelAdmin):
    list_display = ['air_booking', 'segment_number', 'airline_iata_code', 'flight_number',
                    'origin_airport_iata_code', 'destination_airport_iata_code', 'departure_date']
    list_filter = ['airline_iata_code', 'departure_date']
    search_fields = ['air_booking__booking__booking_reference', 'flight_number', 
                    'origin_airport_iata_code', 'destination_airport_iata_code']
    
    fieldsets = (
        ('Segment Info', {
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
        ('Fare Details', {
            'fields': ('booking_class', 'fare_basis', 'distance_km'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AccommodationBooking)
class AccommodationBookingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'hotel_name', 'hotel_chain_ref', 'city', 'check_in_date', 
                    'check_out_date', 'number_of_nights', 'nightly_rate']
    list_filter = ['hotel_chain_ref', 'city', 'country', 'check_in_date']  # Updated to use ref
    search_fields = ['booking__booking_reference', 'hotel_name', 'city', 'hotel_chain',
                    'hotel_chain_ref__name']  # Added ref search
    date_hierarchy = 'check_in_date'
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Hotel Details', {
            'fields': ('hotel_name', 'hotel_chain', 'hotel_chain_ref')  # Added hotel_chain_ref
        }),
        ('Location', {
            'fields': ('city', 'country', 'address')
        }),
        ('Stay Details', {
            'fields': ('check_in_date', 'check_out_date', 'number_of_nights', 'room_type')
        }),
        ('Rates', {
            'fields': ('nightly_rate', 'currency', 'nightly_rate_base', 'total_amount_base')
        }),
    )
    
    # Make it easy to filter by preferred suppliers
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('booking', 'hotel_chain_ref')


@admin.register(CarHireBooking)
class CarHireBookingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'rental_company_ref', 'vehicle_type', 'pickup_city',
                    'pickup_date', 'number_of_days', 'daily_rate']
    list_filter = ['rental_company_ref', 'pickup_city', 'pickup_date']  # Updated to use ref
    search_fields = ['booking__booking_reference', 'rental_company', 'vehicle_type', 'pickup_city',
                    'rental_company_ref__name']  # Added ref search
    date_hierarchy = 'pickup_date'
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Rental Company', {
            'fields': ('rental_company', 'rental_company_ref')  # Added rental_company_ref
        }),
        ('Vehicle', {
            'fields': ('vehicle_type', 'vehicle_class')
        }),
        ('Locations', {
            'fields': ('pickup_location', 'dropoff_location', 'pickup_city')
        }),
        ('Rental Period', {
            'fields': ('pickup_date', 'pickup_time', 'dropoff_date', 'dropoff_time', 'number_of_days')
        }),
        ('Rates', {
            'fields': ('daily_rate', 'currency', 'daily_rate_base', 'total_amount_base')
        }),
    )
    
    # Make it easy to filter by preferred suppliers
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('booking', 'rental_company_ref')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'organization', 'booking', 'invoice_date',
                    'invoice_amount', 'currency', 'payment_status']
    list_filter = ['payment_status', 'currency', 'organization', 'invoice_date']
    search_fields = ['invoice_number', 'organization__name', 'booking__booking_reference']
    date_hierarchy = 'invoice_date'
    
    fieldsets = (
        ('Invoice Details', {
            'fields': ('invoice_number', 'invoice_date', 'organization', 'booking')
        }),
        ('Amounts', {
            'fields': ('currency', 'invoice_amount', 'gst_amount')
        }),
        ('Converted Amounts', {
            'fields': ('invoice_amount_base', 'gst_amount_base', 'exchange_rate', 'exchange_rate_date'),
            'classes': ('collapse',)
        }),
        ('Payment', {
            'fields': ('payment_status', 'payment_date')
        }),
        ('Import Tracking', {
            'fields': ('import_batch',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ServiceFee)
class ServiceFeeAdmin(admin.ModelAdmin):
    list_display = ['fee_type', 'organization', 'traveller', 'fee_date', 
                    'amount', 'currency']
    list_filter = ['fee_type', 'currency', 'organization', 'fee_date']
    search_fields = ['organization__name', 'traveller__first_name', 'traveller__last_name',
                    'description', 'booking__booking_reference']
    date_hierarchy = 'fee_date'
    
    fieldsets = (
        ('Fee Details', {
            'fields': ('fee_type', 'fee_date', 'organization', 'traveller', 'booking')
        }),
        ('Amount', {
            'fields': ('currency', 'amount', 'gst_amount')
        }),
        ('Converted Amounts', {
            'fields': ('amount_base', 'gst_amount_base', 'exchange_rate', 'exchange_rate_date'),
            'classes': ('collapse',)
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Import Tracking', {
            'fields': ('import_batch',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']