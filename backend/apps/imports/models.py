from django.db import models
from apps.organizations.models import Organization
import uuid


class ImportBatch(models.Model):
    """Track each import batch for audit and troubleshooting"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partially Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='import_batches'
    )
    
    # Import details
    import_date = models.DateField()  # The date this import was run
    import_type = models.CharField(max_length=20)  # DAILY, MONTHLY, MANUAL
    file_name = models.CharField(max_length=255, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Statistics
    records_processed = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_unchanged = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    
    # Error tracking
    error_log = models.JSONField(default=list, blank=True)
    
    # Processing time
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'import_batches'
        indexes = [
            models.Index(fields=['organization', 'import_date']),
            models.Index(fields=['status', 'created_at']),
        ]
        ordering = ['-import_date', '-created_at']
    
    def __str__(self):
        return f"{self.organization.code} - {self.import_date} ({self.status})"