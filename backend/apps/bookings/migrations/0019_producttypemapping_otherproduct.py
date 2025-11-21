# Generated manually - Session 27
# Models for flexible product type handling during imports

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0018_preferredairline'),
        ('imports', '__latest__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductTypeMapping',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('source_name', models.CharField(help_text="Product type name as it appears in source data (e.g., 'Airfare', 'Hotel')", max_length=100, unique=True)),
                ('canonical_type', models.CharField(choices=[('BOOKING_AIR', 'Air Booking'), ('BOOKING_ACCOMMODATION', 'Accommodation Booking'), ('BOOKING_CAR_HIRE', 'Car Hire Booking'), ('BOOKING_SERVICE_FEE', 'Service Fee'), ('PRODUCT_MERCHANT_FEE', 'Merchant Fee'), ('PRODUCT_CRUISE', 'Cruise'), ('PRODUCT_PACKAGE', 'Package/Tour'), ('PRODUCT_INSURANCE', 'Insurance'), ('PRODUCT_VISA', 'Visa'), ('PRODUCT_TRANSFER', 'Transfer'), ('PRODUCT_BUS', 'Bus/Coach'), ('PRODUCT_TRAIN', 'Train/Rail'), ('PRODUCT_OTHER', 'Other/Miscellaneous')], help_text='Standardized product type classification', max_length=50)),
                ('target_model', models.CharField(choices=[('AirBooking', 'Air Booking Model'), ('AccommodationBooking', 'Accommodation Booking Model'), ('CarHireBooking', 'Car Hire Booking Model'), ('ServiceFee', 'Service Fee Model'), ('OtherProduct', 'Other Product Model')], help_text='Django model to create when this product type is imported', max_length=50)),
                ('product_type', models.CharField(blank=True, help_text='For OtherProduct target: specific product_type value to set', max_length=50)),
                ('product_subtype', models.CharField(blank=True, help_text='Optional subtype classification', max_length=50)),
                ('is_active', models.BooleanField(default=True, help_text='Inactive mappings are ignored during import')),
                ('auto_created', models.BooleanField(default=False, help_text='True if this mapping was auto-created during import')),
                ('notes', models.TextField(blank=True, help_text='Admin notes about this mapping')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Product Type Mapping',
                'verbose_name_plural': 'Product Type Mappings',
                'db_table': 'product_type_mappings',
                'ordering': ['canonical_type', 'source_name'],
            },
        ),
        migrations.CreateModel(
            name='OtherProduct',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('product_type', models.CharField(help_text='Type of product (e.g., INSURANCE, CRUISE, VISA)', max_length=50)),
                ('product_subtype', models.CharField(blank=True, help_text='Optional subtype (e.g., TRAVEL_INSURANCE, OCEAN_CRUISE)', max_length=50)),
                ('supplier_name', models.CharField(blank=True, max_length=200)),
                ('reference_number', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('amount', models.DecimalField(decimal_places=2, help_text='Total amount in original currency', max_digits=10)),
                ('currency', models.CharField(default='AUD', max_length=3)),
                ('amount_base', models.DecimalField(blank=True, decimal_places=2, help_text='Amount converted to base currency', max_digits=10, null=True)),
                ('purchase_date', models.DateField(blank=True, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('details', models.JSONField(blank=True, default=dict, help_text='Flexible storage for product-specific attributes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking', models.ForeignKey(help_text='Parent booking this product belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='other_products', to='bookings.booking')),
                ('import_batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='other_products', to='imports.importbatch')),
            ],
            options={
                'verbose_name': 'Other Product',
                'verbose_name_plural': 'Other Products',
                'db_table': 'other_products',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='producttypemapping',
            index=models.Index(fields=['source_name', 'is_active'], name='product_typ_source__0f9d8e_idx'),
        ),
        migrations.AddIndex(
            model_name='producttypemapping',
            index=models.Index(fields=['canonical_type'], name='product_typ_canonic_d6e0b0_idx'),
        ),
        migrations.AddIndex(
            model_name='producttypemapping',
            index=models.Index(fields=['target_model'], name='product_typ_target__f59c76_idx'),
        ),
        migrations.AddIndex(
            model_name='otherproduct',
            index=models.Index(fields=['booking', 'product_type'], name='other_produ_booking_b37ebb_idx'),
        ),
        migrations.AddIndex(
            model_name='otherproduct',
            index=models.Index(fields=['product_type', 'purchase_date'], name='other_produ_product_0e8835_idx'),
        ),
        migrations.AddIndex(
            model_name='otherproduct',
            index=models.Index(fields=['supplier_name'], name='other_produ_supplie_d68da5_idx'),
        ),
    ]
