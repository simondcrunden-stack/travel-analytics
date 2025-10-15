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
            'fields': ('fiscal_year_type', 'year_label', 'start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('is_active', 'is_current')
        }),
    )


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['cost_center', 'cost_center_name', 'organization', 'fiscal_year', 
                    'total_budget', 'currency', 'is_active']
    list_filter = ['is_active', 'currency', 'organization', 'fiscal_year']
    search_fields = ['cost_center', 'cost_center_name', 'organization__name']
    
    fieldsets = (
        ('Organization & Period', {
            'fields': ('organization', 'fiscal_year')
        }),
        ('Cost Center', {
            'fields': ('cost_center', 'cost_center_name')
        }),
        ('Budget Allocation', {
            'fields': ('total_budget', 'air_budget', 'accommodation_budget', 
                      'car_hire_budget', 'other_budget', 'currency')
        }),
        ('Alert Thresholds', {
            'fields': ('warning_threshold', 'critical_threshold')
        }),
        ('Additional Info', {
            'fields': ('is_active', 'notes', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BudgetAlert)
class BudgetAlertAdmin(admin.ModelAdmin):
    list_display = ['budget', 'alert_type', 'percentage_used', 'amount_spent', 
                    'is_acknowledged', 'created_at']
    list_filter = ['alert_type', 'is_acknowledged', 'created_at']
    search_fields = ['budget__cost_center', 'budget__organization__name']
    date_hierarchy = 'created_at'
    
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
    filter_horizontal = ['notified_users']
