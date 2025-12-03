# Generated manually

from django.db import migrations, models


def migrate_names_forward(apps, schema_editor):
    """Copy first_name + last_name to name field"""
    Traveller = apps.get_model('bookings', 'Traveller')
    for traveller in Traveller.objects.all():
        traveller.name = f"{traveller.first_name} {traveller.last_name}".strip()
        traveller.save(update_fields=['name'])


def migrate_names_backward(apps, schema_editor):
    """Split name back to first_name and last_name"""
    Traveller = apps.get_model('bookings', 'Traveller')
    for traveller in Traveller.objects.all():
        parts = traveller.name.split(' ', 1)
        traveller.first_name = parts[0] if len(parts) > 0 else ''
        traveller.last_name = parts[1] if len(parts) > 1 else ''
        traveller.save(update_fields=['first_name', 'last_name'])


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0022_standardizationrule'),
    ]

    operations = [
        # Step 1: Add name field as nullable
        migrations.AddField(
            model_name='traveller',
            name='name',
            field=models.CharField(max_length=200, null=True, blank=True, help_text='Full name of the traveller'),
        ),

        # Step 2: Migrate data from first_name + last_name to name
        migrations.RunPython(migrate_names_forward, migrate_names_backward),

        # Step 3: Make name non-nullable
        migrations.AlterField(
            model_name='traveller',
            name='name',
            field=models.CharField(max_length=200, help_text='Full name of the traveller'),
        ),

        # Step 4: Remove old index
        migrations.RemoveIndex(
            model_name='traveller',
            name='travellers_organiz_aa00ce_idx',  # organization + last_name + first_name index
        ),

        # Step 5: Remove first_name and last_name fields
        migrations.RemoveField(
            model_name='traveller',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='traveller',
            name='last_name',
        ),

        # Step 6: Add new index with name field
        migrations.AddIndex(
            model_name='traveller',
            index=models.Index(fields=['organization', 'name'], name='travellers_organiz_name_idx'),
        ),
    ]
