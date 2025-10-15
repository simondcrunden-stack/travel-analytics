from django.contrib import admin
from .models import ImportBatch


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ['organization', 'import_date', 'import_type', 'status', 
                    'records_processed', 'records_created', 'records_failed', 'started_at']
    list_filter = ['status', 'import_type', 'organization', 'import_date']
    search_fields = ['organization__name', 'organization__code', 'file_name']
    date_hierarchy = 'import_date'
    
    fieldsets = (
        ('Import Information', {
            'fields': ('organization', 'import_date', 'import_type', 'file_name')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Statistics', {
            'fields': ('records_processed', 'records_created', 'records_updated', 
                      'records_unchanged', 'records_failed')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Error Log', {
            'fields': ('error_log',),
            'classes': ('collapse',),
            'description': 'JSON field containing detailed error information'
        }),
    )
    
    readonly_fields = ['created_at']
    
    # Make most fields read-only since this is an audit log
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return ['organization', 'import_date', 'import_type', 'file_name', 
                   'records_processed', 'records_created', 'records_updated', 
                   'records_unchanged', 'records_failed', 'started_at', 
                   'completed_at', 'created_at']
        return ['created_at']