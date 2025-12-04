# Fix carbon_budget_tonnes column to allow null or have default value

from django.db import migrations


def fix_carbon_budget_tonnes(apps, schema_editor):
    """Make carbon_budget_tonnes nullable with default value"""
    from django.db import connection

    with connection.cursor() as cursor:
        # Check if carbon_budget_tonnes column exists
        cursor.execute("""
            SELECT column_name, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name='budgets' AND column_name='carbon_budget_tonnes'
        """)

        result = cursor.fetchone()
        if result:
            # Column exists - make it nullable with default 0
            cursor.execute("""
                ALTER TABLE budgets
                ALTER COLUMN carbon_budget_tonnes SET DEFAULT 0,
                ALTER COLUMN carbon_budget_tonnes DROP NOT NULL
            """)

            # Update any existing NULL values to 0
            cursor.execute("""
                UPDATE budgets
                SET carbon_budget_tonnes = 0
                WHERE carbon_budget_tonnes IS NULL
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0005_budget_carbon_budget_safe'),
    ]

    operations = [
        migrations.RunPython(fix_carbon_budget_tonnes, migrations.RunPython.noop),
    ]
