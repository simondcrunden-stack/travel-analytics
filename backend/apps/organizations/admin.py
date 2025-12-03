from django.contrib import admin
from .models import Organization, OrganizationalNode, Budget


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'org_type', 'base_currency', 'home_country', 'is_active', 'subscription_status']
    list_filter = ['org_type', 'is_active', 'subscription_status', 'base_currency', 'home_country']
    search_fields = ['name', 'code', 'contact_email', 'contact_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'org_type', 'travel_agent')
        }),
        ('Contact & Billing', {
            'fields': ('contact_name', 'contact_position', 'contact_email', 'contact_phone', 'address', 'business_number')
        }),
        ('Accounts Payable Contact', {
            'fields': ('ap_contact_name', 'ap_contact_email', 'ap_contact_phone'),
            'description': 'Contact details for invoicing and payment processing'
        }),
        ('Financial Settings', {
            'fields': ('base_currency', 'home_country')
        }),
        ('Subscription', {
            'fields': ('is_active', 'subscription_status', 'subscription_start', 'subscription_end')
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "travel_agent":
            # Only show Travel Agent organizations in the dropdown
            kwargs["queryset"] = Organization.objects.filter(org_type='AGENT')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(OrganizationalNode)
class OrganizationalNodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'node_type', 'parent', 'level', 'is_active']
    list_filter = ['organization', 'node_type', 'is_active']
    search_fields = ['name', 'code', 'organization__name']
    ordering = ['organization', 'tree_id', 'lft']

    fieldsets = (
        ('Basic Information', {
            'fields': ('organization', 'name', 'code', 'node_type', 'description')
        }),
        ('Hierarchy', {
            'fields': ('parent',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Tree Info (Read-only)', {
            'fields': ('level', 'lft', 'rght', 'tree_id'),
            'description': 'MPTT tree structure fields (automatically managed)',
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['level', 'lft', 'rght', 'tree_id']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            # Only show nodes from the same organization
            if 'organization' in request.GET:
                kwargs["queryset"] = OrganizationalNode.objects.filter(
                    organization_id=request.GET['organization']
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = [
        'get_cost_center', 'organization', 'fiscal_year', 'budget_type',
        'amount', 'currency', 'warning_threshold', 'critical_threshold', 'is_active'
    ]
    list_filter = ['organization', 'fiscal_year', 'budget_type', 'is_active']
    search_fields = ['organization__name', 'organizational_node__name', 'business_unit']
    ordering = ['-fiscal_year', 'organization', 'organizational_node__code']

    fieldsets = (
        ('Organization & Cost Center', {
            'fields': ('organization', 'organizational_node', 'business_unit'),
            'description': 'Select either an organizational node OR enter a business unit name (not both)'
        }),
        ('Budget Period', {
            'fields': ('fiscal_year',)
        }),
        ('Budget Details', {
            'fields': ('budget_type', 'amount', 'currency'),
            'description': 'For financial budgets, amount is in the specified currency. For carbon budgets, amount is in tonnes CO2e.'
        }),
        ('Alert Thresholds', {
            'fields': ('warning_threshold', 'critical_threshold'),
            'description': 'Percentage thresholds for budget alerts (e.g., 80 for 80%, 95 for 95%)'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def get_cost_center(self, obj):
        """Display cost center name"""
        return obj.organizational_node.name if obj.organizational_node else obj.business_unit
    get_cost_center.short_description = 'Cost Center'
    get_cost_center.admin_order_field = 'organizational_node__name'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "organizational_node":
            # Filter nodes by organization if specified
            if 'organization' in request.GET:
                kwargs["queryset"] = OrganizationalNode.objects.filter(
                    organization_id=request.GET['organization'],
                    is_active=True
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Auto-set created_by on creation
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)