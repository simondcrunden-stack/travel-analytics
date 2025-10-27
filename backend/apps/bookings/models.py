# apps/bookings/models.py
# CORRECTED MODEL - Session 26

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
    """
    Main booking/transaction record - represents a single travel agent booking
    Can contain multiple air bookings, hotels, car rentals, etc.
    
    IMPORTANT CHANGE (Session 26):
    - Removed 'booking_type' field - one booking can have multiple types
    - Changed relationships to ForeignKey (one-to-many) instead of OneToOneField
    - total_amount is now sum of ALL components
    """
    
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
    
    # Booking reference - MASTER REFERENCE
    agent_booking_reference = models.CharField(
        max_length=100, 
        verbose_name="Agent Booking Reference",
        help_text="Master booking reference (e.g., GPT001)"
    )
    supplier_reference = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Supplier Reference",
        help_text="Optional supplier confirmation number"
    )
    
    # REMOVED: booking_type field (no longer needed)
    # One booking can contain multiple air, hotel, car components
    
    # Dates
    booking_date = models.DateField()
    travel_date = models.DateField(help_text="Start date of travel")
    return_date = models.DateField(null=True, blank=True, help_text="End date of travel")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    
    # Financial - TOTAL AMOUNTS (sum of all components)
    currency = models.CharField(max_length=3, default='AUD')
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Total amount in original currency (sum of all air, hotel, car, fees)"
    )
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Converted amounts (for multi-currency reporting)
    total_amount_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    base_fare_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taxes_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fees_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Currency conversion tracking
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    exchange_rate_date = models.DateField(null=True, blank=True)
    
    # Compliance
    policy_compliant = models.BooleanField(default=True)
    advance_booking_days = models.IntegerField(null=True, blank=True)
    
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
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.agent_booking_reference} - {self.traveller}"
    
    def calculate_total_amount(self):
        """
        Calculate total amount from all booking components
        Returns: Decimal total amount
        """
        total = Decimal('0.00')
        
        # Sum all air bookings
        for air in self.air_bookings.all():
            if air.total_fare:
                total += air.total_fare
        
        # Sum all accommodation bookings
        for hotel in self.accommodation_bookings.all():
            if hotel.total_amount_base:
                total += hotel.total_amount_base
        
        # Sum all car hire bookings
        for car in self.car_hire_bookings.all():
            if car.total_amount_base:
                total += car.total_amount_base
        
        # Sum all service fees
        for fee in self.service_fees.all():
            if fee.fee_amount:
                total += fee.fee_amount
        
        return total


# ============================================================================
# AIR BOOKING MODELS
# ============================================================================

class AirBooking(models.Model):
    """
    Extended details for air bookings
    
    IMPORTANT CHANGE (Session 26):
    - Changed from OneToOneField to ForeignKey
    - One Booking can have MULTIPLE AirBookings
    - Each AirBooking represents a ticketed itinerary
    """
    
    TRIP_TYPES = [
        ('ONE_WAY', 'One Way'),
        ('RETURN', 'Return'),
        ('MULTI_CITY', 'Multi-City'),
    ]
    
    TRAVEL_CLASSES = [
        ('ECONOMY', 'Economy'),
        ('PREMIUM_ECONOMY', 'Premium Economy'),
        ('BUSINESS', 'Business'),
        ('FIRST', 'First Class'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # CHANGED: ForeignKey instead of OneToOneField
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='air_bookings',  # Changed from 'air_details'
        help_text="Parent booking - one booking can have multiple air bookings"
    )
    
    # Flight details
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPES)
    travel_class = models.CharField(max_length=20, choices=TRAVEL_CLASSES)
    
    # Route (from first segment)
    origin_airport_iata_code = models.CharField(max_length=3)
    destination_airport_iata_code = models.CharField(max_length=3)
    
    # Ticketing
    ticket_number = models.CharField(max_length=50, blank=True)
    
    # Primary airline (from first segment or most segments)
    primary_airline_iata_code = models.CharField(max_length=3)
    primary_airline_name = models.CharField(max_length=100)
    
    # Compliance tracking
    lowest_fare_available = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lowest_fare_currency = models.CharField(max_length=3, blank=True)
    potential_savings = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Financial (optional - can calculate from segments)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'air_bookings'
        indexes = [
            models.Index(fields=['booking']),
            models.Index(fields=['origin_airport_iata_code', 'destination_airport_iata_code']),
            models.Index(fields=['primary_airline_iata_code']),
        ]
    
    def __str__(self):
        return f"{self.booking.agent_booking_reference} - {self.origin_airport_iata_code}→{self.destination_airport_iata_code}"
    
    def calculate_carbon_emissions(self):
        """Sum carbon emissions from all segments"""
        total_emissions = sum(
            segment.carbon_emissions_kg or 0 
            for segment in self.segments.all()
        )
        return total_emissions


