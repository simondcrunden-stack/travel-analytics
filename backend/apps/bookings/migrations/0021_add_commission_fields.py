# Generated manually for commission fields addition

from django.db import migrations, models
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0020_populate_product_type_mappings'),
    ]

    operations = [
        # Add commission fields to AirBooking
        migrations.AddField(
            model_name='airbooking',
            name='commission_amount',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Commission earned from airline/supplier',
                max_digits=10
            ),
        ),
        migrations.AddField(
            model_name='airbooking',
            name='commission_rate',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Commission percentage (e.g., 5.00 for 5%)',
                max_digits=5,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='airbooking',
            name='commission_currency',
            field=models.CharField(
                default='AUD',
                help_text='Currency of commission (defaults to booking currency)',
                max_length=3
            ),
        ),

        # Add commission fields to AccommodationBooking
        migrations.AddField(
            model_name='accommodationbooking',
            name='commission_amount',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Commission earned from hotel/supplier',
                max_digits=10
            ),
        ),
        migrations.AddField(
            model_name='accommodationbooking',
            name='commission_rate',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Commission percentage (e.g., 10.00 for 10%)',
                max_digits=5,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='accommodationbooking',
            name='commission_currency',
            field=models.CharField(
                default='AUD',
                help_text='Currency of commission (defaults to booking currency)',
                max_length=3
            ),
        ),

        # Add commission fields to CarHireBooking
        migrations.AddField(
            model_name='carhirebooking',
            name='commission_amount',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Commission earned from rental company/supplier',
                max_digits=10
            ),
        ),
        migrations.AddField(
            model_name='carhirebooking',
            name='commission_rate',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Commission percentage (e.g., 15.00 for 15%)',
                max_digits=5,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='carhirebooking',
            name='commission_currency',
            field=models.CharField(
                default='AUD',
                help_text='Currency of commission (defaults to booking currency)',
                max_length=3
            ),
        ),
    ]
