# Generated migration for StandardizationRule model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bookings', '0021_add_commission_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='StandardizationRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule_type', models.CharField(
                    choices=[
                        ('CONSULTANT', 'Travel Consultant'),
                        ('SERVICE_FEE', 'Service Fee'),
                        ('TRAVELLER', 'Traveller'),
                        ('ORGANIZATION', 'Organization'),
                    ],
                    db_index=True,
                    help_text='Type of entity this rule applies to',
                    max_length=20
                )),
                ('source_text', models.CharField(
                    help_text='The variation/incorrect text to standardize',
                    max_length=500
                )),
                ('target_text', models.CharField(
                    help_text='The standard/correct text to use',
                    max_length=500
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Whether this rule is currently applied during imports'
                )),
                ('last_applied_at', models.DateTimeField(
                    blank=True,
                    help_text='Last time this rule was applied during import',
                    null=True
                )),
                ('application_count', models.IntegerField(
                    default=0,
                    help_text='Number of times this rule has been applied'
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_standardization_rules',
                    to=settings.AUTH_USER_MODEL
                )),
                ('created_from_merge', models.ForeignKey(
                    blank=True,
                    help_text='Merge operation that created this rule',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='standardization_rules',
                    to='bookings.mergeaudit'
                )),
                ('organization', models.ForeignKey(
                    blank=True,
                    help_text='Organization context (for other rules)',
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='standardization_rules_org',
                    to='organizations.organization'
                )),
                ('travel_agent', models.ForeignKey(
                    blank=True,
                    help_text='Travel agent context (for consultant rules)',
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='standardization_rules_agent',
                    to='organizations.organization'
                )),
            ],
            options={
                'db_table': 'standardization_rules',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['rule_type', 'is_active'], name='standardiz_rule_ty_idx'),
                    models.Index(fields=['travel_agent', 'rule_type'], name='standardiz_travel__idx'),
                    models.Index(fields=['organization', 'rule_type'], name='standardiz_organiz_idx'),
                    models.Index(fields=['source_text'], name='standardiz_source__idx'),
                ],
                'unique_together': {
                    ('rule_type', 'source_text', 'travel_agent'),
                    ('rule_type', 'source_text', 'organization'),
                },
            },
        ),
    ]
