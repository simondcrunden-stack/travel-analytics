# Generated manually for organizational hierarchy feature

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0003_organization_home_country_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationalNode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Name of the organizational unit', max_length=200)),
                ('code', models.CharField(help_text='Unique code within organization', max_length=50)),
                ('node_type', models.CharField(choices=[('COST_CENTER', 'Cost Center'), ('BUSINESS_UNIT', 'Business Unit'), ('REGION', 'Region'), ('DEPARTMENT', 'Department'), ('DIVISION', 'Division'), ('GROUP', 'Group'), ('OTHER', 'Other')], default='DEPARTMENT', max_length=20)),
                ('path', models.CharField(blank=True, help_text='Materialized path for efficient tree queries', max_length=500)),
                ('display_order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(help_text='The organization this node belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='organizational_nodes', to='organizations.organization')),
                ('parent', models.ForeignKey(blank=True, help_text='Parent node in the hierarchy', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='organizations.organizationalnode')),
            ],
            options={
                'db_table': 'organizational_nodes',
                'ordering': ['display_order', 'name'],
            },
        ),
        migrations.AddIndex(
            model_name='organizationalnode',
            index=models.Index(fields=['organization', 'parent'], name='organizatio_organiz_98c9a0_idx'),
        ),
        migrations.AddIndex(
            model_name='organizationalnode',
            index=models.Index(fields=['organization', 'node_type'], name='organizatio_organiz_e45c5b_idx'),
        ),
        migrations.AddIndex(
            model_name='organizationalnode',
            index=models.Index(fields=['path'], name='organizatio_path_c50e0b_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='organizationalnode',
            unique_together={('organization', 'code')},
        ),
    ]
