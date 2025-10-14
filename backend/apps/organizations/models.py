from django.db import models
import uuid


class Organization(models.Model):
    """Travel agent organizations and customer companies"""
    ORG_TYPES = [
        ('AGENT', 'Travel Agent'),
        ('CUSTOMER', 'Customer Organization'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    org_type = models.CharField(max_length=20, choices=ORG_TYPES)
    code = models.CharField(max_length=50, unique=True)
    
    # Contact & billing
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Currency settings
    base_currency = models.CharField(max_length=3, default='AUD')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # For customer organizations - link to their travel agent
    travel_agent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='customers'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['org_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"