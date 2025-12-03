# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0004_organizationalnode'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('business_unit', models.CharField(blank=True, help_text='Business unit name (used if organizational_node is not set)', max_length=100)),
                ('fiscal_year', models.IntegerField(help_text='Fiscal year for this budget (e.g., 2024, 2025)')),
                ('budget_type', models.CharField(choices=[('FINANCIAL', 'Financial Budget'), ('CARBON', 'Carbon Budget')], help_text='Type of budget: financial (monetary) or carbon (CO2 tonnes)', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, help_text='Budget amount (currency for financial, tonnes for carbon)', max_digits=12)),
                ('currency', models.CharField(blank=True, help_text='Currency code (ISO 4217) for financial budgets', max_length=3)),
                ('warning_threshold', models.DecimalField(decimal_places=2, default=80.0, help_text='Percentage at which to show warning alert (default 80%)', max_digits=5)),
                ('critical_threshold', models.DecimalField(decimal_places=2, default=95.0, help_text='Percentage at which to show critical alert (default 95%)', max_digits=5)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this budget is currently active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, help_text='User who created this budget', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_budgets', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(help_text='Organization this budget belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='budgets', to='organizations.organization')),
                ('organizational_node', models.ForeignKey(blank=True, help_text='Organizational node (cost center, business unit, etc.) this budget applies to', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='budgets', to='organizations.organizationalnode')),
            ],
            options={
                'verbose_name': 'Budget',
                'verbose_name_plural': 'Budgets',
                'db_table': 'budgets',
                'ordering': ['-fiscal_year', 'organizational_node__code', 'budget_type'],
            },
        ),
        migrations.AddIndex(
            model_name='budget',
            index=models.Index(fields=['organization', 'fiscal_year'], name='budgets_org_fy_idx'),
        ),
        migrations.AddIndex(
            model_name='budget',
            index=models.Index(fields=['organizational_node', 'fiscal_year'], name='budgets_node_fy_idx'),
        ),
        migrations.AddIndex(
            model_name='budget',
            index=models.Index(fields=['fiscal_year', 'is_active'], name='budgets_fy_active_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='budget',
            unique_together={
                ('organization', 'organizational_node', 'fiscal_year', 'budget_type'),
                ('organization', 'business_unit', 'fiscal_year', 'budget_type'),
            },
        ),
    ]
