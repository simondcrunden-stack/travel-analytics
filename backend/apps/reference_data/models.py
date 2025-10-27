from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Airport(models.Model):
    """Airport reference data"""
    iata_code = models.CharField(max_length=3, primary_key=True)  # IATA code
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    timezone = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'airports'
        ordering = ['iata_code']
    
    def __str__(self):
        return f"{self.iata_code} - {self.name}"


class Airline(models.Model):
    """Airline reference data"""
    iata_code = models.CharField(max_length=3, primary_key=True)  # IATA code
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True)
    alliance = models.CharField(max_length=50, blank=True)  # Star Alliance, OneWorld, etc.
    
    class Meta:
        db_table = 'airlines'
        ordering = ['iata_code']
    
    def __str__(self):
        return f"{self.iata_code} - {self.name}"


class CurrencyExchangeRate(models.Model):
    """Store daily exchange rates for currency conversion"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Currency pair
    from_currency = models.CharField(max_length=3)  # e.g., USD, GBP, EUR
    to_currency = models.CharField(max_length=3)    # e.g., AUD
    
    # Rate
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6,
                                       validators=[MinValueValidator(Decimal('0.000001'))])
    rate_date = models.DateField()
    
    # Source of rate
    rate_source = models.CharField(max_length=100, blank=True)  # e.g., "Reserve Bank of Australia"
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'currency_exchange_rates'
        indexes = [
            models.Index(fields=['from_currency', 'to_currency', 'rate_date']),
            models.Index(fields=['rate_date']),
        ]
        unique_together = [['from_currency', 'to_currency', 'rate_date']]
        ordering = ['-rate_date']
    
    def __str__(self):
        return f"{self.from_currency}/{self.to_currency}: {self.exchange_rate} ({self.rate_date})"
    
    @staticmethod
    def get_rate(from_currency, to_currency, date):
        """Get exchange rate for a specific date"""
        if from_currency == to_currency:
            return Decimal('1.0')
        
        try:
            rate = CurrencyExchangeRate.objects.get(
                from_currency=from_currency,
                to_currency=to_currency,
                rate_date=date
            )
            return rate.exchange_rate
        except CurrencyExchangeRate.DoesNotExist:
            # Try to find the most recent rate before this date
            rate = CurrencyExchangeRate.objects.filter(
                from_currency=from_currency,
                to_currency=to_currency,
                rate_date__lte=date
            ).first()
            
            if rate:
                return rate.exchange_rate
            
            return None
    
    @staticmethod
    def convert_amount(amount, from_currency, to_currency, date):
        """Convert an amount from one currency to another"""
        if from_currency == to_currency:
            return amount
        
        rate = CurrencyExchangeRate.get_rate(from_currency, to_currency, date)
        if rate:
            return amount * rate
        
        return None

# ============================================================================
# COUNTRY MODELS
# ============================================================================

class Country(models.Model):
    """ISO 3166-1 Country reference data for standardized country identification"""
    
    # ISO codes (using alpha_3 as primary key for consistency with HighRiskDestination)
    alpha_2 = models.CharField(max_length=2, unique=True, help_text="ISO 3166-1 alpha-2 code (e.g., AU)")
    alpha_3 = models.CharField(max_length=3, unique=True, primary_key=True, 
                               help_text="ISO 3166-1 alpha-3 code (e.g., AUS)")
    numeric_code = models.CharField(max_length=3, blank=True, help_text="ISO 3166-1 numeric code (e.g., 036)")
    
    # Names
    name = models.CharField(max_length=100, help_text="Official country name")
    common_name = models.CharField(max_length=100, blank=True, help_text="Commonly used name")
    
    # Regional classification (UN M49 standard)
    region = models.CharField(max_length=50, blank=True, 
                             help_text="UN region: Africa, Americas, Asia, Europe, Oceania")
    subregion = models.CharField(max_length=50, blank=True,
                                help_text="UN subregion: e.g., South-Eastern Asia, Western Europe")
    
    # Practical info
    currency_code = models.CharField(max_length=3, blank=True, help_text="ISO 4217 currency code")
    phone_prefix = models.CharField(max_length=10, blank=True, help_text="International dialing code")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'countries'
        ordering = ['name']
        verbose_name_plural = 'Countries'
    
    def __str__(self):
        return f"{self.name} ({self.alpha_3})"
    
    def is_domestic_for_organization(self, organization):
        """
        Dynamically determine if this country is domestic for a given organization.
        
        Args:
            organization: Organization model instance
            
        Returns:
            bool: True if country matches organization's home_country
        """
        if not organization or not hasattr(organization, 'home_country'):
            return False
        return self.alpha_3 == organization.home_country
    
    @classmethod
    def get_domestic_country(cls, organization):
        """
        Get the domestic country for an organization.
        
        Args:
            organization: Organization model instance
            
        Returns:
            Country instance or None
        """
        if not organization or not hasattr(organization, 'home_country'):
            return None
        try:
            return cls.objects.get(alpha_3=organization.home_country)
        except cls.DoesNotExist:
            return None


# ============================================================================
# NOTES ON DOMESTIC VS INTERNATIONAL TRAVEL
# ============================================================================
"""
Domestic vs International is determined by Organization.home_country, not stored in Country model.

