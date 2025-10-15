from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from math import radians, sin, cos, sqrt, atan2


class ComplianceRule(models.Model):
    """Define travel policy compliance rules for organizations"""
    RULE_TYPES = [
        ('LOWEST_FARE', 'Lowest Fare Selection'),
        ('ADVANCE_BOOKING', 'Advance Booking Period'),
        ('TRAVEL_CLASS', 'Class of Travel'),
        ('PREFERRED_SUPPLIER', 'Preferred Supplier'),
        ('BOOKING_CHANNEL', 'Booking Channel (Online vs Offline)'),
        ('TRIP_DURATION', 'Trip Duration Limits'),
        ('DAILY_RATE', 'Daily Rate Limits'),
        ('CUSTOM', 'Custom Rule'),
    ]
    
    PRODUCT_TYPES = [
        ('AIR', 'Air Travel'),
        ('HOTEL', 'Accommodation'),
        ('CAR', 'Car Hire'),
        ('ALL', 'All Products'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, 
                                     related_name='compliance_rules')
    
    # Rule definition
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES)
    rule_name = models.CharField(max_length=200)
    rule_description = models.TextField(blank=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    
    # Rule parameters (stored as JSON for flexibility)
    rule_parameters = models.JSONField(default=dict, blank=True)
    # Example for LOWEST_FARE: {"tolerance_percentage": 10, "tolerance_amount": 50}
    # Example for ADVANCE_BOOKING: {"minimum_days": 7, "applies_to": "international"}
    # Example for TRAVEL_CLASS: {"max_class": "ECONOMY", "exceptions": ["CEO", "Board"]}
    
    # Status
    is_active = models.BooleanField(default=True)
    is_enforced = models.BooleanField(default=True)  # If False, violations logged but allowed
    
    # Effective dates
    effective_from = models.DateField()
    effective_until = models.DateField(null=True, blank=True)
    
    # Priority (for when multiple rules apply)
    priority = models.IntegerField(default=100)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True,
                                   related_name='compliance_rules_created')
    
    class Meta:
        db_table = 'compliance_rules'
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['rule_type', 'product_type']),
        ]
        ordering = ['priority', 'rule_name']
    
    def __str__(self):
        return f"{self.organization.name} - {self.rule_name}"


class ComplianceViolation(models.Model):
    """Track policy violations for bookings"""
    VIOLATION_SEVERITY = [
        ('INFO', 'Informational'),
        ('WARNING', 'Warning'),
        ('BREACH', 'Policy Breach'),
        ('CRITICAL', 'Critical Violation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='violations')
    compliance_rule = models.ForeignKey(ComplianceRule, on_delete=models.CASCADE, 
                                        related_name='violations', null=True, blank=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE,
                                     related_name='compliance_violations')
    traveller = models.ForeignKey('bookings.Traveller', on_delete=models.CASCADE, related_name='violations')
    
    # Violation details
    violation_type = models.CharField(max_length=30)  # Matches ComplianceRule.RULE_TYPES
    violation_description = models.TextField()
    severity = models.CharField(max_length=20, choices=VIOLATION_SEVERITY, default='WARNING')
    
    # Financial impact (if applicable)
    expected_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    variance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='AUD')
    
    # Detection
    detected_at = models.DateTimeField(auto_now_add=True)
    detected_by = models.CharField(max_length=50, default='SYSTEM')  # SYSTEM, MANUAL, IMPORT
    
    # Resolution
    is_waived = models.BooleanField(default=False)
    waived_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='violations_waived')
    waived_at = models.DateTimeField(null=True, blank=True)
    waiver_reason = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_violations'
        indexes = [
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['booking']),
            models.Index(fields=['violation_type', 'severity']),
            models.Index(fields=['is_waived']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.traveller} - {self.violation_type} ({self.severity})"


class ComplianceProcessingLog(models.Model):
    """Log compliance processing runs for audit and troubleshooting"""
    PROCESSING_TYPES = [
        ('IMPORT', 'Import Time Processing'),
        ('BATCH', 'Batch Reprocessing'),
        ('MANUAL', 'Manual Update'),
    ]
    
    STATUS_CHOICES = [
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE,
                                     related_name='compliance_logs', null=True, blank=True)
    
    # Processing details
    processing_type = models.CharField(max_length=20, choices=PROCESSING_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RUNNING')
    
    # Scope
    start_date = models.DateField(null=True, blank=True)  # For date range reprocessing
    end_date = models.DateField(null=True, blank=True)
    booking_type = models.CharField(max_length=20, blank=True)  # AIR, HOTEL, CAR, or blank for all
    
    # Statistics
    bookings_processed = models.IntegerField(default=0)
    violations_detected = models.IntegerField(default=0)
    violations_resolved = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    # User tracking
    initiated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='compliance_runs_initiated')
    
    class Meta:
        db_table = 'compliance_processing_logs'
        indexes = [
            models.Index(fields=['organization', 'started_at']),
            models.Index(fields=['status', 'processing_type']),
        ]
        ordering = ['-started_at']
    
    def __str__(self):
        org_name = self.organization.name if self.organization else "All Organizations"
        return f"{org_name} - {self.processing_type} ({self.status})"


