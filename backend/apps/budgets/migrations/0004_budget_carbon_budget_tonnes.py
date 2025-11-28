# Generated manually for carbon budget feature

from django.db import migrations, models
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0003_alter_budget_unique_together_and_more'),
    ]

    operations = [
        # Change all budget fields to whole numbers (0 decimal places)
        migrations.AlterField(
            model_name='budget',
            name='total_budget',
            field=models.DecimalField(
                decimal_places=0,
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))]
            ),
        ),
        migrations.AlterField(
            model_name='budget',
            name='air_budget',
            field=models.DecimalField(
                decimal_places=0,
                default=Decimal('0'),
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))]
            ),
        ),
        migrations.AlterField(
            model_name='budget',
            name='accommodation_budget',
            field=models.DecimalField(
                decimal_places=0,
                default=Decimal('0'),
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))]
            ),
        ),
        migrations.AlterField(
            model_name='budget',
            name='car_hire_budget',
            field=models.DecimalField(
                decimal_places=0,
                default=Decimal('0'),
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))]
            ),
        ),
        migrations.AlterField(
            model_name='budget',
            name='other_budget',
            field=models.DecimalField(
                decimal_places=0,
                default=Decimal('0'),
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))]
            ),
        ),
        # Add carbon budget field
        migrations.AddField(
            model_name='budget',
            name='carbon_budget',
            field=models.DecimalField(
                decimal_places=0,
                default=Decimal('0'),
                help_text='Annual carbon emissions budget in tonnes of CO2',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))]
            ),
        ),
    ]
