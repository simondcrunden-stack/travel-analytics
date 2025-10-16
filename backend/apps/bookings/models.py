from apps.users.models import User
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Traveller(models.Model):
    """Individual travellers within customer organizations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='travellers'
    )
    
    # Personal info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    
    # Link to user account (if traveller has login access)
    user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='traveller_profile',
        verbose_name="User Account",
        help_text="Link this traveller to a user account if they need platform access"
    )
    employee_id = models.CharField(max_length=100, blank=True)
    
    # Department/cost center for reporting
    department = models.CharField(max_length=100, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'travellers'
        indexes = [
            models.Index(fields=['organization', 'last_name', 'first_name']),
            models.Index(fields=['organization', 'is_active']),
        ]
        unique_together = [['organization', 'employee_id']]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Booking(models.Model):
    """Main booking/transaction record"""
    BOOKING_TYPES = [
        ('AIR', 'Air Travel'),
        ('HOTEL', 'Accommodation'),
        ('CAR', 'Car Hire'),
        ('OTHER', 'Other Services'),
    ]
    
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
        ('PENDING', 'Pending'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    traveller = models.ForeignKey(
        Traveller,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # Booking workflow tracking
    travel_arranger = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings_arranged',
        verbose_name="Travel Arranger",
        help_text="Person within the organization who arranged this booking"
    )
    travel_arranger_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Travel Arranger (Text)",
        help_text="Fallback when arranger cannot be matched to a user account"
    )

    travel_consultant = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings_consulted',
        verbose_name="Travel Agent Consultant",
        help_text="Travel agent staff member who processed this booking"
    )
    travel_consultant_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Travel Consultant (Text)",
        help_text="Fallback when consultant cannot be matched to a user account"
    )
    
    # Booking reference
    agent_booking_reference = models.CharField(max_length=100, verbose_name="Agent Booking Reference")
    supplier_reference = models.CharField(max_length=100, blank=True, verbose_name="Supplier Reference")
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPES)
    
    # Dates
    booking_date = models.DateField()
    travel_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    
    # Financial
    currency = models.CharField(max_length=3, default='AUD')
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bookings'
        indexes = [
            models.Index(fields=['organization', 'booking_date']),
            models.Index(fields=['organization', 'travel_date']),
            models.Index(fields=['traveller', 'travel_date']),
            models.Index(fields=['agent_booking_reference']),
            models.Index(fields=['supplier_reference']),
            models.Index(fields=['booking_type', 'status']),
        ]
    
    def __str__(self):
        # Show booking reference and travel agent organization
        if self.organization.travel_agent:
            # If this is a customer org, show their travel agent
            agent_org = self.organization.travel_agent.name
        elif self.organization.org_type == 'AGENT':
            # If this IS the travel agent org
            agent_org = self.organization.name
        else:
            agent_org = "No Agent"
        
        return f"{self.agent_booking_reference} - {agent_org}"


# ============================================================================
# AIR TRAVEL SPECIFIC MODELS
# ============================================================================

class AirBooking(models.Model):
    """Extended details for air bookings"""
    TRAVEL_CLASS = [
        ('FIRST', 'First Class'),
        ('BUSINESS', 'Business Class'),
        ('PREMIUM_ECONOMY', 'Premium Economy'),
        ('ECONOMY', 'Economy'),
        ('RESTRICTED_ECONOMY', 'Restricted Economy'),
    ]
    
    TRIP_TYPE = [
        ('ONE_WAY', 'One Way'),
        ('RETURN', 'Return'),
        ('MULTI_CITY', 'Multi-City'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='air_details')
    
    # Flight details
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE)
    travel_class = models.CharField(max_length=30, choices=TRAVEL_CLASS)
    
    # Ticket
    ticket_number = models.CharField(max_length=50, blank=True)
    
    # Primary airline (for multi-segment bookings)
    primary_airline_iata_code = models.CharField(max_length=3, blank=True)
    primary_airline_name = models.CharField(max_length=100, blank=True)
    
    # Route (summary)
    origin_airport_iata_code = models.CharField(max_length=3)  # Airport IATA code
    destination_airport_iata_code = models.CharField(max_length=3)  # Airport IATA code
    
    # Compliance
    lowest_fare_available = models.DecimalField(max_digits=10, decimal_places=2, 
                                                null=True, blank=True)
    lowest_fare_currency = models.CharField(max_length=3, blank=True)
    
    # Savings/lost savings calculation
    potential_savings = models.DecimalField(max_digits=10, decimal_places=2, 
                                           null=True, blank=True)
    
    class Meta:
        db_table = 'air_bookings'
        indexes = [
            models.Index(fields=['origin_airport_iata_code', 'destination_airport_iata_code']),
            models.Index(fields=['primary_airline_iata_code']),
        ]
    
    def __str__(self):
        return f"{self.booking.agent_booking_reference} - {self.origin_airport_iata_code} to {self.destination_airport_iata_code}"


class AirSegment(models.Model):
    """Individual flight segments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    air_booking = models.ForeignKey(AirBooking, on_delete=models.CASCADE, related_name='segments')
    
    # Segment order
    segment_number = models.IntegerField()  # 1, 2, 3, etc.
    
    # Flight details
    airline_iata_code = models.CharField(max_length=3)  # QF, VA, etc.
    airline_name = models.CharField(max_length=100)
    flight_number = models.CharField(max_length=10)
    
    # Route
    origin_airport_iata_code = models.CharField(max_length=3)  # Airport IATA code
    destination_airport_iata_code = models.CharField(max_length=3)  # Airport IATA code
    
    # Times
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_date = models.DateField()
    arrival_time = models.TimeField()
    
    # Class & fare
    booking_class = models.CharField(max_length=10)  # Y, J, etc.
    fare_basis = models.CharField(max_length=20, blank=True)
    
    # Distance
    distance_km = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'air_segments'
        indexes = [
            models.Index(fields=['air_booking', 'segment_number']),
            models.Index(fields=['origin_airport_iata_code', 'destination_airport_iata_code']),
            models.Index(fields=['departure_date']),
        ]
        ordering = ['segment_number']
    
    def __str__(self):
        return f"Segment {self.segment_number}: {self.airline_iata_code}{self.flight_number} {self.origin_airport_iata_code}-{self.destination_airport_iata_code}"


