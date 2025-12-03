# Safe migration to add carbon_budget field if it doesn't exist

from django.db import migrations, models
from decimal import Decimal
import django.core.validators


def add_carbon_budget_if_not_exists(apps, schema_editor):
    """Add carbon_budget column only if it doesn't already exist"""
    from django.db import connection

    with connection.cursor() as cursor:
        # Check if column exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='budgets' AND column_name='carbon_budget'
        """)

        if not cursor.fetchone():
            # Column doesn't exist, add it
            cursor.execute("""
                ALTER TABLE budgets
                ADD COLUMN carbon_budget DECIMAL(10, 0) DEFAULT 0 NOT NULL
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0004_budget_carbon_budget_tonnes'),
    ]

    operations = [
        migrations.RunPython(add_carbon_budget_if_not_exists, migrations.RunPython.noop),
    ]
