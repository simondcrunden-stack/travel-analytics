# Generated to merge migration branches
# This resolves the conflict between 0023 and 0028

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0023_change_traveller_name_to_single_field'),
        ('bookings', '0028_merge_20251203_1526'),
    ]

    operations = [
    ]