# ============================================================================
# ACCOMMODATION MODELS
# ============================================================================

class AccommodationBooking(models.Model):
    """Extended details for hotel bookings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='accommodation_details')
    
    # Hotel details - HYBRID APPROACH
    hotel_name = models.CharField(max_length=200)
    hotel_chain = models.CharField(max_length=100, blank=True)  # Text fallback
    
    # Location
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    
    # Stay details
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_nights = models.IntegerField()
    room_type = models.CharField(max_length=100, blank=True)
    
    # Rate
    nightly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='AUD')
    
    # Converted to base currency
    nightly_rate_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'accommodation_bookings'
        indexes = [
            models.Index(fields=['city', 'check_in_date']),
            models.Index(fields=['hotel_chain']),
        ]
    
    def __str__(self):
        return f"{self.booking.agent_booking_reference} - {self.hotel_name}"


# ============================================================================
# CAR HIRE MODELS
# ============================================================================

class CarHireBooking(models.Model):
    """Extended details for car rental bookings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='car_hire_details')
    
    # Rental company - HYBRID APPROACH
    rental_company = models.CharField(max_length=100)  # Text fallback
    
    # Vehicle
    vehicle_type = models.CharField(max_length=100, blank=True)  # Compact, SUV, etc.
    vehicle_class = models.CharField(max_length=50, blank=True)
    
    # Location
    pickup_location = models.CharField(max_length=200)
    dropoff_location = models.CharField(max_length=200)
    pickup_city = models.CharField(max_length=100)
    
    # Rental period
    pickup_date = models.DateField()
    pickup_time = models.TimeField()
    dropoff_date = models.DateField()
    dropoff_time = models.TimeField()
    number_of_days = models.IntegerField()
    
    # Rate
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='AUD')
    
    # Converted to base currency
    daily_rate_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'car_hire_bookings'
        indexes = [
            models.Index(fields=['pickup_city', 'pickup_date']),
            models.Index(fields=['rental_company']),
        ]
    
    def __str__(self):
        return f"{self.booking.agent_booking_reference} - {self.rental_company}"


# ============================================================================
# INVOICE & SERVICE FEE MODELS
# ============================================================================

class Invoice(models.Model):
    """Invoice records - when tickets/services are issued"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='invoices')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, 
                                     related_name='invoices')
    
    # Invoice details
    invoice_number = models.CharField(max_length=100)
    invoice_date = models.DateField()
    
    # Amounts
    currency = models.CharField(max_length=3, default='AUD')  # Original invoice currency
    invoice_amount = models.DecimalField(max_digits=10, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Converted amounts in organization's base currency
    invoice_amount_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gst_amount_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Exchange rate used for conversion
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    exchange_rate_date = models.DateField(null=True, blank=True)
    
    # Payment
    payment_status = models.CharField(max_length=20, default='UNPAID')
    payment_date = models.DateField(null=True, blank=True)
    
    # Import tracking
    import_batch = models.ForeignKey('imports.ImportBatch', on_delete=models.SET_NULL, null=True,
                                     related_name='invoices')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        indexes = [
            models.Index(fields=['organization', 'invoice_date']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['booking']),
        ]
        unique_together = [['organization', 'invoice_number']]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.organization.code}"


class ServiceFee(models.Model):
    """Service fees charged by travel agents"""
    FEE_TYPES = [
        ('BOOKING_ONLINE_DOM', 'Online Booking - Domestic'),
        ('BOOKING_ONLINE_INTL', 'Online Booking - International'),
        ('BOOKING_OFFLINE_DOM', 'Offline Booking - Domestic'),
        ('BOOKING_OFFLINE_INTL', 'Offline Booking - International'),
        ('CHANGE_FEE', 'Change Fee'),
        ('REFUND_FEE', 'Refund Fee'),
        ('AFTER_HOURS', 'After Hours Fee'),
        ('CONSULTATION', 'Consultation Fee'),
        ('OTHER', 'Other Fee'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='service_fees', 
                                null=True, blank=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, 
                                     related_name='service_fees')
    traveller = models.ForeignKey(Traveller, on_delete=models.CASCADE, related_name='service_fees', 
                                  null=True, blank=True)
    
    # Fee details
    fee_type = models.CharField(max_length=50, choices=FEE_TYPES)
    fee_date = models.DateField()
    
    # Amount
    currency = models.CharField(max_length=3, default='AUD')  # Original fee currency
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Converted amounts in organization's base currency
    amount_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gst_amount_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Exchange rate used for conversion
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    exchange_rate_date = models.DateField(null=True, blank=True)
    
    # Description
    description = models.TextField(blank=True)
    
    # Import tracking
    import_batch = models.ForeignKey('imports.ImportBatch', on_delete=models.SET_NULL, null=True,
                                     related_name='service_fees')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_fees'
        indexes = [
            models.Index(fields=['organization', 'fee_date']),
            models.Index(fields=['fee_type', 'fee_date']),
        ]
    
    def __str__(self):
        return f"{self.fee_type} - {self.amount} {self.currency}"