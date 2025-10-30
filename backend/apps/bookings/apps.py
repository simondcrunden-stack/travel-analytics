from django.apps import AppConfig


class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bookings'
    verbose_name = 'Bookings'
    
    def ready(self):
        """Import signal handlers when Django starts"""
        try:
            import apps.bookings.signals
            print("✅ Bookings signals registered successfully")
        except Exception as e:
            print(f"❌ Error registering bookings signals: {e}")
