from django.contrib import admin
from .models import Organization, OrganizationalNode


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
    list_display = ['name', 'code', 'organization', 'node_type', 'parent', 'display_order', 'is_active']
    list_filter = ['organization', 'node_type', 'is_active']
    search_fields = ['name', 'code', 'organization__name']
    ordering = ['organization', 'display_order', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('organization', 'name', 'code', 'node_type')
        }),
        ('Hierarchy', {
            'fields': ('parent', 'display_order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Computed Fields (Read-only)', {
            'fields': ('path',),
            'description': 'These fields are automatically computed'
        }),
    )

    readonly_fields = ['path']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            # Only show nodes from the same organization
            if 'organization' in request.GET:
                kwargs["queryset"] = OrganizationalNode.objects.filter(
                    organization_id=request.GET['organization']
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)