from django.contrib import admin
from .models import FiscalYear, Budget, BudgetAlert


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ['year_label', 'organization', 'fiscal_year_type', 'start_date',
                    'end_date', 'is_current', 'is_active']
    list_filter = ['fiscal_year_type', 'is_current', 'is_active', 'organization']
    search_fields = ['year_label', 'organization__name']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Organization', {
            'fields': ('organization',)
        }),
        ('Fiscal Year Definition', {
            'fields': ('fiscal_year_type', 'year_label')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('is_active', 'is_current')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['organization', 'fiscal_year', 'cost_center', 'cost_center_name',
                    'total_budget', 'currency', 'is_active']
    list_filter = ['organization', 'fiscal_year', 'is_active', 'currency']
    search_fields = ['cost_center', 'cost_center_name', 'organization__name']
    
    fieldsets = (
        ('Budget Details', {
            'fields': ('organization', 'fiscal_year', 'cost_center', 'cost_center_name')
        }),
        ('Budget Allocations', {
            'fields': ('total_budget', 'air_budget', 'accommodation_budget',
                      'car_hire_budget', 'other_budget', 'currency', 'carbon_budget')
        }),
        ('Alert Thresholds', {
            'fields': ('warning_threshold', 'critical_threshold'),
            'description': 'Percentage thresholds for budget alerts'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BudgetAlert)
class BudgetAlertAdmin(admin.ModelAdmin):
    list_display = ['budget', 'alert_type', 'percentage_used', 'amount_spent',
                    'is_acknowledged', 'acknowledged_by', 'created_at']
    list_filter = ['alert_type', 'is_acknowledged', 'budget__organization']
    search_fields = ['budget__cost_center', 'budget__cost_center_name',
                    'budget__organization__name']
    date_hierarchy = 'created_at'
    filter_horizontal = ['notified_users']
    
    fieldsets = (
        ('Alert Details', {
            'fields': ('budget', 'alert_type', 'percentage_used', 'amount_spent')
        }),
        ('Notification', {
            'fields': ('notified_users', 'notification_sent_at')
        }),
        ('Acknowledgement', {
            'fields': ('is_acknowledged', 'acknowledged_by', 'acknowledged_at')
        }),
    )
    
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        # Budget alerts are typically created automatically by the system
        return False