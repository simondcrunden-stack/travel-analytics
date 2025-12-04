# Update existing budgets to sync cost_center fields with organizational_node

from django.db import migrations


def sync_cost_center_fields(apps, schema_editor):
    """Sync cost_center fields from organizational_node for existing budgets"""
    Budget = apps.get_model('budgets', 'Budget')
    OrganizationalNode = apps.get_model('organizations', 'OrganizationalNode')

    # Find budgets that have organizational_node but empty cost_center fields
    budgets_to_update = Budget.objects.filter(
        organizational_node__isnull=False
    ).exclude(
        organizational_node__name=''
    )

    updated_count = 0
    for budget in budgets_to_update:
        if budget.organizational_node:
            budget.cost_center = budget.organizational_node.code or ''
            budget.cost_center_name = budget.organizational_node.name or ''
            budget.save()
            updated_count += 1

    if updated_count > 0:
        print(f"Updated {updated_count} budgets with organizational node data")


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0007_fix_carbon_budget_tonnes'),
    ]

    operations = [
        migrations.RunPython(sync_cost_center_fields, migrations.RunPython.noop),
    ]