class AirSegment(models.Model):
    """
    Individual flight segments within an air booking
    Relationship: Booking → AirBooking (many) → AirSegment (many)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    air_booking = models.ForeignKey(AirBooking, on_delete=models.CASCADE, related_name='segments')
    
    # Segment number (for ordering)
    segment_number = models.IntegerField()
    
    # Airline
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
    booking_class = models.CharField(max_length=10)  # Y, J, etc.
    fare_basis = models.CharField(max_length=20, blank=True)
    
    # Distance & carbon (auto-calculated)
    distance_km = models.IntegerField(null=True, blank=True)
    carbon_emissions_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'air_segments'
        indexes = [
            models.Index(fields=['air_booking', 'segment_number']),
            models.Index(fields=['origin_airport_iata_code', 'destination_airport_iata_code']),
            models.Index(fields=['departure_date']),
        ]
        ordering = ['segment_number']
    
    def __str__(self):
        return f"Segment {self.segment_number}: {self.origin_airport_iata_code}→{self.destination_airport_iata_code}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate distance and carbon emissions on save"""
        if not self.distance_km:
            self.distance_km = self.calculate_distance()
        
        if self.distance_km and not self.carbon_emissions_kg:
            self.carbon_emissions_kg = self.calculate_carbon_emissions()
        
        super().save(*args, **kwargs)
    
    def calculate_distance(self):
        """Calculate distance between airports using Haversine formula"""
        try:
            from math import radians, sin, cos, sqrt, atan2
            from apps.reference_data.models import Airport
            
            origin_airport = Airport.objects.get(iata_code=self.origin_airport_iata_code)
            dest_airport = Airport.objects.get(iata_code=self.destination_airport_iata_code)
            
            if not all([origin_airport.latitude, origin_airport.longitude,
                       dest_airport.latitude, dest_airport.longitude]):
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
            return None
    
    def calculate_carbon_emissions(self):
        """Calculate CO2 emissions based on ICAO standards"""
        if not self.distance_km:
            return None
        
        try:
            # ICAO emission factors (kg CO2 per passenger per km)
            if self.distance_km < 1000:
                # Short haul
                emission_factor = 0.254
            elif self.distance_km < 3500:
                # Medium haul
                emission_factor = 0.195
            else:
                # Long haul
                emission_factor = 0.152
            
            # Adjust for travel class
            class_multipliers = {
                'Y': 1.0,      # Economy baseline
                'W': 1.5,      # Premium Economy
                'J': 2.0,      # Business
                'F': 3.0,      # First
            }
            
            multiplier = class_multipliers.get(self.booking_class, 1.0)
            emissions = self.distance_km * emission_factor * multiplier
            
            return round(emissions, 2)
        except Exception as e:
            print(f"Error calculating carbon emissions: {e}")
            return None


# ============================================================================
# ACCOMMODATION MODELS
# ============================================================================

