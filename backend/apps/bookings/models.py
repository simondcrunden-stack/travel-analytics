# apps/bookings/models.py
# CORRECTED MODEL - Session 26 + Session 34 (Phase 1 enhancements)

from apps.users.models import User
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
import json
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
    cost_center = models.CharField(
        max_length=100,
        blank=True,
        help_text="DEPRECATED: Use organizational_node instead. Kept for backward compatibility."
    )

    # Organizational hierarchy (replaces cost_center)
    organizational_node = models.ForeignKey(
        'organizations.OrganizationalNode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='travellers',
        help_text="Link to organizational hierarchy node (cost center, business unit, etc.)"
    )

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
            models.Index(fields=['organizational_node']),
            models.Index(fields=['employee_id']),  # Add index for employee_id lookups
        ]
        # Removed unique_together constraint to allow duplicate employee_ids for data import
        # Duplicates can be merged using the Data Management merge functionality
    
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
        default=0,
        help_text="Total amount in original currency (auto-calculated from all components)"
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

        # Sum all other products
        for other in self.other_products.all():
            if other.amount_base:
                total += other.amount_base
            elif other.amount:
                total += other.amount

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
    base_fare = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    taxes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_fare = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='AUD')

    # Commission (from airline/supplier)
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Commission earned from airline/supplier"
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Commission percentage (e.g., 5.00 for 5%)"
    )
    commission_currency = models.CharField(
        max_length=3,
        default='AUD',
        help_text="Currency of commission (defaults to booking currency)"
    )

    # Carbon emissions (total from all segments)
    total_carbon_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total CO2 emissions in kg (sum of all segments)"
    )
    
    # Compliance
    lowest_fare_available = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    lowest_fare_currency = models.CharField(max_length=3, blank=True)
    
    # Savings/lost savings calculation
    potential_savings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
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
        if not self.lowest_fare_available or not self.total_fare:
            return None

        try:
            from apps.reference_data.models import CurrencyExchangeRate

            # Convert lowest fare to booking currency if needed
            if self.lowest_fare_currency != self.currency:
                rate = CurrencyExchangeRate.get_rate(
                    from_currency=self.lowest_fare_currency,
                    to_currency=self.currency,
                    date=self.booking.booking_date
                )
                if rate is None:
                    logger.warning(
                        f"No exchange rate found for {self.lowest_fare_currency} to "
                        f"{self.currency} on {self.booking.booking_date}"
                    )
                    return None

                lowest_in_booking_currency = Decimal(str(self.lowest_fare_available)) * Decimal(str(rate))
            else:
                lowest_in_booking_currency = Decimal(str(self.lowest_fare_available))

            # Calculate savings (total_fare - lowest_fare_available)
            savings = Decimal(str(self.total_fare)) - lowest_in_booking_currency

            logger.info(
                f"Savings calculation for {self.booking.agent_booking_reference}: "
                f"Total fare {self.total_fare} - Lowest {lowest_in_booking_currency} = {savings}"
            )

            return max(savings, Decimal('0.00'))  # Only return positive savings

        except Exception as e:
            logger.error(f"Error calculating potential savings: {e}")
            return None
    
    def save(self, *args, **kwargs):
        """
        Enhanced save with automatic calculations
        
        Calculates:
        1. total_fare from component fields (base_fare + taxes + gst_amount + fees)
        2. Total carbon from segments (if segments exist)
        3. Potential savings (if lowest fare available)
        """
        # Calculate total_fare from components
        self.total_fare = (
            Decimal(str(self.base_fare or 0)) +
            Decimal(str(self.taxes or 0)) +
            Decimal(str(self.gst_amount or 0)) +
            Decimal(str(self.fees or 0))
        )
        
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
        
        # ==================================================================
        # SESSION 45: Update parent Booking total_amount
        # ==================================================================
        try:
            # Recalculate parent booking's total from all components
            new_total = self.booking.calculate_total_amount()
            if new_total != self.booking.total_amount:
                Booking.objects.filter(pk=self.booking.pk).update(
                    total_amount=new_total
                )
                logger.info(f"Updated booking {self.booking.agent_booking_reference} total: {new_total}")
        except Exception as e:
            logger.error(f"Error updating booking total: {e}")


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
        default=0,
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
    
    # ========================================================================
    # PROPERTY METHODS FOR AIRPORT LOOKUPS
    # ========================================================================
    @property
    def origin_airport(self):
        """Get Airport object for origin - enables Airport.country lookups"""
        from apps.reference_data.models import Airport
        try:
            return Airport.objects.get(iata_code=self.origin_airport_iata_code)
        except Airport.DoesNotExist:
            logger.warning(f"Airport not found: {self.origin_airport_iata_code}")
            return None
    
    @property
    def destination_airport(self):
        """Get Airport object for destination - enables Airport.country lookups"""
        from apps.reference_data.models import Airport
        try:
            return Airport.objects.get(iata_code=self.destination_airport_iata_code)
        except Airport.DoesNotExist:
            logger.warning(f"Airport not found: {self.destination_airport_iata_code}")
            return None
    
    def calculate_distance(self):
        """
        Calculate great circle distance between origin and destination airports.
        Returns distance in kilometers.
        """
        try:
            from math import radians, sin, cos, sqrt, atan2
            
            # Use ForeignKey relationships directly
            origin_airport = self.origin_airport
            dest_airport = self.destination_airport
            
            if not all([origin_airport.latitude, origin_airport.longitude,
                       dest_airport.latitude, dest_airport.longitude]):
                logger.warning(f"Missing coordinates for {origin_airport.iata_code} or {dest_airport.iata_code}")
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
    - Session 43: Added Hotel FK for master data management
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # CHANGED: ForeignKey instead of OneToOneField
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='accommodation_bookings',  # Changed from 'accommodation_details'
        help_text="Parent booking - one booking can have multiple hotel stays"
    )

    # Hotel reference (master data)
    hotel = models.ForeignKey(
        'reference_data.Hotel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        help_text="Link to canonical hotel record (for master data management)"
    )

    # Hotel details (preserved for historical data and unmapped hotels)
    hotel_name = models.CharField(
        max_length=200,
        help_text="Original hotel name from booking (preserved for history)"
    )
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
    nightly_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='AUD')

    # Converted to base currency
    nightly_rate_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Commission (from hotel/supplier)
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Commission earned from hotel/supplier"
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Commission percentage (e.g., 10.00 for 10%)"
    )
    commission_currency = models.CharField(
        max_length=3,
        default='AUD',
        help_text="Currency of commission (defaults to booking currency)"
    )

    class Meta:
        db_table = 'accommodation_bookings'
        indexes = [
            models.Index(fields=['booking']),
            models.Index(fields=['hotel']),
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
        
        # ==================================================================
        # SESSION 45: Update parent Booking total_amount
        # ==================================================================
        try:
            # Recalculate parent booking's total from all components
            new_total = self.booking.calculate_total_amount()
            if new_total != self.booking.total_amount:
                Booking.objects.filter(pk=self.booking.pk).update(
                    total_amount=new_total
                )
                logger.info(f"Updated booking {self.booking.agent_booking_reference} total: {new_total}")
        except Exception as e:
            logger.error(f"Error updating booking total: {e}")


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
    daily_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='AUD')

    # Converted to base currency
    daily_rate_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Commission (from rental company/supplier)
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Commission earned from rental company/supplier"
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Commission percentage (e.g., 15.00 for 15%)"
    )
    commission_currency = models.CharField(
        max_length=3,
        default='AUD',
        help_text="Currency of commission (defaults to booking currency)"
    )

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
        
        # ==================================================================
        # SESSION 45: Update parent Booking total_amount
        # ==================================================================
        try:
            # Recalculate parent booking's total from all components
            new_total = self.booking.calculate_total_amount()
            if new_total != self.booking.total_amount:
                Booking.objects.filter(pk=self.booking.pk).update(
                    total_amount=new_total
                )
                logger.info(f"Updated booking {self.booking.agent_booking_reference} total: {new_total}")
        except Exception as e:
            logger.error(f"Error updating booking total: {e}")


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
    fee_date = models.DateField(verbose_name='Invoice Date')
    invoice_number = models.CharField(max_length=100, blank=True, verbose_name='Invoice Number')
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Fee Amount')
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='GST Amount')
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

    def save(self, *args, **kwargs):
        """Save and update parent booking total"""
        super().save(*args, **kwargs)

        # Update parent Booking total_amount
        if self.booking:
            try:
                new_total = self.booking.calculate_total_amount()
                if new_total != self.booking.total_amount:
                    Booking.objects.filter(pk=self.booking.pk).update(
                        total_amount=new_total
                    )
                    logger.info(f"Updated booking {self.booking.agent_booking_reference} total after service fee: {new_total}")
            except Exception as e:
                logger.error(f"Error updating booking total after service fee: {e}")

