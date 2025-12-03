# Safe migration for StandardizationRule model - handles existing table

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def safe_create_standardization_rule_table(apps, schema_editor):
    """Create standardization_rules table only if it doesn't already exist"""
    from django.db import connection

    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public' AND table_name='standardization_rules'
        """)

        if cursor.fetchone():
            # Table already exists, just ensure it's registered with Django's migration system
            print("standardization_rules table already exists, skipping creation")
            return

        # Table doesn't exist, create it
        cursor.execute("""
            CREATE TABLE standardization_rules (
                id BIGSERIAL PRIMARY KEY,
                rule_type VARCHAR(20) NOT NULL,
                source_text VARCHAR(500) NOT NULL,
                target_text VARCHAR(500) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                last_applied_at TIMESTAMP WITH TIME ZONE,
                application_count INTEGER NOT NULL DEFAULT 0,
                created_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
                created_from_merge_id UUID REFERENCES merge_audits(id) ON DELETE SET NULL,
                organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
                travel_agent_id UUID REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX standardiz_rule_ty_idx ON standardization_rules(rule_type, is_active)")
        cursor.execute("CREATE INDEX standardiz_travel__idx ON standardization_rules(travel_agent_id, rule_type)")
        cursor.execute("CREATE INDEX standardiz_organiz_idx ON standardization_rules(organization_id, rule_type)")
        cursor.execute("CREATE INDEX standardiz_source__idx ON standardization_rules(source_text)")
        cursor.execute("CREATE INDEX standardiz_rule_type_idx ON standardization_rules(rule_type)")

        # Create unique constraints
        cursor.execute("""
            CREATE UNIQUE INDEX standardiz_rule_type_source_text_travel_agent_uniq
            ON standardization_rules(rule_type, source_text, travel_agent_id)
            WHERE travel_agent_id IS NOT NULL
        """)
        cursor.execute("""
            CREATE UNIQUE INDEX standardiz_rule_type_source_text_organization_uniq
            ON standardization_rules(rule_type, source_text, organization_id)
            WHERE organization_id IS NOT NULL
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bookings', '0021_add_commission_fields'),
    ]

    operations = [
        migrations.RunPython(safe_create_standardization_rule_table, migrations.RunPython.noop),
    ]
