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
    
    # Booking reference
    booking_reference = models.CharField(max_length=100)
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
            models.Index(fields=['booking_reference']),
            models.Index(fields=['booking_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.booking_reference} - {self.traveller}"