# ============================================================================
# PRODUCT TYPE MAPPING - For handling import variations
# ============================================================================

class ProductTypeMapping(models.Model):
    """
    Maps various source system product type names to canonical types.

    Handles naming variations during imports:
    - Air/Airfare/Flight → AirBooking
    - Accommodation/Hotel → AccommodationBooking
    - Insurance/Cruise/etc → OtherProduct

    This prevents import failures when encountering new or variant product type names.
    """

    # Canonical product types
    CANONICAL_TYPES = [
        ('BOOKING_AIR', 'Air Booking'),
        ('BOOKING_ACCOMMODATION', 'Accommodation Booking'),
        ('BOOKING_CAR_HIRE', 'Car Hire Booking'),
        ('BOOKING_SERVICE_FEE', 'Service Fee'),
        ('PRODUCT_MERCHANT_FEE', 'Merchant Fee'),
        ('PRODUCT_CRUISE', 'Cruise'),
        ('PRODUCT_PACKAGE', 'Package/Tour'),
        ('PRODUCT_INSURANCE', 'Insurance'),
        ('PRODUCT_VISA', 'Visa'),
        ('PRODUCT_TRANSFER', 'Transfer'),
        ('PRODUCT_BUS', 'Bus/Coach'),
        ('PRODUCT_TRAIN', 'Train/Rail'),
        ('PRODUCT_OTHER', 'Other/Miscellaneous'),
    ]

    # Target model classes
    TARGET_MODELS = [
        ('AirBooking', 'Air Booking Model'),
        ('AccommodationBooking', 'Accommodation Booking Model'),
        ('CarHireBooking', 'Car Hire Booking Model'),
        ('ServiceFee', 'Service Fee Model'),
        ('OtherProduct', 'Other Product Model'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Mapping fields
    source_name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Product type name as it appears in source data (e.g., 'Airfare', 'Hotel')"
    )
    canonical_type = models.CharField(
        max_length=50,
        choices=CANONICAL_TYPES,
        help_text="Standardized product type classification"
    )
    target_model = models.CharField(
        max_length=50,
        choices=TARGET_MODELS,
        help_text="Django model to create when this product type is imported"
    )

    # For OtherProduct, specify the product_type to use
    product_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="For OtherProduct target: specific product_type value to set"
    )
    product_subtype = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional subtype classification"
    )

    # Configuration
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive mappings are ignored during import"
    )
    auto_created = models.BooleanField(
        default=False,
        help_text="True if this mapping was auto-created during import"
    )

    # Metadata
    notes = models.TextField(blank=True, help_text="Admin notes about this mapping")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_type_mappings'
        verbose_name = 'Product Type Mapping'
        verbose_name_plural = 'Product Type Mappings'
        ordering = ['canonical_type', 'source_name']
        indexes = [
            models.Index(fields=['source_name', 'is_active']),
            models.Index(fields=['canonical_type']),
            models.Index(fields=['target_model']),
        ]

    def __str__(self):
        return f"{self.source_name} → {self.target_model} ({self.get_canonical_type_display()})"


# ============================================================================
# OTHER PRODUCT MODEL - Flexible catch-all for non-standard products
# ============================================================================

