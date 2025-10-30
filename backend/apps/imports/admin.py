from django.contrib import admin
from .models import ImportBatch


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ['organization', 'import_date', 'import_type', 'status',
                    'records_processed', 'records_created', 'records_updated',
                    'records_failed']
    list_filter = ['status', 'import_type', 'organization', 'import_date']
    search_fields = ['organization__name', 'file_name']
    date_hierarchy = 'import_date'
    
    fieldsets = (
        ('Import Details', {
            'fields': ('organization', 'import_date', 'import_type', 'file_name', 'status')
        }),
        ('Statistics', {
            'fields': ('records_processed', 'records_created', 'records_updated',
                      'records_unchanged', 'records_failed')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Errors', {
            'fields': ('error_log',),
            'classes': ('collapse',),
            'description': 'JSON log of errors encountered during import'
        }),
    )
    
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        # Import batches are typically created programmatically, not manually
        return False