# Generated manually - Session 27
# Pre-populate ProductTypeMapping with known product type variations

from django.db import migrations


def populate_mappings(apps, schema_editor):
    """Create default product type mappings"""
    ProductTypeMapping = apps.get_model('bookings', 'ProductTypeMapping')

    mappings = [
        # AIR BOOKINGS - All variations
        {'source_name': 'Air', 'canonical_type': 'BOOKING_AIR', 'target_model': 'AirBooking', 'product_type': ''},
        {'source_name': 'Airfare', 'canonical_type': 'BOOKING_AIR', 'target_model': 'AirBooking', 'product_type': ''},
        {'source_name': 'Air Travel', 'canonical_type': 'BOOKING_AIR', 'target_model': 'AirBooking', 'product_type': ''},
        {'source_name': 'Flight', 'canonical_type': 'BOOKING_AIR', 'target_model': 'AirBooking', 'product_type': ''},

        # ACCOMMODATION BOOKINGS - All variations
        {'source_name': 'Accommodation', 'canonical_type': 'BOOKING_ACCOMMODATION', 'target_model': 'AccommodationBooking', 'product_type': ''},
        {'source_name': 'Hotel', 'canonical_type': 'BOOKING_ACCOMMODATION', 'target_model': 'AccommodationBooking', 'product_type': ''},

        # CAR HIRE BOOKINGS - All variations
        {'source_name': 'Car hire', 'canonical_type': 'BOOKING_CAR_HIRE', 'target_model': 'CarHireBooking', 'product_type': ''},
        {'source_name': 'Rental Car', 'canonical_type': 'BOOKING_CAR_HIRE', 'target_model': 'CarHireBooking', 'product_type': ''},
        {'source_name': 'Rental Car Hire', 'canonical_type': 'BOOKING_CAR_HIRE', 'target_model': 'CarHireBooking', 'product_type': ''},

        # SERVICE FEES - All variations
        {'source_name': 'Service Fee', 'canonical_type': 'BOOKING_SERVICE_FEE', 'target_model': 'ServiceFee', 'product_type': ''},
        {'source_name': 'TMC Fee', 'canonical_type': 'BOOKING_SERVICE_FEE', 'target_model': 'ServiceFee', 'product_type': ''},
        {'source_name': 'Transaction Fee', 'canonical_type': 'BOOKING_SERVICE_FEE', 'target_model': 'ServiceFee', 'product_type': ''},
        {'source_name': 'Travel Agent Fee', 'canonical_type': 'BOOKING_SERVICE_FEE', 'target_model': 'ServiceFee', 'product_type': ''},

        # MERCHANT FEES → OtherProduct
        {'source_name': 'Merchant Fee', 'canonical_type': 'PRODUCT_MERCHANT_FEE', 'target_model': 'OtherProduct', 'product_type': 'MERCHANT_FEE'},
        {'source_name': 'Credit Card Fee', 'canonical_type': 'PRODUCT_MERCHANT_FEE', 'target_model': 'OtherProduct', 'product_type': 'MERCHANT_FEE'},

        # CRUISE → OtherProduct
        {'source_name': 'Cruise', 'canonical_type': 'PRODUCT_CRUISE', 'target_model': 'OtherProduct', 'product_type': 'CRUISE'},

        # PACKAGE/TOUR → OtherProduct
        {'source_name': 'Package', 'canonical_type': 'PRODUCT_PACKAGE', 'target_model': 'OtherProduct', 'product_type': 'PACKAGE'},
        {'source_name': 'Package Holiday', 'canonical_type': 'PRODUCT_PACKAGE', 'target_model': 'OtherProduct', 'product_type': 'PACKAGE'},
        {'source_name': 'Tour', 'canonical_type': 'PRODUCT_PACKAGE', 'target_model': 'OtherProduct', 'product_type': 'TOUR'},

        # INSURANCE → OtherProduct
        {'source_name': 'Insurance', 'canonical_type': 'PRODUCT_INSURANCE', 'target_model': 'OtherProduct', 'product_type': 'INSURANCE'},

        # VISA → OtherProduct
        {'source_name': 'Visa', 'canonical_type': 'PRODUCT_VISA', 'target_model': 'OtherProduct', 'product_type': 'VISA'},
        {'source_name': 'Travel Visa', 'canonical_type': 'PRODUCT_VISA', 'target_model': 'OtherProduct', 'product_type': 'VISA'},

        # TRANSFER → OtherProduct
        {'source_name': 'Transfer', 'canonical_type': 'PRODUCT_TRANSFER', 'target_model': 'OtherProduct', 'product_type': 'TRANSFER'},
        {'source_name': 'Airport Transfers', 'canonical_type': 'PRODUCT_TRANSFER', 'target_model': 'OtherProduct', 'product_type': 'TRANSFER'},
        {'source_name': 'Transfers', 'canonical_type': 'PRODUCT_TRANSFER', 'target_model': 'OtherProduct', 'product_type': 'TRANSFER'},
        {'source_name': 'Chauffeur', 'canonical_type': 'PRODUCT_TRANSFER', 'target_model': 'OtherProduct', 'product_type': 'CHAUFFEUR'},

        # BUS/COACH → OtherProduct
        {'source_name': 'Bus', 'canonical_type': 'PRODUCT_BUS', 'target_model': 'OtherProduct', 'product_type': 'BUS'},
        {'source_name': 'Coach', 'canonical_type': 'PRODUCT_BUS', 'target_model': 'OtherProduct', 'product_type': 'COACH'},

        # TRAIN/RAIL → OtherProduct
        {'source_name': 'Train', 'canonical_type': 'PRODUCT_TRAIN', 'target_model': 'OtherProduct', 'product_type': 'TRAIN'},
        {'source_name': 'Rail', 'canonical_type': 'PRODUCT_TRAIN', 'target_model': 'OtherProduct', 'product_type': 'RAIL'},

        # OTHER/MISCELLANEOUS → OtherProduct
        {'source_name': 'Miscellaneous', 'canonical_type': 'PRODUCT_OTHER', 'target_model': 'OtherProduct', 'product_type': 'MISCELLANEOUS'},
        {'source_name': 'Other', 'canonical_type': 'PRODUCT_OTHER', 'target_model': 'OtherProduct', 'product_type': 'OTHER'},
    ]

    for mapping_data in mappings:
        ProductTypeMapping.objects.create(**mapping_data)

    print(f"✅ Created {len(mappings)} product type mappings")


def reverse_mappings(apps, schema_editor):
    """Remove all mappings on rollback"""
    ProductTypeMapping = apps.get_model('bookings', 'ProductTypeMapping')
    count = ProductTypeMapping.objects.all().count()
    ProductTypeMapping.objects.all().delete()
    print(f"❌ Deleted {count} product type mappings")


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0019_producttypemapping_otherproduct'),
    ]

    operations = [
        migrations.RunPython(populate_mappings, reverse_mappings),
    ]