class OtherProduct(models.Model):
    """
    Flexible model for product types that don't have dedicated models.

    Used for:
    - Products discovered during import (Cruise, Insurance, etc.)
    - Products that will be migrated to specific models later
    - One-off or rare product types

    Uses JSON field for flexible attribute storage.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='other_products',
        help_text="Parent booking this product belongs to"
    )

    # Product classification
    product_type = models.CharField(
        max_length=50,
        help_text="Type of product (e.g., INSURANCE, CRUISE, VISA)"
    )
    product_subtype = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional subtype (e.g., TRAVEL_INSURANCE, OCEAN_CRUISE)"
    )

    # Core details
    supplier_name = models.CharField(max_length=200, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    # Financial
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total amount in original currency"
    )
    currency = models.CharField(max_length=3, default='AUD')
    amount_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount converted to base currency"
    )

    # Dates
    purchase_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Flexible details storage
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible storage for product-specific attributes"
    )

    # Import tracking
    import_batch = models.ForeignKey(
        'imports.ImportBatch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='other_products'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'other_products'
        verbose_name = 'Other Product'
        verbose_name_plural = 'Other Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', 'product_type']),
            models.Index(fields=['product_type', 'purchase_date']),
            models.Index(fields=['supplier_name']),
        ]

    def __str__(self):
        return f"{self.product_type} - {self.supplier_name or 'Unknown'} - ${self.amount}"

    def convert_to_base_currency(self):
        """Convert amount to base currency using exchange rates"""
        if self.currency == 'AUD':
            self.amount_base = self.amount
            return

        try:
            from apps.reference_data.models import CurrencyExchangeRate
            from decimal import Decimal

            # Get exchange rate
            rate = CurrencyExchangeRate.get_rate(
                from_currency=self.currency,
                to_currency='AUD',
                date=self.purchase_date or timezone.now().date()
            )

            if rate:
                self.amount_base = round(Decimal(str(self.amount)) * Decimal(str(rate)), 2)
            else:
                self.amount_base = None
        except Exception:
            self.amount_base = None

    def save(self, *args, **kwargs):
        """Auto-convert currency on save and update parent booking total"""
        if not self.amount_base or self.amount_base == 0:
            self.convert_to_base_currency()

        super().save(*args, **kwargs)

        # Update parent Booking total_amount
        try:
            new_total = self.booking.calculate_total_amount()
            if new_total != self.booking.total_amount:
                Booking.objects.filter(pk=self.booking.pk).update(
                    total_amount=new_total
                )
                logger.info(f"Updated booking {self.booking.agent_booking_reference} total after other product: {new_total}")
        except Exception as e:
            logger.error(f"Error updating booking total after other product: {e}")

# ============================================================================
# BOOKING TRANSACTION MODEL
# ============================================================================

class BookingTransaction(models.Model):
    """
    Universal transaction tracking for all booking amendments.
    
    Tracks the complete lifecycle of any booking component:
    - Original bookings
    - Exchanges/modifications
    - Refunds (full or partial)
    - Cancellations
    - Voids
    - Reissues
    
    Links to: AirBooking, AccommodationBooking, CarHireBooking, ServiceFee
    """
    
    # Transaction types that apply across all booking categories
    TRANSACTION_TYPE_CHOICES = [
        # Original transaction
        ('ORIGINAL', 'Original Booking'),
        
        # Air-specific
        ('EXCHANGE', 'Ticket Exchange'),
        ('REISSUE', 'Ticket Reissue'),
        ('VOID', 'Ticket Void'),
        
        # Modifications (all types)
        ('MODIFICATION', 'Booking Modification'),
        ('DATE_CHANGE', 'Date Change'),
        ('UPGRADE', 'Upgrade'),
        ('DOWNGRADE', 'Downgrade'),
        
        # Cancellations & Refunds (all types)
        ('CANCELLATION', 'Cancellation'),
        ('PARTIAL_CANCELLATION', 'Partial Cancellation'),
        ('REFUND', 'Refund'),
        ('PARTIAL_REFUND', 'Partial Refund'),
        
        # Adjustments
        ('ADJUSTMENT', 'Price Adjustment'),
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
        ('FEE_ADJUSTMENT', 'Fee Adjustment'),
    ]
    
    # Status of this transaction
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    # =============================================================================
    # IDENTIFICATION
    # =============================================================================
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    
    # =============================================================================
    # POLYMORPHIC LINK TO BOOKING COMPONENT
    # =============================================================================
    # This allows linking to AirBooking, AccommodationBooking, CarHireBooking, etc.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            'model__in': ('airbooking', 'accommodationbooking', 'carhirebooking', 'servicefee')
        },
        verbose_name="Booking Type"
    )
    object_id = models.UUIDField(
        verbose_name="Booking ID"
    )
    booking_component = GenericForeignKey('content_type', 'object_id')
    
    # =============================================================================
    # TRANSACTION DETAILS
    # =============================================================================
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPE_CHOICES,
        db_index=True,
        help_text="Type of transaction (original, exchange, refund, etc.)"
    )
    
    transaction_date = models.DateField(
        db_index=True,
        help_text="Date the transaction was processed"
    )
    
    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="External reference (ticket number, confirmation code, etc.)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CONFIRMED',
        db_index=True
    )
    
    # =============================================================================
    # FINANCIAL DETAILS
    # =============================================================================
    # All amounts support positive (charge) and negative (credit/refund) values
    
    currency = models.CharField(
        max_length=3,
        default='AUD',
        help_text="Transaction currency (e.g., AUD, USD, EUR)"
    )
    
    # Breakdown of costs
    base_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Base fare/rate amount (can be negative for refunds)"
    )
    
    taxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tax amount (can be negative for refunds)"
    )
    
    fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fees charged (can be negative for credits)"
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_index=True,
        help_text="Total transaction amount (base + taxes + fees). Negative = refund/credit"
    )
    
    # Converted to organization's base currency
    base_amount_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Base amount converted to organization base currency"
    )
    
    taxes_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Taxes converted to organization base currency"
    )
    
    fees_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fees converted to organization base currency"
    )
    
    total_amount_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
        help_text="Total amount in organization base currency"
    )
    
    exchange_rate = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Exchange rate used for currency conversion"
    )
    
    # =============================================================================
    # REASON & NOTES
    # =============================================================================
    reason = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reason for transaction (why was ticket exchanged, booking cancelled, etc.)"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Additional notes, comments, or details"
    )
    
    # =============================================================================
    # AUDIT TRAIL
    # =============================================================================
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_created',
        help_text="User who created this transaction record"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    # =============================================================================
    # META
    # =============================================================================
    class Meta:
        db_table = 'booking_transactions'
        ordering = ['transaction_date', 'created_at']
        indexes = [
            # Query by booking component
            models.Index(fields=['content_type', 'object_id']),
            # Query by transaction type and date
            models.Index(fields=['transaction_type', 'transaction_date']),
            # Query by status
            models.Index(fields=['status', 'transaction_date']),
            # Financial queries
            models.Index(fields=['transaction_date', 'total_amount']),
            models.Index(fields=['currency', 'transaction_date']),
        ]
        verbose_name = 'Booking Transaction'
        verbose_name_plural = 'Booking Transactions'
    
    # =============================================================================
    # METHODS
    # =============================================================================
    def __str__(self):
        """String representation showing transaction type and amount"""
        amount_display = f"{self.currency} {self.total_amount:,.2f}"
        if self.total_amount < 0:
            amount_display = f"({amount_display})"  # Show negative in parentheses
        
        return f"{self.get_transaction_type_display()} - {amount_display} - {self.transaction_date}"
    
    def save(self, *args, **kwargs):
        """
        Auto-calculate total_amount and convert to base currency on save.
        Uses .update() to avoid infinite recursion.
        """
        # Calculate total if not already set
        if self.total_amount is None or self.total_amount == 0:
            self.total_amount = self.base_amount + self.taxes + self.fees
        
        # Save first to get the ID
        super().save(*args, **kwargs)
        
        # Convert to base currency if needed
        self.convert_to_base_currency()
    
    def convert_to_base_currency(self):
        """
        Convert transaction amounts to organization's base currency.
        Gets the base currency from the booking's organization.
        """
        # Import here to avoid circular imports
        from apps.reference_data.models import CurrencyExchangeRate
        
        # Get the booking component to find the organization
        booking_component = self.booking_component
        if not booking_component:
            return
        
        # Get the parent Booking to access organization
        try:
            parent_booking = booking_component.booking
            org = parent_booking.organization
            base_currency = org.base_currency
        except AttributeError:
            # Couldn't find organization, skip conversion
            return
        
        # If already in base currency, just copy values
        if self.currency == base_currency:
            BookingTransaction.objects.filter(pk=self.pk).update(
                base_amount_base=self.base_amount,
                taxes_base=self.taxes,
                fees_base=self.fees,
                total_amount_base=self.total_amount,
                exchange_rate=Decimal('1.000000')
            )
            return
        
        # Get exchange rate
        rate = CurrencyExchangeRate.get_rate(
            from_currency=self.currency,
            to_currency=base_currency,
            date=self.transaction_date
        )
        
        if rate is None:
            # No rate found, log warning and use 1:1 fallback
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"No exchange rate found for {self.currency} to {base_currency} "
                f"on {self.transaction_date}. Using 1:1 rate."
            )
            rate = Decimal('1.0')
        
        # Convert all amounts
        BookingTransaction.objects.filter(pk=self.pk).update(
            base_amount_base=self.base_amount * rate,
            taxes_base=self.taxes * rate,
            fees_base=self.fees * rate,
            total_amount_base=self.total_amount * rate,
            exchange_rate=rate
        )
    
    @property
    def is_refund(self):
        """Check if this is a refund/credit transaction"""
        return self.total_amount < 0
    
    @property
    def is_cancellation(self):
        """Check if this is a cancellation"""
        return self.transaction_type in ['CANCELLATION', 'PARTIAL_CANCELLATION', 'VOID']
    
    @property
    def booking_reference(self):
        """Get the booking reference from the parent booking"""
        try:
            return self.booking_component.booking.agent_booking_reference
        except AttributeError:
            return "N/A"

# =============================================================================
# BOOKING AUDIT LOG MODEL
# =============================================================================

class BookingAuditLog(models.Model):
    """
    Complete audit trail for booking-level changes.
    
    Captures ALL changes to bookings and related objects:
    - Transaction additions/modifications/deletions
    - Booking field changes
    - Component changes (Air/Accommodation/Car)
    - Status changes
    - Financial adjustments
    
    Provides compliance documentation and complete change history.
    """
    
    # Action types
    ACTION_CHOICES = [
        # Transaction actions
        ('TRANSACTION_CREATED', 'Transaction Created'),
        ('TRANSACTION_MODIFIED', 'Transaction Modified'),
        ('TRANSACTION_DELETED', 'Transaction Deleted'),
        
        # Booking actions
        ('BOOKING_CREATED', 'Booking Created'),
        ('BOOKING_MODIFIED', 'Booking Modified'),
        ('BOOKING_DELETED', 'Booking Deleted'),
        ('BOOKING_STATUS_CHANGED', 'Booking Status Changed'),
        
        # Component actions
        ('COMPONENT_CREATED', 'Component Created'),
        ('COMPONENT_MODIFIED', 'Component Modified'),
        ('COMPONENT_DELETED', 'Component Deleted'),
        
        # Financial actions
        ('TOTAL_RECALCULATED', 'Total Recalculated'),
        ('CURRENCY_CONVERTED', 'Currency Converted'),
        ('REFUND_PROCESSED', 'Refund Processed'),
        
        # Other
        ('NOTE_ADDED', 'Note Added'),
        ('SYSTEM_ACTION', 'System Action'),
    ]
    
    # =============================================================================
    # IDENTIFICATION
    # =============================================================================
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Link to the main booking
    booking = models.ForeignKey(
        'Booking',
        on_delete=models.CASCADE,
        related_name='audit_logs',
        db_index=True,
        help_text="The booking this audit log entry relates to"
    )
    
    # =============================================================================
    # ACTION DETAILS
    # =============================================================================
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Type of action performed"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this action occurred"
    )
    
    # =============================================================================
    # RELATED OBJECT (Optional - for component/transaction changes)
    # =============================================================================
    # Links to the object that was changed (Transaction, AirBooking, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Type of related object (if applicable)"
    )
    
    object_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of related object (if applicable)"
    )
    
    related_object = GenericForeignKey('content_type', 'object_id')
    
    related_object_repr = models.CharField(
        max_length=255,
        blank=True,
        help_text="String representation of related object (preserved even after deletion)"
    )
    
    # =============================================================================
    # CHANGE DETAILS
    # =============================================================================
    field_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of field that changed (if applicable)"
    )
    
    old_value = models.JSONField(
        null=True,
        blank=True,
        encoder=DjangoJSONEncoder,
        help_text="Previous value (JSON format)"
    )
    
    new_value = models.JSONField(
        null=True,
        blank=True,
        encoder=DjangoJSONEncoder,
        help_text="New value (JSON format)"
    )
    
    # =============================================================================
    # DESCRIPTION & CONTEXT
    # =============================================================================
    description = models.TextField(
        help_text="Human-readable description of what changed"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or context"
    )
    
    # =============================================================================
    # USER TRACKING
    # =============================================================================
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booking_audit_logs',
        help_text="User who performed this action"
    )
    
    user_repr = models.CharField(
        max_length=255,
        blank=True,
        help_text="String representation of user (preserved even after user deletion)"
    )
    
    # IP address for additional tracking
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of user who made the change"
    )
    
    # =============================================================================
    # METADATA
    # =============================================================================
    class Meta:
        db_table = 'booking_audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['booking', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
        verbose_name = 'Booking Audit Log'
        verbose_name_plural = 'Booking Audit Logs'
    
    # =============================================================================
    # METHODS
    # =============================================================================
    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.get_action_display()} - {self.booking.agent_booking_reference}"
    
    def save(self, *args, **kwargs):
        """Auto-populate string representations"""
        # Store string representation of related object
        if self.related_object and not self.related_object_repr:
            self.related_object_repr = str(self.related_object)
        
        # Store string representation of user
        if self.user and not self.user_repr:
            self.user_repr = str(self.user)
        
        super().save(*args, **kwargs)
    
    @classmethod
    def log_transaction_created(cls, booking, transaction, user=None):
        """Log when a transaction is created"""
        return cls.objects.create(
            booking=booking,
            action='TRANSACTION_CREATED',
            content_type=ContentType.objects.get_for_model(transaction),
            object_id=transaction.id,
            related_object_repr=str(transaction),
            description=f"Transaction created: {transaction.get_transaction_type_display()} - {transaction.currency} {transaction.total_amount}",
            new_value={
                'transaction_type': transaction.transaction_type,
                'total_amount': str(transaction.total_amount),
                'currency': transaction.currency,
                'transaction_date': transaction.transaction_date.isoformat(),
            },
            user=user
        )
    
    @classmethod
    def log_transaction_modified(cls, booking, transaction, old_data, new_data, user=None):
        """Log when a transaction is modified"""
        changes = []
        for key in old_data.keys():
            if old_data.get(key) != new_data.get(key):
                changes.append(f"{key}: {old_data.get(key)} → {new_data.get(key)}")
        
        return cls.objects.create(
            booking=booking,
            action='TRANSACTION_MODIFIED',
            content_type=ContentType.objects.get_for_model(transaction),
            object_id=transaction.id,
            related_object_repr=str(transaction),
            description=f"Transaction modified: {', '.join(changes)}",
            old_value=old_data,
            new_value=new_data,
            user=user
        )
    
    @classmethod
    def log_transaction_deleted(cls, booking, transaction_data, user=None):
        """Log when a transaction is deleted"""
        return cls.objects.create(
            booking=booking,
            action='TRANSACTION_DELETED',
            related_object_repr=f"{transaction_data.get('transaction_type')} - {transaction_data.get('currency')} {transaction_data.get('total_amount')}",
            description=f"Transaction deleted: {transaction_data.get('transaction_type')} - {transaction_data.get('currency')} {transaction_data.get('total_amount')}",
            old_value=transaction_data,
            user=user
        )
    
    @classmethod
    def log_booking_modified(cls, booking, field_name, old_value, new_value, user=None):
        """Log when a booking field is modified"""
        return cls.objects.create(
            booking=booking,
            action='BOOKING_MODIFIED',
            field_name=field_name,
            old_value={'value': old_value},
            new_value={'value': new_value},
            description=f"Booking {field_name} changed from {old_value} to {new_value}",
            user=user
        )
    
    @classmethod
    def log_total_recalculated(cls, booking, old_total, new_total, reason='', user=None):
        """Log when booking total is recalculated"""
        return cls.objects.create(
            booking=booking,
            action='TOTAL_RECALCULATED',
            field_name='total_amount',
            old_value={'total': str(old_total)},
            new_value={'total': str(new_total)},
            description=f"Total recalculated: {old_total} → {new_total}. {reason}",
            user=user
        )
    
    @classmethod
    def log_component_change(cls, booking, component, action_type, description, user=None):
        """Log component (Air/Accommodation/Car) changes"""
        return cls.objects.create(
            booking=booking,
            action=action_type,
            content_type=ContentType.objects.get_for_model(component),
            object_id=component.id,
            related_object_repr=str(component),
            description=description,
            user=user
        )

# =============================================================================
# USAGE EXAMPLES
# =============================================================================
"""
Example 1: Original Air Booking
--------------------------------
BookingTransaction.objects.create(
    content_type=ContentType.objects.get_for_model(AirBooking),
    object_id=air_booking.id,
    transaction_type='ORIGINAL',
    transaction_date=date(2025, 10, 15),
    transaction_reference='TKT-1234567890',
    base_amount=Decimal('450.00'),
    taxes=Decimal('45.00'),
    fees=Decimal('5.00'),
    total_amount=Decimal('500.00'),
    currency='AUD',
    reason='Original ticket purchase',
)

