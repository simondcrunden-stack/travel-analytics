# Generated manually for carbon budget feature

from django.db import migrations, models
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0003_alter_budget_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='budget',
            name='carbon_budget_tonnes',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='Annual carbon emissions budget in tonnes of CO2',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]
            ),
        ),
    ]
