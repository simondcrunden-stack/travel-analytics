from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
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


class UserProfile(models.Model):
    """Extended user profile for preferences and settings"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    # User's home country for domestic/international filtering
    home_country = models.CharField(
        max_length=2, 
        default='AU',
        help_text="ISO 2-letter country code (e.g., 'AU', 'NZ', 'SG')"
    )
    
    # Saved default filter preferences (stored as JSON)
    default_filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="User's default filter preferences across dashboards"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"{self.user.username}'s profile"


# Signal handlers for automatic profile creation
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()