Example 2: Ticket Exchange with Additional Cost
------------------------------------------------
BookingTransaction.objects.create(
    content_type=ContentType.objects.get_for_model(AirBooking),
    object_id=air_booking.id,
    transaction_type='EXCHANGE',
    transaction_date=date(2025, 10, 20),
    transaction_reference='TKT-1234567891',
    base_amount=Decimal('150.00'),  # Additional fare
    taxes=Decimal('15.00'),
    fees=Decimal('50.00'),  # Exchange fee
    total_amount=Decimal('215.00'),
    currency='AUD',
    reason='Date change - departure moved forward 3 days',
)

Example 3: Partial Refund (Negative Amount)
--------------------------------------------
BookingTransaction.objects.create(
    content_type=ContentType.objects.get_for_model(AirBooking),
    object_id=air_booking.id,
    transaction_type='PARTIAL_REFUND',
    transaction_date=date(2025, 10, 25),
    transaction_reference='REF-9876543210',
    base_amount=Decimal('-300.00'),  # Negative = refund
    taxes=Decimal('-30.00'),
    fees=Decimal('25.00'),  # Non-refundable admin fee (positive)
    total_amount=Decimal('-305.00'),  # Net refund
    currency='AUD',
    reason='Trip cancelled - partial refund processed',
)

