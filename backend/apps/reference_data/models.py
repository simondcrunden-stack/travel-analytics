# apps/reference_data/models.py
# Session 34: Enhanced with improved CurrencyExchangeRate.get_rate() method

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger(__name__)


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
    """
    Store daily exchange rates for currency conversion
    
    Session 34: Enhanced get_rate() method with intelligent fallback
    """
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
    
    # ==================================================================
    # SESSION 34 ENHANCEMENT: Intelligent Rate Lookup with Fallbacks
    # ==================================================================
    
    @classmethod
    def get_rate(cls, from_currency, to_currency, date):
        """
        Get exchange rate for a specific date with intelligent fallback
        
        Args:
            from_currency (str): Source currency code (e.g., 'USD')
            to_currency (str): Target currency code (e.g., 'AUD')
            date (date): Date for which to get the rate
            
        Returns:
            Decimal: Exchange rate, or None if not found
            
        Logic:
        1. If same currency, return 1.0
        2. Look for exact date match (from → to)
        3. If not found, look for most recent rate before this date
        4. If not found, look for reverse rate (to → from) and invert
        5. If still not found, log warning and return None
        
        Example:
            >>> rate = CurrencyExchangeRate.get_rate('USD', 'AUD', date(2024, 1, 15))
            >>> print(rate)  # 1.52
        """
        # Same currency, no conversion needed
        if from_currency == to_currency:
            return Decimal('1.0')
        
        try:
            # Try to find exact date match first
            direct_rate = cls.objects.filter(
                from_currency=from_currency,
                to_currency=to_currency,
                rate_date=date
            ).first()
            
            if direct_rate:
                logger.debug(
                    f"Found exact rate {from_currency}→{to_currency} "
                    f"on {direct_rate.rate_date}: {direct_rate.exchange_rate}"
                )
                return Decimal(str(direct_rate.exchange_rate))
            
            # Try to find most recent rate before this date
            direct_rate = cls.objects.filter(
                from_currency=from_currency,
                to_currency=to_currency,
                rate_date__lte=date
            ).order_by('-rate_date').first()
            
            if direct_rate:
                logger.debug(
                    f"Found recent rate {from_currency}→{to_currency} "
                    f"on {direct_rate.rate_date}: {direct_rate.exchange_rate}"
                )
                return Decimal(str(direct_rate.exchange_rate))
            
        except Exception as e:
            logger.error(f"Error looking up direct rate: {e}")
        
        try:
            # Try to find reverse rate (to → from) and invert it
            # First try exact date
            reverse_rate = cls.objects.filter(
                from_currency=to_currency,
                to_currency=from_currency,
                rate_date=date
            ).first()
            
            if not reverse_rate:
                # Try most recent before date
                reverse_rate = cls.objects.filter(
                    from_currency=to_currency,
                    to_currency=from_currency,
                    rate_date__lte=date
                ).order_by('-rate_date').first()
            
            if reverse_rate and reverse_rate.exchange_rate:
                inverted_rate = Decimal('1.0') / Decimal(str(reverse_rate.exchange_rate))
                logger.debug(
                    f"Found reverse rate {to_currency}→{from_currency} "
                    f"on {reverse_rate.rate_date}: {reverse_rate.exchange_rate}, "
                    f"inverted to: {inverted_rate}"
                )
                return inverted_rate
            
        except Exception as e:
            logger.error(f"Error looking up reverse rate: {e}")
        
        # No rate found - log warning and return None
        logger.warning(
            f"No exchange rate found for {from_currency} → {to_currency} "
            f"on or before {date}. "
            f"Please add exchange rate data for accurate conversions."
        )
        return None
    
    @staticmethod
    def convert_amount(amount, from_currency, to_currency, date):
        """
        Convert an amount from one currency to another
        
        Args:
            amount (Decimal): Amount to convert
            from_currency (str): Source currency
            to_currency (str): Target currency
            date (date): Date for exchange rate
            
        Returns:
            Decimal: Converted amount, or None if rate not found
        """
        if from_currency == to_currency:
            return amount
        
        rate = CurrencyExchangeRate.get_rate(from_currency, to_currency, date)
        if rate:
            return amount * rate
        
        return None

# ==================================================================
# COUNTRY MODELS - ADDED BACK INTO THE CODE IN SESSION 35
# ==================================================================

class Country(models.Model):
    """
    Country reference data using ISO 3166-1 standard
    
    Multi-tenant design: Domestic status calculated dynamically
    """
    
    # ISO 3166-1 codes
    alpha_3 = models.CharField(max_length=3, primary_key=True)
    alpha_2 = models.CharField(max_length=2, unique=True)
    numeric_code = models.CharField(max_length=3, blank=True)
    
    # Names
    name = models.CharField(max_length=200)
    common_name = models.CharField(max_length=200, blank=True)
    
    # Regional classification
    region = models.CharField(max_length=100, blank=True)
    subregion = models.CharField(max_length=100, blank=True)
    
    # Travel-related info
    currency_code = models.CharField(max_length=3, blank=True)
    phone_prefix = models.CharField(max_length=10, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'countries'
        verbose_name_plural = 'Countries'
        ordering = ['name']
        indexes = [
            models.Index(fields=['region']),
            models.Index(fields=['subregion']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.alpha_3})"
    
    def is_domestic_for_organization(self, organization):
        """Check if this country is domestic for the given organization"""
        return self.alpha_3 == organization.home_country

# ============================================================================
# SUPPLIER MODELS (if you have these)
# ============================================================================

class HotelChain(models.Model):
    """Hotel chain/brand reference data"""
    SUPPLIER_TIERS = [
        ('PREFERRED', 'Preferred Supplier'),
        ('APPROVED', 'Approved Supplier'),
        ('STANDARD', 'Standard Supplier'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic info
    name = models.CharField(max_length=200)
    alternative_names = models.TextField(
        blank=True,
        help_text="Alternative names or abbreviations (comma-separated)"
    )
    website = models.URLField(blank=True)
    
    # Supplier status
    is_preferred = models.BooleanField(default=False)
    tier = models.CharField(max_length=20, choices=SUPPLIER_TIERS, default='STANDARD')
    is_active = models.BooleanField(default=True)
    
    # Corporate rates
    has_corporate_rate = models.BooleanField(default=False)
    corporate_discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average discount percentage off BAR (Best Available Rate)"
    )
    
    # Account manager
    account_manager_name = models.CharField(max_length=200, blank=True)
    account_manager_email = models.EmailField(blank=True)
    account_manager_phone = models.CharField(max_length=50, blank=True)
    
    # Contract
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hotel_chains'
        ordering = ['name']
    
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
    
    # Basic info
    name = models.CharField(max_length=200)
    alternative_names = models.TextField(
        blank=True,
        help_text="Alternative names or abbreviations (comma-separated)"
    )
    website = models.URLField(blank=True)
    
    # Supplier status
    is_preferred = models.BooleanField(default=False)
    tier = models.CharField(max_length=20, choices=SUPPLIER_TIERS, default='STANDARD')
    is_active = models.BooleanField(default=True)
    
    # Corporate rates
    has_corporate_rate = models.BooleanField(default=False)
    corporate_discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average discount percentage"
    )
    
    # Account manager
    account_manager_name = models.CharField(max_length=200, blank=True)
    account_manager_email = models.EmailField(blank=True)
    account_manager_phone = models.CharField(max_length=50, blank=True)
    
    # Contract
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'car_rental_companies'
        ordering = ['name']
    
    def __str__(self):
        return self.name