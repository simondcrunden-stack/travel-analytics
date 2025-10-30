# apps/bookings/models.py
# CORRECTED MODEL - Session 26 + Session 34 (Phase 1 enhancements)

from apps.users.models import User
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger(__name__)


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
# AIR TRAVEL SPECIFIC MODELS
# ============================================================================

class AirBooking(models.Model):
    """
    Extended details for air bookings
    
    IMPORTANT CHANGES:
    - Session 26: Changed from OneToOneField to ForeignKey
    - Session 34: Added automatic carbon and savings calculations
    """
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
    
    # CHANGED: ForeignKey instead of OneToOneField
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='air_bookings',  # Changed from 'air_details'
        help_text="Parent booking - one booking can have multiple air bookings"
    )
    
    # Flight details
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE)
    travel_class = models.CharField(max_length=30, choices=TRAVEL_CLASS)
    
    # Ticket
    ticket_number = models.CharField(max_length=50, blank=True)
    
    # Primary airline (for multi-segment bookings)
    primary_airline_iata_code = models.CharField(max_length=3, blank=True)
    primary_airline_name = models.CharField(max_length=100, blank=True)
    
    # Route (summary - from first segment origin to last segment destination)
    origin_airport_iata_code = models.CharField(max_length=3)
    destination_airport_iata_code = models.CharField(max_length=3)
    
    # Fare breakdown
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='AUD')
    
    # Carbon emissions (total from all segments)
    total_carbon_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total CO2 emissions in kg (sum of all segments)"
    )
    
    # Compliance
    lowest_fare_available = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    lowest_fare_currency = models.CharField(max_length=3, blank=True)
    
    # Savings/lost savings calculation
    potential_savings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount that could have been saved if lowest fare was used"
    )
    
    class Meta:
        db_table = 'air_bookings'
        indexes = [
            models.Index(fields=['booking']),
            models.Index(fields=['origin_airport_iata_code', 'destination_airport_iata_code']),
            models.Index(fields=['primary_airline_iata_code']),
        ]
    
    def __str__(self):
        return f"{self.booking.agent_booking_reference} - {self.origin_airport_iata_code} to {self.destination_airport_iata_code}"

    # ==================================================================
    # SESSION 34 ENHANCEMENTS: Automatic Calculations
    # ==================================================================
    
    def calculate_total_carbon(self):
        """
        Sum carbon emissions from all segments
        
        Returns:
            Decimal: Total carbon in kg CO2
        """
        total = Decimal('0.00')
        
        # Sum from all segments
        for segment in self.segments.all():
            if segment.carbon_emissions_kg:
                total += Decimal(str(segment.carbon_emissions_kg))
        
        return round(total, 2)
    
    def calculate_potential_savings(self):
        """
        Calculate potential savings if lowest fare was used instead
        
        Returns:
            Decimal: Savings amount in base currency, or None if can't calculate
        """
        if not self.lowest_fare_available or not self.booking.base_fare:
            return None
        
        try:
            from apps.reference_data.models import CurrencyExchangeRate
            
            # Convert lowest fare to booking currency if needed
            if self.lowest_fare_currency != self.booking.currency:
                rate = CurrencyExchangeRate.get_rate(
                    from_currency=self.lowest_fare_currency,
                    to_currency=self.booking.currency,
                    date=self.booking.booking_date
                )
                if rate is None:
                    logger.warning(
                        f"No exchange rate found for {self.lowest_fare_currency} to "
                        f"{self.booking.currency} on {self.booking.booking_date}"
                    )
                    return None
                    
                lowest_in_booking_currency = Decimal(str(self.lowest_fare_available)) * Decimal(str(rate))
            else:
                lowest_in_booking_currency = Decimal(str(self.lowest_fare_available))
            
            # Calculate savings (only if positive)
            savings = Decimal(str(self.booking.base_fare)) - lowest_in_booking_currency
            
            logger.info(
                f"Savings calculation for {self.booking.agent_booking_reference}: "
                f"Base fare {self.booking.base_fare} - Lowest {lowest_in_booking_currency} = {savings}"
            )
            
            return max(savings, Decimal('0.00'))  # Only return positive savings
            
        except Exception as e:
            logger.error(f"Error calculating potential savings: {e}")
            return None
    
    def save(self, *args, **kwargs):
        """
        Enhanced save with automatic calculations
        
        Calculates:
        1. Total carbon from segments (if segments exist)
        2. Potential savings (if lowest fare available)
        """
        is_new = self.pk is None
        
        # Save first to ensure we have an ID for relationships
        super().save(*args, **kwargs)
        
        # Calculate total carbon from segments (only if not new, segments need to exist)
        if not is_new:
            try:
                calculated_carbon = self.calculate_total_carbon()
                if calculated_carbon and calculated_carbon != self.total_carbon_kg:
                    self.total_carbon_kg = calculated_carbon
                    # Use update to avoid recursion
                    AirBooking.objects.filter(pk=self.pk).update(
                        total_carbon_kg=calculated_carbon
                    )
                    logger.info(f"Updated carbon for {self.booking.agent_booking_reference}: {calculated_carbon} kg")
            except Exception as e:
                logger.error(f"Error calculating total carbon: {e}")
        
        # Calculate potential savings
        if self.lowest_fare_available:
            try:
                calculated_savings = self.calculate_potential_savings()
                if calculated_savings is not None and calculated_savings != self.potential_savings:
                    self.potential_savings = calculated_savings
                    # Use update to avoid recursion
                    AirBooking.objects.filter(pk=self.pk).update(
                        potential_savings=calculated_savings
                    )
                    logger.info(f"Updated savings for {self.booking.agent_booking_reference}: {calculated_savings}")
            except Exception as e:
                logger.error(f"Error calculating potential savings: {e}")


