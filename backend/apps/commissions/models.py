from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.organizations.models import Organization
from apps.bookings.models import Booking
import uuid


class Commission(models.Model):
    """Track commissions earned from suppliers on bookings"""
    
    PRODUCT_TYPES = [
        ('AIR', 'Air Travel'),
        ('HOTEL', 'Accommodation'),
        ('CAR', 'Car Hire'),
        ('CRUISE', 'Cruise'),
        ('INSURANCE', 'Travel Insurance'),
        ('VISA', 'Visa Services'),
        ('TOUR', 'Tours & Activities'),
        ('RAIL', 'Rail Travel'),
        ('PACKAGE', 'Package/Wholesale'),
        ('OTHER', 'Other Services'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='commissions',
        help_text="Travel agent organization earning the commission"
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='commissions'
    )
    
    # Product Type
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    
    # Supplier Information (from import data)
    supplier_name = models.CharField(
        max_length=200,
        help_text="Airline, hotel chain, car rental company, etc."
    )
    supplier_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Supplier's booking/confirmation reference for commission tracking"
    )
    
    # Commission Amount (from import - already calculated by supplier)
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Commission amount earned (from supplier)"
    )
    currency = models.CharField(max_length=3, default='AUD')
    
    # Converted to base currency (if different)
    commission_amount_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Commission in organization's base currency"
    )
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    exchange_rate_date = models.DateField(null=True, blank=True)
    
    # Optional: Store the booking amount for analysis
    booking_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Booking amount (for commission % analysis)"
    )
    
    # Date earned (typically the booking date)
    earned_date = models.DateField(help_text="Date commission was earned")
    
    # Period Tracking (for reconciliation with supplier statements)
    commission_period = models.CharField(
        max_length=20,
        blank=True,
        help_text="Commission period, e.g., '2025-10' for October 2025"
    )
    
    # Import tracking
    import_batch = models.ForeignKey(
        'imports.ImportBatch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='commissions'
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'commissions'
        indexes = [
            models.Index(fields=['organization', 'earned_date']),
            models.Index(fields=['booking']),
            models.Index(fields=['product_type', 'supplier_name']),
            models.Index(fields=['commission_period']),
        ]
        ordering = ['-earned_date']
    
    def __str__(self):
        return f"{self.supplier_name} - ${self.commission_amount} ({self.product_type})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate commission_period from earned_date
        if self.earned_date and not self.commission_period:
            self.commission_period = self.earned_date.strftime('%Y-%m')
        super().save(*args, **kwargs)
    
    @property
    def commission_rate(self):
        """Calculate commission rate as percentage (for analysis)"""
        if self.booking_amount and self.booking_amount > 0:
            return (self.commission_amount / self.booking_amount * 100).quantize(Decimal('0.01'))
        return None