class HighRiskDestination(models.Model):
    """Define high risk countries and regions for travel tracking"""
    RISK_LEVELS = [
        ('EXTREME', 'Extreme Risk - Do Not Travel'),
        ('HIGH', 'High Risk - Reconsider Travel'),
        ('MODERATE', 'Moderate Risk - Exercise Caution'),
        ('LOW', 'Low Risk - Normal Precautions'),
    ]
    
    DESTINATION_TYPES = [
        ('COUNTRY', 'Entire Country'),
        ('REGION', 'Specific Region/State'),
        ('CITY', 'Specific City'),
        ('RADIUS', 'Radius Around Location'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, 
                                     related_name='high_risk_destinations')
    
    # Destination identification
    destination_type = models.CharField(max_length=20, choices=DESTINATION_TYPES)
    country_code = models.CharField(max_length=3)  # ISO 3166-1 alpha-3
    country_name = models.CharField(max_length=100)
    
    # For regions/cities
    region_name = models.CharField(max_length=200, blank=True)
    city_name = models.CharField(max_length=100, blank=True)
    
    # For radius-based tracking
    center_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    center_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_km = models.IntegerField(null=True, blank=True)  # Radius in kilometers
    
    # Risk assessment
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    risk_description = models.TextField(blank=True)
    
    # Advisory details
    advisory_source = models.CharField(max_length=200, blank=True)  # e.g., "DFAT", "UK FCO"
    advisory_url = models.URLField(blank=True)
    advisory_date = models.DateField(null=True, blank=True)
    
    # Policy
    approval_required = models.BooleanField(default=True)
    allow_travel = models.BooleanField(default=False)  # Override to allow with approval
    
    # Notification settings
    notify_immediately = models.BooleanField(default=True)
    notification_recipients = models.ManyToManyField('users.User', related_name='risk_notifications', 
                                                     blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_until = models.DateField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True,
                                   related_name='risk_destinations_created')
    
    class Meta:
        db_table = 'high_risk_destinations'
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['country_code', 'is_active']),
            models.Index(fields=['risk_level']),
        ]
    
    def __str__(self):
        if self.destination_type == 'RADIUS':
            return f"{self.city_name or self.region_name} ({self.radius_km}km radius) - {self.risk_level}"
        elif self.destination_type == 'CITY':
            return f"{self.city_name}, {self.country_name} - {self.risk_level}"
        elif self.destination_type == 'REGION':
            return f"{self.region_name}, {self.country_name} - {self.risk_level}"
        else:
            return f"{self.country_name} - {self.risk_level}"
    
    def check_location_in_range(self, latitude, longitude):
        """Check if a location falls within this high-risk zone (for RADIUS type)"""
        if self.destination_type != 'RADIUS' or not all([
            self.center_latitude, self.center_longitude, self.radius_km
        ]):
            return False
        
        # Haversine formula to calculate distance
        R = 6371  # Earth's radius in km
        
        lat1 = radians(float(self.center_latitude))
        lon1 = radians(float(self.center_longitude))
        lat2 = radians(latitude)
        lon2 = radians(longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance <= self.radius_km


class TravelRiskAlert(models.Model):
    """Track when travelers book trips to high-risk destinations"""
    ALERT_STATUS = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
        ('CANCELLED', 'Booking Cancelled'),
        ('COMPLETED', 'Travel Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='risk_alerts')
    high_risk_destination = models.ForeignKey(HighRiskDestination, on_delete=models.CASCADE,
                                              related_name='travel_alerts')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE,
                                     related_name='travel_risk_alerts')
    traveller = models.ForeignKey('bookings.Traveller', on_delete=models.CASCADE, related_name='risk_alerts')
    
    # Alert details
    alert_status = models.CharField(max_length=20, choices=ALERT_STATUS, default='PENDING')
    risk_level_at_booking = models.CharField(max_length=20)  # Snapshot of risk level
    
    # Matched location details
    matched_location = models.CharField(max_length=200)  # City/region that triggered alert
    distance_from_center_km = models.DecimalField(max_digits=8, decimal_places=2, 
                                                   null=True, blank=True)
    
    # Approval workflow
    approval_requested_at = models.DateTimeField(auto_now_add=True)
    approval_notes = models.TextField(blank=True)
    
    approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='risk_approvals_given')
    approval_decision_at = models.DateTimeField(null=True, blank=True)
    approval_comments = models.TextField(blank=True)
    
    # Additional safety measures
    emergency_contact_verified = models.BooleanField(default=False)
    travel_insurance_confirmed = models.BooleanField(default=False)
    safety_briefing_completed = models.BooleanField(default=False)
    
    # Notifications
    traveller_notified = models.BooleanField(default=False)
    traveller_notified_at = models.DateTimeField(null=True, blank=True)
    
    admins_notified = models.BooleanField(default=False)
    admins_notified_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'travel_risk_alerts'
        indexes = [
            models.Index(fields=['organization', 'alert_status']),
            models.Index(fields=['traveller', 'alert_status']),
            models.Index(fields=['booking']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.traveller} - {self.matched_location} ({self.alert_status})"