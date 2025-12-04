from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.organizations.models import Organization
from apps.users.models import User
import uuid


class FiscalYear(models.Model):
    """Fiscal year configuration for organizations"""
    FISCAL_YEAR_TYPES = [
        ('AUS', 'Australia (1 Jul - 30 Jun)'),
        ('UK', 'United Kingdom (1 Apr - 31 Mar)'),
        ('USA', 'United States (1 Jan - 31 Dec)'),
        ('CALENDAR', 'Calendar Year (1 Jan - 31 Dec)'),
        ('CUSTOM', 'Custom Period'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='fiscal_years')
    
    # Fiscal year definition
    fiscal_year_type = models.CharField(max_length=20, choices=FISCAL_YEAR_TYPES)
    year_label = models.CharField(max_length=20)  # e.g., "FY2024", "FY2024-25"
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Status
    is_active = models.BooleanField(default=True)
    is_current = models.BooleanField(default=False)  # Only one current FY per organization
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fiscal_years'
        indexes = [
            models.Index(fields=['organization', 'is_current']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        unique_together = [['organization', 'year_label']]
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.organization.name} - {self.year_label}"


class Budget(models.Model):
    """Annual budget allocations by organizational node (cost center, business unit, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='budgets')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='budgets')

    # Organizational hierarchy node
    organizational_node = models.ForeignKey(
        'organizations.OrganizationalNode',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='budgets',
        help_text="Link to organizational hierarchy node (cost center, business unit, division, etc.)"
    )

    # Cost center (deprecated - kept for backward compatibility)
    cost_center = models.CharField(
        max_length=100,
        blank=True,
        help_text="DEPRECATED: Use organizational_node instead. Kept for backward compatibility."
    )
    cost_center_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="DEPRECATED: Use organizational_node.name instead. Kept for backward compatibility."
    )

    # Budget allocation by category
    total_budget = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    air_budget = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    accommodation_budget = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    car_hire_budget = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    other_budget = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )

    # Currency
    currency = models.CharField(max_length=3, default='AUD')

    # Carbon emissions budget (in tonnes of CO2)
    carbon_budget = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Annual carbon emissions budget in tonnes of CO2"
    )

    # Alert thresholds (percentage)
    warning_threshold = models.IntegerField(default=80)  # Alert at 80% spent
    critical_threshold = models.IntegerField(default=95)  # Critical alert at 95%
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='budgets_created'
    )
    
    class Meta:
        db_table = 'budgets'
        indexes = [
            models.Index(fields=['organization', 'fiscal_year', 'cost_center']),
            models.Index(fields=['organizational_node']),
            models.Index(fields=['fiscal_year', 'is_active']),
        ]
        # Note: Removed unique_together for cost_center since we're migrating to organizational_node
        # Will add new constraint: unique_together = [['organization', 'fiscal_year', 'organizational_node']]
        # after data migration is complete

    def __str__(self):
        if self.organizational_node:
            return f"{self.organization.name} - {self.organizational_node.name} ({self.fiscal_year.year_label})"
        return f"{self.organization.name} - {self.cost_center} ({self.fiscal_year.year_label})"

    @property
    def node_name(self):
        """Get the display name for this budget's organizational node"""
        if self.organizational_node:
            return self.organizational_node.name
        return self.cost_center_name or self.cost_center

    @property
    def node_code(self):
        """Get the code for this budget's organizational node"""
        if self.organizational_node:
            return self.organizational_node.code
        return self.cost_center

    def save(self, *args, **kwargs):
        """Auto-populate deprecated cost_center fields from organizational_node"""
        if self.organizational_node:
            # Sync deprecated fields with organizational_node for backward compatibility
            self.cost_center = self.organizational_node.code or ''
            self.cost_center_name = self.organizational_node.name or ''
        super().save(*args, **kwargs)

    def get_total_spent(self):
        """Calculate total spent against this budget"""
        from django.db.models import Sum, Q
        from apps.bookings.models import Booking

        # Build filter based on organizational_node or cost_center
        if self.organizational_node:
            # Match by organizational_node OR cost_center (for travellers not yet migrated)
            traveller_filter = Q(traveller__organizational_node=self.organizational_node)
            # Also match travellers with cost_center matching the org node's code
            if self.organizational_node.code:
                traveller_filter |= Q(traveller__cost_center=self.organizational_node.code)
        else:
            # Fall back to cost_center for backward compatibility
            traveller_filter = Q(traveller__cost_center=self.cost_center)

        bookings = Booking.objects.filter(
            traveller_filter,
            organization=self.organization,
            travel_date__gte=self.fiscal_year.start_date,
            travel_date__lte=self.fiscal_year.end_date,
            status='CONFIRMED'
        ).aggregate(total=Sum('total_amount'))

        return bookings['total'] or Decimal('0.00')

    def get_spent_by_category(self):
        """Calculate spent amount by booking category"""
        from django.db.models import Sum, Q
        from apps.bookings.models import Booking

        # Build filter based on organizational_node or cost_center
        if self.organizational_node:
            # Match by organizational_node OR cost_center (for travellers not yet migrated)
            traveller_filter = Q(traveller__organizational_node=self.organizational_node)
            # Also match travellers with cost_center matching the org node's code
            if self.organizational_node.code:
                traveller_filter |= Q(traveller__cost_center=self.organizational_node.code)
        else:
            # Fall back to cost_center for backward compatibility
            traveller_filter = Q(traveller__cost_center=self.cost_center)

        base_query = Booking.objects.filter(
            traveller_filter,
            organization=self.organization,
            travel_date__gte=self.fiscal_year.start_date,
            travel_date__lte=self.fiscal_year.end_date,
            status='CONFIRMED'
        )

        return {
            'air': base_query.filter(booking_type='AIR').aggregate(
                total=Sum('total_amount'))['total'] or Decimal('0.00'),
            'accommodation': base_query.filter(booking_type='HOTEL').aggregate(
                total=Sum('total_amount'))['total'] or Decimal('0.00'),
            'car_hire': base_query.filter(booking_type='CAR').aggregate(
                total=Sum('total_amount'))['total'] or Decimal('0.00'),
            'other': base_query.filter(booking_type='OTHER').aggregate(
                total=Sum('total_amount'))['total'] or Decimal('0.00'),
        }
    
    def get_budget_status(self):
        """Calculate budget utilization percentage and status"""
        total_spent = self.get_total_spent()
        if self.total_budget == 0:
            return {'percentage': 0, 'status': 'OK'}
        
        percentage = (total_spent / self.total_budget) * 100
        
        if percentage >= self.critical_threshold:
            status = 'CRITICAL'
        elif percentage >= self.warning_threshold:
            status = 'WARNING'
        else:
            status = 'OK'
        
        return {
            'percentage': round(percentage, 2),
            'status': status,
            'spent': total_spent,
            'remaining': self.total_budget - total_spent
        }


class BudgetAlert(models.Model):
    """Track budget threshold alerts"""
    ALERT_TYPES = [
        ('WARNING', 'Warning Threshold Reached'),
        ('CRITICAL', 'Critical Threshold Reached'),
        ('EXCEEDED', 'Budget Exceeded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='alerts')
    
    # Alert details
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    percentage_used = models.DecimalField(max_digits=5, decimal_places=2)
    amount_spent = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Notification
    notified_users = models.ManyToManyField(User, related_name='budget_alerts_received')
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='budget_alerts_acknowledged'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'budget_alerts'
        indexes = [
            models.Index(fields=['budget', 'created_at']),
            models.Index(fields=['alert_type', 'is_acknowledged']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.budget.cost_center} - {self.alert_type} ({self.percentage_used}%)"