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


class OrganizationalNode(models.Model):
    """
    Hierarchical organizational structure (departments, divisions, cost centers, etc.)
    for customer organizations. Uses adjacency list model for tree structure.
    """
    NODE_TYPES = [
        ('COST_CENTER', 'Cost Center'),
        ('BUSINESS_UNIT', 'Business Unit'),
        ('REGION', 'Region'),
        ('DEPARTMENT', 'Department'),
        ('DIVISION', 'Division'),
        ('GROUP', 'Group'),
        ('OTHER', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='organizational_nodes',
        help_text="The organization this node belongs to"
    )

    # Node identification
    name = models.CharField(max_length=200, help_text="Name of the organizational unit")
    code = models.CharField(max_length=50, help_text="Unique code within organization")
    node_type = models.CharField(max_length=20, choices=NODE_TYPES, default='DEPARTMENT')

    # Tree structure (adjacency list)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent node in the hierarchy"
    )

    # Cached path for efficient queries (format: /root_code/parent_code/node_code/)
    path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Materialized path for efficient tree queries"
    )

    # Display order within siblings
    display_order = models.IntegerField(default=0)

    # Status
    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organizational_nodes'
        unique_together = [('organization', 'code')]
        indexes = [
            models.Index(fields=['organization', 'parent']),
            models.Index(fields=['organization', 'node_type']),
            models.Index(fields=['path']),
        ]
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.organization.code} - {self.name} ({self.code})"

    def save(self, *args, **kwargs):
        """Override save to update the materialized path"""
        # Update path on save
        if self.parent:
            self.path = f"{self.parent.path}{self.code}/"
        else:
            self.path = f"/{self.code}/"

        super().save(*args, **kwargs)

        # Update children paths if this node's path changed
        if hasattr(self, '_path_changed'):
            for child in self.children.all():
                child.save()

    @property
    def full_path(self):
        """Get human-readable full path"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    @property
    def depth(self):
        """Calculate depth in tree (root = 0)"""
        return self.path.count('/') - 2 if self.path else 0

    def get_ancestors(self):
        """Get all ancestors from root to parent"""
        if not self.parent:
            return OrganizationalNode.objects.none()

        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent

        return OrganizationalNode.objects.filter(id__in=[a.id for a in ancestors])

    def get_descendants(self, include_self=False):
        """Get all descendants (children, grandchildren, etc.)"""
        queryset = OrganizationalNode.objects.filter(
            organization=self.organization,
            path__startswith=self.path
        ).exclude(id=self.id)

        if include_self:
            queryset = queryset | OrganizationalNode.objects.filter(id=self.id)

        return queryset

    def get_siblings(self, include_self=False):
        """Get siblings (nodes with same parent)"""
        queryset = OrganizationalNode.objects.filter(
            organization=self.organization,
            parent=self.parent
        )

        if not include_self:
            queryset = queryset.exclude(id=self.id)

        return queryset

    def can_delete(self):
        """Check if node can be deleted (no children, no references)"""
        has_children = self.children.exists()
        has_travellers = hasattr(self, 'travellers') and self.travellers.exists()
        has_budgets = hasattr(self, 'budgets') and self.budgets.exists()

        return not (has_children or has_travellers or has_budgets)

    def get_traveller_count(self):
        """Count travellers associated with this node"""
        if hasattr(self, 'travellers'):
            return self.travellers.count()
        return 0

    def get_budget_count(self):
        """Count budgets associated with this node"""
        if hasattr(self, 'budgets'):
            return self.budgets.count()
        return 0