Example 4: Accommodation Cancellation
--------------------------------------
BookingTransaction.objects.create(
    content_type=ContentType.objects.get_for_model(AccommodationBooking),
    object_id=accommodation_booking.id,
    transaction_type='CANCELLATION',
    transaction_date=date(2025, 10, 18),
    base_amount=Decimal('-800.00'),  # Full refund of room charges
    taxes=Decimal('-80.00'),
    fees=Decimal('50.00'),  # Cancellation fee retained
    total_amount=Decimal('-830.00'),
    currency='AUD',
    reason='Hotel booking cancelled due to change in travel plans',
)

Example 5: Car Hire Date Extension
-----------------------------------
BookingTransaction.objects.create(
    content_type=ContentType.objects.get_for_model(CarHireBooking),
    object_id=car_hire_booking.id,
    transaction_type='MODIFICATION',
    transaction_date=date(2025, 10, 22),
    base_amount=Decimal('120.00'),  # 2 additional days at $60/day
    taxes=Decimal('12.00'),
    fees=Decimal('0.00'),
    total_amount=Decimal('132.00'),
    currency='AUD',
    reason='Extended rental by 2 days',
)

Example 6: Get All Transactions for a Booking Component
--------------------------------------------------------
from django.contrib.contenttypes.models import ContentType

