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