# backend/apps/organizations/models.py

from django.db import models
import uuid


class Organization(models.Model):
    """Travel agent organizations and customer companies"""
    ORG_TYPES = [
        ('AGENT', 'Travel Agent'),
        ('CUSTOMER', 'Customer Organization'),
    ]

    SUBSCRIPTION_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('TRIAL', 'Trial Period'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    org_type = models.CharField(max_length=20, choices=ORG_TYPES)
    code = models.CharField(max_length=50, unique=True)
    
    # Contact & billing
    contact_name = models.CharField(max_length=200, blank=True, verbose_name="Contact Name")
    contact_position = models.CharField(max_length=100, blank=True, verbose_name="Contact Position")
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    business_number = models.CharField(max_length=50, blank=True, help_text="ABN, ACN, or similar business registration number")
    
    # Accounts Payable contact
    ap_contact_name = models.CharField(max_length=200, blank=True, verbose_name="AP Contact Name")
    ap_contact_email = models.EmailField(blank=True, verbose_name="AP Contact Email")
    ap_contact_phone = models.CharField(max_length=20, blank=True, verbose_name="AP Contact Phone")

    # Currency settings
    base_currency = models.CharField(max_length=3, default='AUD')
    
    # ============================================================================
    # NEW FIELD: home_country for domestic/international determination
    # ============================================================================
    home_country = models.CharField(
        max_length=3,
        default='AUS',
        help_text="ISO 3166-1 alpha-3 code for organization's home country (e.g., AUS, NZL, SGP)"
    )
    
    # Subscription Status
    is_active = models.BooleanField(default=True)
    subscription_status = models.CharField(
        max_length=20, 
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='ACTIVE'
    )
    subscription_start = models.DateField(null=True, blank=True)
    subscription_end = models.DateField(null=True, blank=True)
    
    # For customer organizations - link to their travel agent
    travel_agent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='customers'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['org_type', 'is_active']),
            models.Index(fields=['home_country']),  # Index for domestic/international queries
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    # ============================================================================
    # NEW HELPER METHODS for domestic/international determination
    # ============================================================================
    
    def is_domestic_travel(self, country_code):
        """
        Determine if travel to a country is domestic for this organization.
        
        Args:
            country_code: ISO 3166-1 alpha-3 code (e.g., 'AUS', 'NZL')
            
        Returns:
            bool: True if travel is domestic
            
        Example:
            >>> org = Organization.objects.get(name='TechCorp', home_country='AUS')
            >>> org.is_domestic_travel('AUS')
            True
            >>> org.is_domestic_travel('NZL')
            False
        """
        return self.home_country == country_code
    
    def get_home_country_display(self):
        """
        Get the full country name for the home country.
        
        Returns:
            str: Country common name or alpha_3 code if country not found
            
        Example:
            >>> org = Organization.objects.get(name='TechCorp', home_country='AUS')
            >>> org.get_home_country_display()
            'Australia'
        """
        try:
            from apps.reference_data.models import Country
            country = Country.objects.get(alpha_3=self.home_country)
            return country.common_name
        except:
            return self.home_country