# Get all transactions for an air booking
ct = ContentType.objects.get_for_model(AirBooking)
transactions = BookingTransaction.objects.filter(
    content_type=ct,
    object_id=air_booking.id
).order_by('transaction_date')

# Calculate net amount across all transactions
total = sum(t.total_amount for t in transactions)

Example 7: Query Refunds in a Date Range
-----------------------------------------
refunds = BookingTransaction.objects.filter(
    transaction_type__in=['REFUND', 'PARTIAL_REFUND'],
    transaction_date__range=['2025-10-01', '2025-10-31'],
    total_amount__lt=0  # Negative amounts
)
"""


# ============================================================================
# PREFERRED AIRLINE SUPPLIER TRACKING
# ============================================================================

class PreferredAirline(models.Model):
    """
    Tracks preferred airline contracts and target market shares for customer organizations.

    Used for:
    - Airline deals analysis and compliance tracking
    - Market share calculations (% of revenue on preferred airlines)
    - Route-level performance monitoring
    - Restricted economy fare tracking

    Example:
        Qantas - Domestic contract with 85% target market share
        Singapore Airlines - International (UK, USA, SG routes) with 80% target
    """

    MARKET_TYPE_CHOICES = [
        ('DOMESTIC', 'Domestic'),
        ('INTERNATIONAL', 'International'),
    ]

    # =============================================================================
    # IDENTIFICATION
    # =============================================================================
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='preferred_airlines',
        help_text="Customer organization with this preferred airline contract"
    )

    # =============================================================================
    # AIRLINE DETAILS
    # =============================================================================
    airline_iata_code = models.CharField(
        max_length=3,
        help_text="IATA airline code (e.g., QF for Qantas, SQ for Singapore Airlines)"
    )

    airline_name = models.CharField(
        max_length=200,
        help_text="Full airline name (e.g., Qantas Airways, Singapore Airlines)"
    )

    # =============================================================================
    # MARKET SCOPE
    # =============================================================================
    market_type = models.CharField(
        max_length=20,
        choices=MARKET_TYPE_CHOICES,
        db_index=True,
        help_text="Whether this contract is for domestic or international travel"
    )

    # For international airlines: which countries/markets they service
    # For domestic: typically null or ['ALL']
    markets_served = models.JSONField(
        default=list,
        blank=True,
        help_text="List of country codes served (e.g., ['UK', 'USA', 'SG']). For domestic, use ['ALL'] or leave empty."
    )

    # Specific routes covered by this contract
    # Examples: ['MEL-SYD', 'SYD-BNE', 'MEL-BNE'] or ['ALL'] for all domestic routes
    routes_covered = models.JSONField(
        default=list,
        blank=True,
        help_text="Specific routes covered (e.g., ['MEL-SYD', 'SYD-BNE']) or ['ALL'] for all routes"
    )

    # =============================================================================
    # CONTRACT TARGETS
    # =============================================================================
    target_market_share = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Target market share percentage (e.g., 85.00 for 85%)"
    )

    target_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Target revenue amount in base currency (e.g., 500000.00 for $500,000)"
    )

    # =============================================================================
    # CONTRACT PERIOD
    # =============================================================================
    contract_start_date = models.DateField(
        db_index=True,
        help_text="Date this airline contract becomes effective"
    )

    contract_end_date = models.DateField(
        db_index=True,
        help_text="Date this airline contract expires"
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this contract is currently active"
    )

    # =============================================================================
    # ADDITIONAL DETAILS
    # =============================================================================
    notes = models.TextField(
        blank=True,
        help_text="Additional contract details, terms, or special conditions"
    )

    # =============================================================================
    # AUDIT TRAIL
    # =============================================================================
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_airlines_created',
        help_text="User who created this preferred airline record"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =============================================================================
    # META
    # =============================================================================
    class Meta:
        db_table = 'preferred_airlines'
        ordering = ['organization', 'market_type', 'airline_name']
        indexes = [
            models.Index(fields=['organization', 'market_type']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['airline_iata_code']),
            models.Index(fields=['contract_start_date', 'contract_end_date']),
        ]
        unique_together = [
            ['organization', 'airline_iata_code', 'market_type', 'contract_start_date']
        ]
        verbose_name = 'Preferred Airline'
        verbose_name_plural = 'Preferred Airlines'

    # =============================================================================
    # METHODS
    # =============================================================================
    def __str__(self):
        return f"{self.organization.code} - {self.airline_name} ({self.market_type})"

    def is_contract_active(self, check_date=None):
        """
        Check if contract is active on a specific date

        Args:
            check_date: Date to check (defaults to today)

        Returns:
            bool: True if contract is active on the given date
        """
        from django.utils import timezone
        if check_date is None:
            check_date = timezone.now().date()

        return (
            self.is_active and
            self.contract_start_date <= check_date <= self.contract_end_date
        )

    def covers_route(self, origin_code, destination_code):
        """
        Check if this preferred airline contract covers a specific route

        Args:
            origin_code: Origin airport IATA code (e.g., 'MEL')
            destination_code: Destination airport IATA code (e.g., 'SYD')

        Returns:
            bool: True if route is covered by this contract
        """
        # If no specific routes defined or 'ALL', covers everything
        if not self.routes_covered or 'ALL' in self.routes_covered:
            return True

        # Check both directions (MEL-SYD and SYD-MEL)
        route_forward = f"{origin_code}-{destination_code}"
        route_reverse = f"{destination_code}-{origin_code}"

        return route_forward in self.routes_covered or route_reverse in self.routes_covered

    def covers_market(self, country_code):
        """
        Check if this preferred airline contract covers a specific market/country

        Args:
            country_code: ISO country code (e.g., 'UK', 'USA', 'SG')

        Returns:
            bool: True if market is covered by this contract
        """
        # If no specific markets defined or 'ALL', covers everything
        if not self.markets_served or 'ALL' in self.markets_served:
            return True

        return country_code in self.markets_served


# ============================================================================
# PREFERRED HOTEL MODEL
# ============================================================================

class PreferredHotel(models.Model):
    """
    Tracks preferred hotel contracts and target metrics for customer organizations.

    Used for:
    - Hotel deals analysis and compliance tracking
    - Room night and revenue tracking
    - Location-specific performance monitoring
    - Chain vs independent hotel preferences

    Example:
        Marriott - Sydney CBD with 1000 room nights target
        Hilton - Melbourne with $250,000 revenue target
    """

    MARKET_TYPE_CHOICES = [
        ('DOMESTIC', 'Domestic'),
        ('INTERNATIONAL', 'International'),
    ]

    # =============================================================================
    # IDENTIFICATION
    # =============================================================================
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='preferred_hotels',
        help_text="Customer organization with this preferred hotel contract"
    )

    # =============================================================================
    # HOTEL DETAILS
    # =============================================================================
    hotel_chain = models.CharField(
        max_length=200,
        help_text="Hotel chain name (e.g., Marriott, Hilton, Accor)"
    )

    # Optional: Link to specific hotel in master data
    hotel = models.ForeignKey(
        'reference_data.Hotel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_contracts',
        help_text="Specific hotel (optional - leave blank for chain-wide contracts)"
    )

    # =============================================================================
    # LOCATION SCOPE
    # =============================================================================
    market_type = models.CharField(
        max_length=20,
        choices=MARKET_TYPE_CHOICES,
        db_index=True,
        help_text="Whether this contract is for domestic or international hotels"
    )

    # City or location for this contract
    location_city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City/location for this contract (e.g., 'Sydney', 'Melbourne'). Leave blank for all locations."
    )

    location_country = models.CharField(
        max_length=100,
        blank=True,
        help_text="Country for this contract. Leave blank for all countries."
    )

    # =============================================================================
    # CONTRACT TARGETS
    # =============================================================================
    target_room_nights = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Target number of room nights per year (e.g., 1000)"
    )

    target_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Target revenue amount in base currency (e.g., 250000.00 for $250,000)"
    )

    # Priority level for multi-tier agreements
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Priority level (1=highest, 10=lowest) for tiered agreements"
    )

    # =============================================================================
    # CONTRACT PERIOD
    # =============================================================================
    contract_start_date = models.DateField(
        db_index=True,
        help_text="Date this hotel contract becomes effective"
    )

    contract_end_date = models.DateField(
        db_index=True,
        help_text="Date this hotel contract expires"
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this contract is currently active"
    )

    # =============================================================================
    # ADDITIONAL DETAILS
    # =============================================================================
    notes = models.TextField(
        blank=True,
        help_text="Additional contract details, terms, or special conditions"
    )

    # =============================================================================
    # AUDIT TRAIL
    # =============================================================================
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_hotels_created',
        help_text="User who created this preferred hotel record"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =============================================================================
    # META
    # =============================================================================
    class Meta:
        db_table = 'preferred_hotels'
        ordering = ['organization', 'market_type', 'priority', 'hotel_chain']
        indexes = [
            models.Index(fields=['organization', 'market_type']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['hotel_chain']),
            models.Index(fields=['contract_start_date', 'contract_end_date']),
            models.Index(fields=['location_city', 'location_country']),
        ]
        unique_together = [
            ['organization', 'hotel_chain', 'location_city', 'contract_start_date']
        ]
        verbose_name = 'Preferred Hotel'
        verbose_name_plural = 'Preferred Hotels'

    # =============================================================================
    # METHODS
    # =============================================================================
    def __str__(self):
        location = self.location_city or self.location_country or 'All Locations'
        return f"{self.organization.code} - {self.hotel_chain} ({location}, {self.market_type})"

    def is_contract_active(self, check_date=None):
        """
        Check if contract is active on a specific date

        Args:
            check_date: Date to check (defaults to today)

        Returns:
            bool: True if contract is active on the given date
        """
        from django.utils import timezone
        if check_date is None:
            check_date = timezone.now().date()

        return (
            self.is_active and
            self.contract_start_date <= check_date <= self.contract_end_date
        )

    def matches_location(self, city=None, country=None):
        """
        Check if this preferred hotel contract covers a specific location

        Args:
            city: City name to check (optional)
            country: Country name to check (optional)

        Returns:
            bool: True if location is covered by this contract
        """
        # If no specific location defined, covers everything
        if not self.location_city and not self.location_country:
            return True

        # Check city match
        if self.location_city:
            if city and self.location_city.lower() == city.lower():
                return True
            return False

        # Check country match
        if self.location_country:
            if country and self.location_country.lower() == country.lower():
                return True
            return False

        return False


# ============================================================================
# PREFERRED CAR HIRE MODEL
# ============================================================================

class PreferredCarHire(models.Model):
    """
    Tracks preferred car hire supplier contracts and target metrics for customer organizations.

    Used for:
    - Car rental deals analysis and compliance tracking
    - Rental days and revenue tracking
    - Market-specific (country/region) performance monitoring
    - Supplier relationship management

    Example:
        Hertz - Australia with 5000 rental days target
        Avis - New Zealand with $500,000 revenue target
        Budget - USA with focus on compact car category
    """

    MARKET_CHOICES = [
        ('AUSTRALIA', 'Australia'),
        ('NEW_ZEALAND', 'New Zealand'),
        ('USA', 'United States'),
        ('UK', 'United Kingdom'),
        ('CANADA', 'Canada'),
        ('OTHER', 'Other'),
    ]

    CAR_CATEGORY_CHOICES = [
        ('ANY', 'Any Category'),
        ('COMPACT', 'Compact'),
        ('SEDAN', 'Sedan'),
        ('SUV', 'SUV'),
        ('LUXURY', 'Luxury'),
        ('VAN', 'Van/Minivan'),
        ('TRUCK', 'Truck/Ute'),
    ]

    # =============================================================================
    # IDENTIFICATION
    # =============================================================================
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='preferred_car_hires',
        help_text="Customer organization with this preferred car hire contract"
    )

    # =============================================================================
    # SUPPLIER DETAILS
    # =============================================================================
    supplier = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Car hire supplier name (e.g., Hertz, Avis, Budget, Enterprise)"
    )

    related_brands = models.TextField(
        blank=True,
        help_text="Comma-separated list of related brands that should also count as compliant (e.g., 'Budget, Payless' for an Avis contract)"
    )

    # =============================================================================
    # MARKET SCOPE
    # =============================================================================
    market = models.CharField(
        max_length=50,
        choices=MARKET_CHOICES,
        db_index=True,
        help_text="Geographic market/country for this contract"
    )

    # Optional: Specific car category focus
    car_category = models.CharField(
        max_length=20,
        choices=CAR_CATEGORY_CHOICES,
        default='ANY',
        help_text="Specific car category for this contract (optional)"
    )

    # =============================================================================
    # CONTRACT TARGETS
    # =============================================================================
    target_rental_days = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Target number of rental days per year (e.g., 5000)"
    )

    target_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Target revenue amount in base currency (e.g., 500000.00 for $500k)"
    )

    # Priority level for multi-tier agreements
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Priority level (1=highest, 10=lowest) for tiered agreements"
    )

    # =============================================================================
    # CONTRACT PERIOD
    # =============================================================================
    contract_start_date = models.DateField(
        db_index=True,
        help_text="Date this car hire contract becomes effective"
    )

    contract_end_date = models.DateField(
        db_index=True,
        help_text="Date this car hire contract expires"
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this contract is currently active"
    )

    # =============================================================================
    # ADDITIONAL DETAILS
    # =============================================================================
    notes = models.TextField(
        blank=True,
        help_text="Additional contract details, terms, or special conditions"
    )

    # =============================================================================
    # AUDIT TRAIL
    # =============================================================================
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_car_hires_created',
        help_text="User who created this preferred car hire record"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =============================================================================
    # META
    # =============================================================================
    class Meta:
        db_table = 'preferred_car_hires'
        ordering = ['organization', 'market', 'priority', 'supplier']
        indexes = [
            models.Index(fields=['organization', 'market']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['supplier']),
            models.Index(fields=['contract_start_date', 'contract_end_date']),
        ]
        unique_together = [
            ['organization', 'supplier', 'market', 'contract_start_date']
        ]
        verbose_name = 'Preferred Car Hire'
        verbose_name_plural = 'Preferred Car Hires'

    # =============================================================================
    # METHODS
    # =============================================================================
    def __str__(self):
        category_str = f" ({self.get_car_category_display()})" if self.car_category != 'ANY' else ''
        return f"{self.organization.code} - {self.supplier} ({self.get_market_display()}{category_str})"

    def is_contract_active(self, check_date=None):
        """
        Check if contract is active on a specific date

        Args:
            check_date: Date to check (defaults to today)

        Returns:
            bool: True if contract is active on the given date
        """
        from django.utils import timezone
        if check_date is None:
            check_date = timezone.now().date()

        return (
            self.is_active and
            self.contract_start_date <= check_date <= self.contract_end_date
        )

    def matches_market(self, market):
        """
        Check if this contract covers a specific market

        Args:
            market: Market/country to check

        Returns:
            bool: True if market is covered by this contract
        """
        if not market:
            return False

        return self.market.upper() == market.upper()

    def matches_category(self, category):
        """
        Check if this contract covers a specific car category

        Args:
            category: Car category to check

        Returns:
            bool: True if category is covered (ANY matches all)
        """
        if self.car_category == 'ANY':
            return True

        if not category:
            return True  # No category specified, so it matches

        return self.car_category.upper() == category.upper()


# ============================================================================
# DATA MERGE AUDIT MODEL
# ============================================================================

class MergeAudit(models.Model):
    """
    Track all merge operations for audit trail and undo capability
    
    Supports merging of:
    - Travellers (within organizations)
    - Travel Consultants  
    - Organizations
    - Service Fees
    
    Provides:
    - Complete audit trail
    - Undo capability via data snapshots
    - Relationship tracking
    """
    MERGE_TYPE_CHOICES = [
        ('TRAVELLER', 'Traveller'),
        ('CONSULTANT', 'Travel Consultant'),
        ('ORGANIZATION', 'Organization'),
        ('SERVICE_FEE', 'Service Fee'),
    ]

    STATUS_CHOICES = [
        ('COMPLETED', 'Completed'),
        ('UNDONE', 'Undone'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # What type of merge
    merge_type = models.CharField(max_length=20, choices=MERGE_TYPE_CHOICES)

    # Who performed the merge
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_merges'
    )

    # Organization/Travel Agent context
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='merge_audits',
        help_text="Organization context for this merge"
    )

    # The primary record (the one kept)
    primary_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='primary_merges'
    )
    primary_object_id = models.CharField(max_length=255)
    primary_object = GenericForeignKey('primary_content_type', 'primary_object_id')

    # IDs of merged records (that were deleted)
    merged_record_ids = models.JSONField(
        default=list,
        help_text="List of IDs of records that were merged into the primary"
    )

    # Data snapshot before merge (for undo)
    merged_records_snapshot = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
        help_text="Full data of merged records before deletion"
    )

    # Relationship updates (what got reassigned)
    relationship_updates = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
        help_text="Track which related records were updated (bookings, etc.)"
    )

    # Chosen values
    chosen_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name chosen/entered during merge"
    )
    chosen_employee_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Employee ID preserved during merge"
    )

    # Merge summary
    summary = models.TextField(
        blank=True,
        help_text="Human-readable summary of the merge"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='COMPLETED'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    undone_at = models.DateTimeField(null=True, blank=True)
    undone_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='undone_merges'
    )

    class Meta:
        db_table = 'merge_audits'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merge_type', 'status']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['performed_by', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_merge_type_display()} merge by {self.performed_by} on {self.created_at.strftime('%Y-%m-%d')}"
