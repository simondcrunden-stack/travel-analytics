from django.contrib import admin
from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organization model"""
    
    list_display = ['name', 'code', 'org_type', 'base_currency', 'is_active', 'created_at']
    list_filter = ['org_type', 'is_active', 'base_currency']
    search_fields = ['name', 'code', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'org_type', 'is_active')
        }),
        ('Contact Details', {
            'fields': ('contact_email', 'contact_phone', 'address')
        }),
        ('Settings', {
            'fields': ('base_currency', 'travel_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
