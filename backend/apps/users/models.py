from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    """Extended user model for both travel agents and end customers"""
    USER_TYPES = [
        ('ADMIN', 'Platform Admin'),
        ('AGENT_ADMIN', 'Travel Agent Admin'),
        ('AGENT_USER', 'Travel Agent User'),
        ('CUSTOMER_ADMIN', 'Customer Admin'),
        ('CUSTOMER_RISK', 'Customer Risk Manager'),
        ('CUSTOMER', 'End Customer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone = models.CharField(max_length=20, blank=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, 
                                     null=True, blank=True, related_name='users')
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