class AirSegment(models.Model):
    """Individual flight segments within an air booking"""
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
                logger.warning(f"Missing coordinates for {self.origin_airport_iata_code} or {self.destination_airport_iata_code}")
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
            logger.error(f"Error calculating distance: {e}")
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
    """
    Extended details for hotel bookings
    
    IMPORTANT CHANGES:
    - Session 26: Changed from OneToOneField to ForeignKey
    - Session 34: Added automatic currency conversion
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

    # ==================================================================
    # SESSION 34 ENHANCEMENTS: Automatic Currency Conversion
    # ==================================================================

    def convert_to_base_currency(self):
        """
        Convert nightly rate and total to organization's base currency
        
        Updates:
        - nightly_rate_base
        - total_amount_base
        """
        try:
            base_currency = self.booking.organization.base_currency
            
            # If already in base currency, just copy values
            if self.currency == base_currency:
                self.nightly_rate_base = self.nightly_rate
                self.total_amount_base = self.nightly_rate * self.number_of_nights
                logger.debug(f"Hotel {self.hotel_name} already in base currency {base_currency}")
                return
            
            # Get exchange rate
            from apps.reference_data.models import CurrencyExchangeRate
            
            rate = CurrencyExchangeRate.get_rate(
                from_currency=self.currency,
                to_currency=base_currency,
                date=self.check_in_date
            )
            
            if rate is None:
                logger.warning(
                    f"No exchange rate found for {self.currency} to {base_currency} "
                    f"on {self.check_in_date}. Using 1:1 fallback."
                )
                rate = Decimal('1.0')
            
            # Calculate converted amounts
            self.nightly_rate_base = round(Decimal(str(self.nightly_rate)) * Decimal(str(rate)), 2)
            self.total_amount_base = round(self.nightly_rate_base * self.number_of_nights, 2)
            
            logger.info(
                f"Converted hotel {self.hotel_name}: "
                f"{self.currency} {self.nightly_rate} → {base_currency} {self.nightly_rate_base} "
                f"(rate: {rate}, total: {self.total_amount_base})"
            )
            
        except Exception as e:
            logger.error(f"Error converting accommodation to base currency: {e}")
            # Set to None if conversion fails
            self.nightly_rate_base = None
            self.total_amount_base = None
    
    def save(self, *args, **kwargs):
        """
        Enhanced save with automatic currency conversion
        
        Converts nightly_rate to organization's base currency before saving
        """
        # Calculate base currency amounts
        self.convert_to_base_currency()
        
        # Save with converted values
        super().save(*args, **kwargs)


# ============================================================================
# CAR HIRE MODELS
# ============================================================================

class CarHireBooking(models.Model):
    """
    Extended details for car rental bookings
    
    IMPORTANT CHANGES:
    - Session 26: Changed from OneToOneField to ForeignKey
    - Session 34: Added automatic currency conversion
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
    country = models.CharField(max_length=100, blank=True, null=True)
    
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

    # ==================================================================
    # SESSION 34 ENHANCEMENTS: Automatic Currency Conversion
    # ==================================================================

    def convert_to_base_currency(self):
        """
        Convert daily rate and total to organization's base currency
        
        Updates:
        - daily_rate_base
        - total_amount_base
        """
        try:
            base_currency = self.booking.organization.base_currency
            
            # If already in base currency, just copy values
            if self.currency == base_currency:
                self.daily_rate_base = self.daily_rate
                self.total_amount_base = self.daily_rate * self.number_of_days
                logger.debug(f"Car hire {self.rental_company} already in base currency {base_currency}")
                return
            
            # Get exchange rate
            from apps.reference_data.models import CurrencyExchangeRate
            
            rate = CurrencyExchangeRate.get_rate(
                from_currency=self.currency,
                to_currency=base_currency,
                date=self.pickup_date
            )
            
            if rate is None:
                logger.warning(
                    f"No exchange rate found for {self.currency} to {base_currency} "
                    f"on {self.pickup_date}. Using 1:1 fallback."
                )
                rate = Decimal('1.0')
            
            # Calculate converted amounts
            self.daily_rate_base = round(Decimal(str(self.daily_rate)) * Decimal(str(rate)), 2)
            self.total_amount_base = round(self.daily_rate_base * self.number_of_days, 2)
            
            logger.info(
                f"Converted car hire {self.rental_company}: "
                f"{self.currency} {self.daily_rate} → {base_currency} {self.daily_rate_base} "
                f"(rate: {rate}, total: {self.total_amount_base})"
            )
            
        except Exception as e:
            logger.error(f"Error converting car hire to base currency: {e}")
            # Set to None if conversion fails
            self.daily_rate_base = None
            self.total_amount_base = None
    
    def save(self, *args, **kwargs):
        """
        Enhanced save with automatic currency conversion
        
        Converts daily_rate to organization's base currency before saving
        """
        # Calculate base currency amounts
        self.convert_to_base_currency()
        
        # Save with converted values
        super().save(*args, **kwargs)


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