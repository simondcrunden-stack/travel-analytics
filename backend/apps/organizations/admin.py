from django.contrib import admin
from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'org_type', 'base_currency', 'is_active', 'subscription_status']
    list_filter = ['org_type', 'is_active', 'subscription_status', 'base_currency']
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
            'classes': ('collapse',),
            'description': 'Contact details for invoicing and payment processing'
        }),
        ('Financial Settings', {
            'fields': ('base_currency',)
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