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
    
    # Converted amounts in organization's base currency
    total_amount_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    base_fare_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taxes_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fees_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Exchange rate used for conversion
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    exchange_rate_date = models.DateField(null=True, blank=True)
    
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    air_booking = models.ForeignKey(AirBooking, on_delete=models.CASCADE, related_name='segments')
    
    # Segment order
    segment_number = models.IntegerField()
    
    # Flight details
    airline_iata_code = models.CharField(max_length=3)
    airline_name = models.CharField(max_length=100)
    flight_number = models.CharField(max_length=10)
    
    # Route
    origin_airport_iata_code = models.CharField(max_length=3)
    destination_airport_iata_code = models.CharField(max_length=3)
    
    # Times
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_date = models.DateField()
    arrival_time = models.TimeField()
    
    # Class & fare
    booking_class = models.CharField(max_length=10)
    fare_basis = models.CharField(max_length=20, blank=True)
    
    # Distance & Carbon
    distance_km = models.IntegerField(null=True, blank=True)
    carbon_emissions_kg = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="CO2 emissions in kilograms for this segment (ICAO standards)"
    )
    
    class Meta:
        db_table = 'air_segments'
        indexes = [
            models.Index(fields=['air_booking', 'segment_number']),
            models.Index(fields=['origin_airport_iata_code', 'destination_airport_iata_code']),
            models.Index(fields=['departure_date']),
        ]
        ordering = ['segment_number']
    
    def calculate_distance(self):
        """
        Calculate great circle distance between origin and destination airports.
        Returns distance in kilometers.
        """
        try:
            from math import radians, sin, cos, sqrt, atan2
            from apps.reference_data.models import Airport
            
            origin_airport = Airport.objects.get(iata_code=self.origin_airport_iata_code)
            dest_airport = Airport.objects.get(iata_code=self.destination_airport_iata_code)
            
            if not all([origin_airport.latitude, origin_airport.longitude,
                       dest_airport.latitude, dest_airport.longitude]):
                print(f"Missing coordinates for {self.origin_airport_iata_code} or {self.destination_airport_iata_code}")
                return None
            
            # Haversine formula
            R = 6371  # Earth's radius in km
            
            lat1 = radians(float(origin_airport.latitude))
            lon1 = radians(float(origin_airport.longitude))
            lat2 = radians(float(dest_airport.latitude))
            lon2 = radians(float(dest_airport.longitude))
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            return round(distance)
        except Exception as e:
            print(f"Error calculating distance: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def calculate_carbon_emissions(self):
        """
        Calculate CO2 emissions based on ICAO standards.
        
        ICAO Carbon Emissions Calculator methodology:
        - Short-haul (<1000km): ~0.158 kg CO2/km
        - Medium-haul (1000-3000km): ~0.113 kg CO2/km  
        - Long-haul (>3000km): ~0.103 kg CO2/km
        
        Class multipliers (per passenger):
        - Economy: 1.0x
        - Premium Economy: 1.5x
        - Business: 2.0x
        - First: 2.5x
        """
        if not self.distance_km:
            distance = self.calculate_distance()
            if distance:
                self.distance_km = distance
            else:
                return None
        
        # Determine emission factor based on distance
        if self.distance_km < 1000:
            base_emission_factor = 0.158  # kg CO2 per km
        elif self.distance_km < 3000:
            base_emission_factor = 0.113
        else:
            base_emission_factor = 0.103
        
        # Get class multiplier from booking class
        class_multiplier = 1.0  # Default to economy
        try:
            air_booking = self.air_booking
            if air_booking.travel_class in ['BUSINESS', 'PREMIUM_BUSINESS']:
                class_multiplier = 2.0
            elif air_booking.travel_class == 'FIRST':
                class_multiplier = 2.5
            elif air_booking.travel_class == 'PREMIUM_ECONOMY':
                class_multiplier = 1.5
        except Exception:
            pass
        
        # Calculate total emissions
        emissions = self.distance_km * base_emission_factor * class_multiplier
        
        return round(emissions, 2)
    
    def save(self, *args, **kwargs):
        """Auto-calculate distance and emissions on save if not provided"""
        # Calculate distance if missing
        if not self.distance_km:
            calculated_distance = self.calculate_distance()
            if calculated_distance:
                self.distance_km = calculated_distance
        
        # Calculate carbon if we have distance
        if self.distance_km and not self.carbon_emissions_kg:
            calculated_carbon = self.calculate_carbon_emissions()
            if calculated_carbon:
                self.carbon_emissions_kg = calculated_carbon
        
        super().save(*args, **kwargs)


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