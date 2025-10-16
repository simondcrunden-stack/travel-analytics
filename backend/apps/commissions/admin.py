from django.contrib import admin
from .models import Commission


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ['supplier_name', 'supplier_reference', 'product_type', 
                    'commission_amount', 'currency', 'earned_date', 
                    'booking', 'organization']
    list_filter = ['product_type', 'supplier_name', 'organization', 
                   'earned_date', 'commission_period']
    search_fields = ['supplier_name', 'supplier_reference', 
                    'booking__agent_booking_reference', 
                    'booking__supplier_reference',
                    'organization__name']
    date_hierarchy = 'earned_date'
    
    fieldsets = (
        ('Commission Details', {
            'fields': ('organization', 'booking', 'product_type')
        }),
        ('Supplier Information', {
            'fields': ('supplier_name', 'supplier_reference')
        }),
        ('Commission Amount', {
            'fields': ('commission_amount', 'currency', 'booking_amount')
        }),
        ('Converted Amount', {
            'fields': ('commission_amount_base', 'exchange_rate', 'exchange_rate_date'),
            'classes': ('collapse',),
            'description': 'Converted to organization base currency'
        }),
        ('Tracking', {
            'fields': ('earned_date', 'commission_period')
        }),
        ('Import Tracking', {
            'fields': ('import_batch',),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'commission_period']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('organization', 'booking', 'import_batch')