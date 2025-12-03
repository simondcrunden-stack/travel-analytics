# backend/apps/organizations/models.py

from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
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


class OrganizationalNode(MPTTModel):
    """
    Flexible organizational hierarchy using MPTT (Modified Preorder Tree Traversal).

    Supports variable-depth organizational structures:
    - Cost centers (leaves)
    - Business units, regions, departments, divisions (intermediate nodes)
    - Custom node types defined by organization

    Examples:
        Sales structure (deep):
            Sales-ASPAC (Division)
            └── Sales-Australia (National)
                └── VIC-Sales (Region)
                    ├── VIC-001 (Cost Center)
                    ├── VIC-002 (Cost Center)
                    └── VIC-003 (Cost Center)

        Marketing structure (flat):
            ASPAC-Marketing (Division)
            ├── National-Marketing (National)
            │   ├── VIC-Marketing (Cost Center)
            │   ├── NSW-Marketing (Cost Center)
            │   └── QLD-Marketing (Cost Center)
    """

    NODE_TYPE_CHOICES = [
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
        help_text="Organization this node belongs to"
    )

    # Tree structure
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent node in the hierarchy (null for root nodes)"
    )

    # Node identification
    code = models.CharField(
        max_length=100,
        help_text="Unique code for this node (e.g., 'VIC-001', 'Sales-ASPAC')"
    )
    name = models.CharField(
        max_length=200,
        help_text="Display name for this node"
    )
    node_type = models.CharField(
        max_length=20,
        choices=NODE_TYPE_CHOICES,
        default='COST_CENTER',
        help_text="Type of organizational unit"
    )

    # Node properties
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this node is currently active"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of this organizational unit"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['code']

    class Meta:
        db_table = 'organizational_nodes'
        unique_together = [['organization', 'code']]
        indexes = [
            models.Index(fields=['organization', 'code'], name='organizatio_organiz_6b29ba_idx'),
            models.Index(fields=['organization', 'node_type'], name='organizatio_organiz_0f618c_idx'),
            models.Index(fields=['organization', 'is_active'], name='organizatio_organiz_b76c4c_idx'),
        ]
        verbose_name = 'Organizational Node'
        verbose_name_plural = 'Organizational Nodes'

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_full_path(self):
        """
        Get the full path from root to this node.

        Returns:
            str: Path like "Sales-ASPAC > Sales-Australia > VIC-Sales > VIC-001"
        """
        ancestors = self.get_ancestors(include_self=True)
        return " > ".join([node.name for node in ancestors])

    def get_descendants_count(self):
        """
        Get count of all descendants (children, grandchildren, etc.).

        Returns:
            int: Number of descendants
        """
        return self.get_descendant_count()

    def get_traveller_count(self):
        """
        Get count of travellers associated with this node.

        Returns:
            int: Number of travellers
        """
        try:
            from apps.bookings.models import Traveller
            return Traveller.objects.filter(organizational_node=self).count()
        except:
            return 0

    def get_budget_count(self):
        """
        Get count of budgets associated with this node.

        Returns:
            int: Number of budgets
        """
        try:
            from apps.budgets.models import Budget
            return Budget.objects.filter(organizational_node=self).count()
        except:
            return 0

    def can_be_merged_with(self, other_node):
        """
        Check if this node can be merged with another node.

        Rules:
        - Must be in same organization
        - Must be same node type
        - Cannot merge node with itself
        - Cannot merge if it would create circular reference

        Args:
            other_node: OrganizationalNode to merge with

        Returns:
            bool: True if merge is allowed
        """
        if self.id == other_node.id:
            return False
        if self.organization_id != other_node.organization_id:
            return False
        if self.node_type != other_node.node_type:
            return False
        # Check if other_node is an ancestor of self (would create circular ref)
        if other_node in self.get_ancestors():
            return False
        return True

    def merge_into(self, target_node):
        """
        Merge this node into another node.

        Process:
        1. Move all children to target node
        2. Update all travellers pointing to this node
        3. Update all budgets pointing to this node
        4. Mark this node as inactive or delete it

        Args:
            target_node: OrganizationalNode to merge into

        Returns:
            bool: True if merge successful

        Raises:
            ValueError: If merge not allowed
        """
        if not self.can_be_merged_with(target_node):
            raise ValueError(f"Cannot merge {self} into {target_node}")

        # Move children to target
        for child in self.get_children():
            child.move_to(target_node, 'last-child')
            child.save()

        # Update travellers
        from apps.bookings.models import Traveller
        Traveller.objects.filter(organizational_node=self).update(
            organizational_node=target_node
        )

        # Update budgets
        from apps.budgets.models import Budget
        Budget.objects.filter(organizational_node=self).update(
            organizational_node=target_node
        )

        # Mark as inactive
        self.is_active = False
        self.code = f"{self.code}_MERGED_{uuid.uuid4().hex[:8]}"  # Prevent unique constraint issues
        self.save()

        return True