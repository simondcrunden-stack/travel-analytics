"""
Management command to populate sample hotels and link them to existing accommodation bookings.
This is needed for hotel autocomplete to work properly.

Usage:
    python manage.py populate_sample_hotels --settings=travel_analytics.settings.development
"""
from django.core.management.base import BaseCommand
from apps.reference_data.models import Hotel
from apps.bookings.models import AccommodationBooking


class Command(BaseCommand):
    help = 'Create sample hotels and link them to existing accommodation bookings'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample hotels...')

        # Sample hotels
        hotels_data = [
            {'canonical_name': 'Hyatt Regency Sydney', 'hotel_chain': 'Hyatt', 'city': 'Sydney', 'country': 'Australia'},
            {'canonical_name': 'InterContinental Melbourne', 'hotel_chain': 'IHG', 'city': 'Melbourne', 'country': 'Australia'},
            {'canonical_name': 'Novotel Brisbane', 'hotel_chain': 'Accor', 'city': 'Brisbane', 'country': 'Australia'},
            {'canonical_name': 'Marriott Perth', 'hotel_chain': 'Marriott', 'city': 'Perth', 'country': 'Australia'},
            {'canonical_name': 'Hilton Adelaide', 'hotel_chain': 'Hilton', 'city': 'Adelaide', 'country': 'Australia'},
            {'canonical_name': 'Sheraton Grand Sydney', 'hotel_chain': 'Marriott', 'city': 'Sydney', 'country': 'Australia'},
            {'canonical_name': 'Sofitel Melbourne', 'hotel_chain': 'Accor', 'city': 'Melbourne', 'country': 'Australia'},
            {'canonical_name': 'Crown Towers Perth', 'hotel_chain': 'Crown', 'city': 'Perth', 'country': 'Australia'},
            {'canonical_name': 'Park Hyatt Sydney', 'hotel_chain': 'Hyatt', 'city': 'Sydney', 'country': 'Australia'},
            {'canonical_name': 'The Langham Melbourne', 'hotel_chain': 'Langham', 'city': 'Melbourne', 'country': 'Australia'},
        ]

        hotels_created = 0
        hotels_existing = 0

        # Create hotels
        hotel_map = {}
        for hotel_data in hotels_data:
            hotel, created = Hotel.objects.get_or_create(
                canonical_name=hotel_data['canonical_name'],
                defaults=hotel_data
            )
            hotel_map[hotel.canonical_name.lower()] = hotel
            if created:
                hotels_created += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {hotel.canonical_name}'))
            else:
                hotels_existing += 1
                self.stdout.write(f'  → Already exists: {hotel.canonical_name}')

        self.stdout.write(f'\nHotels created: {hotels_created}, already existing: {hotels_existing}')

        # Now link existing accommodation bookings to hotels
        self.stdout.write('\nLinking accommodation bookings to hotels...')

        accommodation_bookings = AccommodationBooking.objects.filter(hotel__isnull=True)
        linked_count = 0
        skipped_count = 0

        for accom in accommodation_bookings:
            # Try to match hotel_name to a canonical hotel
            hotel_name_lower = accom.hotel_name.lower() if accom.hotel_name else ''

            matched_hotel = None
            # Try exact match first
            if hotel_name_lower in hotel_map:
                matched_hotel = hotel_map[hotel_name_lower]
            else:
                # Try partial match
                for canonical_name, hotel in hotel_map.items():
                    if canonical_name in hotel_name_lower or hotel_name_lower in canonical_name:
                        matched_hotel = hotel
                        break

            if matched_hotel:
                accom.hotel = matched_hotel
                accom.save()
                linked_count += 1
                self.stdout.write(f'  ✓ Linked "{accom.hotel_name}" → {matched_hotel.canonical_name}')
            else:
                skipped_count += 1
                if skipped_count <= 10:  # Only show first 10
                    self.stdout.write(self.style.WARNING(f'  ⚠ Could not match: {accom.hotel_name}'))

        if skipped_count > 10:
            self.stdout.write(self.style.WARNING(f'  ... and {skipped_count - 10} more unmatched'))

        self.stdout.write(f'\nLinked: {linked_count}, Skipped: {skipped_count}')

        # Summary
        total_with_hotel = AccommodationBooking.objects.filter(hotel__isnull=False).count()
        total_hotels = Hotel.objects.filter(is_active=True).count()

        self.stdout.write(self.style.SUCCESS(f'\n✅ Complete!'))
        self.stdout.write(f'Total active hotels: {total_hotels}')
        self.stdout.write(f'Accommodation bookings with hotel FK: {total_with_hotel}')
