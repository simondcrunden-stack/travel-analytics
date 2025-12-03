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
    list_display = ['get_node_name', 'organization', 'fiscal_year',
                    'total_budget', 'carbon_budget', 'currency', 'get_budget_status_display', 'is_active']
    list_filter = ['organization', 'fiscal_year', 'is_active', 'currency']
    search_fields = ['organizational_node__name', 'organizational_node__code',
                    'cost_center', 'cost_center_name', 'organization__name']
    ordering = ['-fiscal_year__start_date', 'organization', 'organizational_node__code']

    fieldsets = (
        ('Organization & Cost Center', {
            'fields': ('organization', 'fiscal_year', 'organizational_node'),
            'description': 'Link budget to an organizational node (cost center, business unit, etc.)'
        }),
        ('Deprecated Fields (Backward Compatibility)', {
            'fields': ('cost_center', 'cost_center_name'),
            'classes': ('collapse',),
            'description': 'Legacy fields - use organizational_node instead'
        }),
        ('Financial Budget Allocations', {
            'fields': ('total_budget', 'currency', 'air_budget', 'accommodation_budget',
                      'car_hire_budget', 'other_budget'),
            'description': 'Budget amounts by category'
        }),
        ('Carbon Budget', {
            'fields': ('carbon_budget',),
            'description': 'Annual carbon emissions budget in tonnes of CO2'
        }),
        ('Alert Thresholds', {
            'fields': ('warning_threshold', 'critical_threshold'),
            'description': 'Percentage thresholds for budget alerts (e.g., 80 = 80%, 95 = 95%)'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def get_node_name(self, obj):
        """Display organizational node name"""
        return obj.node_name
    get_node_name.short_description = 'Cost Center / Business Unit'
    get_node_name.admin_order_field = 'organizational_node__name'

    def get_budget_status_display(self, obj):
        """Display current budget status with color coding"""
        try:
            status_info = obj.get_budget_status()
            percentage = status_info['percentage']
            status = status_info['status']

            if status == 'CRITICAL':
                color = 'red'
            elif status == 'WARNING':
                color = 'orange'
            else:
                color = 'green'

            return f'<span style="color: {color}; font-weight: bold;">{percentage}% ({status})</span>'
        except:
            return 'N/A'
    get_budget_status_display.short_description = 'Status'
    get_budget_status_display.allow_tags = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "organizational_node":
            # Filter nodes by organization if specified
            if 'organization' in request.GET:
                from apps.organizations.models import OrganizationalNode
                kwargs["queryset"] = OrganizationalNode.objects.filter(
                    organization_id=request.GET['organization'],
                    is_active=True
                ).order_by('tree_id', 'lft')
        elif db_field.name == "fiscal_year":
            # Filter fiscal years by organization if specified
            if 'organization' in request.GET:
                kwargs["queryset"] = FiscalYear.objects.filter(
                    organization_id=request.GET['organization']
                ).order_by('-start_date')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Auto-set created_by on creation
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


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