Example usage in queries:
    
    # Get domestic bookings for an organization
    domestic_bookings = Booking.objects.filter(
        organization=org,
        # Assuming Organization has home_country field
        air_booking__origin_country=org.home_country,
        air_booking__destination_country=org.home_country
    )
    
    # In API/views:
    def is_domestic_travel(booking, organization):
        '''Check if booking is domestic based on org's home country'''
        home_country = organization.home_country  # e.g., 'AUS' or 'NZL'
        
        if hasattr(booking, 'air_details'):
            # For air travel, both origin and destination must be in home country
            return (booking.air_details.origin_country == home_country and 
                    booking.air_details.destination_country == home_country)
        
        elif hasattr(booking, 'accommodation_details'):
            # For accommodation, hotel must be in home country
            return booking.accommodation_details.country == home_country
        
        elif hasattr(booking, 'car_hire_details'):
            # For car hire, rental must be in home country
            return booking.car_hire_details.country == home_country
        
        return False

Future Enhancement: Add home_country to Organization model
    
    # In apps/organizations/models.py:
    class Organization(models.Model):
        ...
        home_country = models.ForeignKey(
            'reference_data.Country',
            on_delete=models.PROTECT,
            related_name='home_organizations',
            to_field='alpha_3',
            help_text="Organization's home country for domestic/international classification"
        )
"""

# ============================================================================
# SUPPLIER MODELS
# ============================================================================

class HotelChain(models.Model):
    """Hotel chain/brand reference data"""
    SUPPLIER_TIERS = [
        ('PREFERRED', 'Preferred Supplier'),
        ('APPROVED', 'Approved Supplier'),
        ('STANDARD', 'Standard Supplier'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    alternative_names = models.JSONField(default=list, blank=True)  # ["Hilton", "Hilton Hotels", "Hilton Worldwide"]
    website = models.URLField(blank=True)
    
    # Preferred supplier tracking (for compliance)
    is_preferred = models.BooleanField(default=False)
    tier = models.CharField(max_length=20, choices=SUPPLIER_TIERS, blank=True)
    
    # Corporate rates
    has_corporate_rate = models.BooleanField(default=False)
    corporate_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Contact information
    account_manager_name = models.CharField(max_length=200, blank=True)
    account_manager_email = models.EmailField(blank=True)
    account_manager_phone = models.CharField(max_length=20, blank=True)
    
    # Contract details
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hotel_chains'
        ordering = ['name']
        verbose_name_plural = 'Hotel Chains'
    
    def __str__(self):
        return self.name


class CarRentalCompany(models.Model):
    """Car rental company reference data"""
    SUPPLIER_TIERS = [
        ('PREFERRED', 'Preferred Supplier'),
        ('APPROVED', 'Approved Supplier'),
        ('STANDARD', 'Standard Supplier'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    alternative_names = models.JSONField(default=list, blank=True)  # ["Hertz", "Hertz Rent A Car"]
    website = models.URLField(blank=True)
    
    # Preferred supplier tracking
    is_preferred = models.BooleanField(default=False)
    tier = models.CharField(max_length=20, choices=SUPPLIER_TIERS, blank=True)
    
    # Corporate rates
    has_corporate_rate = models.BooleanField(default=False)
    corporate_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Contact information
    account_manager_name = models.CharField(max_length=200, blank=True)
    account_manager_email = models.EmailField(blank=True)
    account_manager_phone = models.CharField(max_length=20, blank=True)
    
    # Contract details
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'car_rental_companies'
        ordering = ['name']
        verbose_name_plural = 'Car Rental Companies'
    
    def __str__(self):
        return self.name