class AccommodationBooking(models.Model):
    """
    Extended details for hotel bookings
    
    IMPORTANT CHANGE (Session 26):
    - Changed from OneToOneField to ForeignKey
    - One Booking can have MULTIPLE AccommodationBookings
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # CHANGED: ForeignKey instead of OneToOneField
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='accommodation_bookings',  # Changed from 'accommodation_details'
        help_text="Parent booking - one booking can have multiple hotel stays"
    )
    
    # Hotel details
    hotel_name = models.CharField(max_length=200)
    hotel_chain = models.CharField(max_length=100, blank=True)
    
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
            models.Index(fields=['booking']),
            models.Index(fields=['city', 'check_in_date']),
            models.Index(fields=['hotel_chain']),
        ]
    
    def __str__(self):
        return f"{self.booking.agent_booking_reference} - {self.hotel_name}"


# ============================================================================
# CAR HIRE MODELS
# ============================================================================

class CarHireBooking(models.Model):
    """
    Extended details for car rental bookings
    
    IMPORTANT CHANGE (Session 26):
    - Changed from OneToOneField to ForeignKey
    - One Booking can have MULTIPLE CarHireBookings
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # CHANGED: ForeignKey instead of OneToOneField
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='car_hire_bookings',  # Changed from 'car_hire_details'
        help_text="Parent booking - one booking can have multiple car rentals"
    )
    
    # Rental company
    rental_company = models.CharField(max_length=100)
    
    # Vehicle
    vehicle_type = models.CharField(max_length=100, blank=True)  # Compact, SUV, etc.
    vehicle_category = models.CharField(max_length=100, blank=True)  # Economy, Full-size, etc.
    vehicle_make_model = models.CharField(max_length=100, blank=True)  # Toyota Corolla or similar
    
    # Pickup
    pickup_location = models.CharField(max_length=200)
    pickup_city = models.CharField(max_length=100)
    pickup_date = models.DateField()
    pickup_time = models.TimeField()
    
    # Dropoff
    dropoff_location = models.CharField(max_length=200)
    dropoff_city = models.CharField(max_length=100)
    dropoff_date = models.DateField()
    dropoff_time = models.TimeField()
    
    # Country
    country = models.CharField(max_length=100)
    
    # Duration & rate
    number_of_days = models.IntegerField()
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='AUD')
    
    # Converted to base currency
    daily_rate_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'car_hire_bookings'
        indexes = [
            models.Index(fields=['booking']),
            models.Index(fields=['pickup_city', 'pickup_date']),
            models.Index(fields=['rental_company']),
        ]
    
    def __str__(self):
        return f"{self.booking.agent_booking_reference} - {self.rental_company}"


# ============================================================================
# INVOICE & SERVICE FEE MODELS
# ============================================================================

class Invoice(models.Model):
    """Invoices issued by travel agents to customer organizations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, 
                                     related_name='invoices')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='invoices', 
                                null=True, blank=True)
    
    # Invoice details
    invoice_number = models.CharField(max_length=100)
    invoice_date = models.DateField()
    due_date = models.DateField()
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='AUD')
    
    # Payment
    payment_status = models.CharField(max_length=20, default='UNPAID')
    payment_date = models.DateField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
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
    fee_type = models.CharField(max_length=30, choices=FEE_TYPES)
    fee_date = models.DateField()
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='AUD')
    
    # Channel
    booking_channel = models.CharField(max_length=20, blank=True)  # Online, Offline, Mobile
    
    # Import tracking
    import_batch = models.ForeignKey('imports.ImportBatch', on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='service_fees')
    
    # Metadata
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_fees'
        indexes = [
            models.Index(fields=['organization', 'fee_date']),
            models.Index(fields=['booking']),
            models.Index(fields=['fee_type']),
        ]
    
    def __str__(self):
        return f"{self.get_fee_type_display()} - {self.organization.code} - ${self.fee_amount}"