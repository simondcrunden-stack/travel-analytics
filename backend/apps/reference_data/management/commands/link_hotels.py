"""
Management command to link existing accommodation bookings to hotels in the master data.

Usage:
    python manage.py link_hotels --settings=travel_analytics.settings.development
"""
from django.core.management.base import BaseCommand
from apps.reference_data.models import Hotel
from apps.bookings.models import AccommodationBooking


class Command(BaseCommand):
    help = 'Link accommodation bookings to hotels by matching hotel names'

    def handle(self, *args, **options):
        self.stdout.write('Linking accommodation bookings to hotels...\n')

        # Get all hotels for matching
        all_hotels = Hotel.objects.filter(is_active=True)
        hotel_map = {hotel.canonical_name.lower(): hotel for hotel in all_hotels}

        self.stdout.write(f'Found {len(hotel_map)} active hotels in master data\n')

        # Get accommodation bookings without hotel FK
        unlinked_bookings = AccommodationBooking.objects.filter(hotel__isnull=True)
        total_unlinked = unlinked_bookings.count()

        self.stdout.write(f'Found {total_unlinked} unlinked accommodation bookings\n')

        if total_unlinked == 0:
            self.stdout.write(self.style.SUCCESS('✅ All accommodation bookings are already linked!'))
            return

        linked_count = 0
        not_found_count = 0
        not_found_names = set()

        for accom in unlinked_bookings:
            hotel_name_lower = accom.hotel_name.lower() if accom.hotel_name else ''

            # Try exact match first
            if hotel_name_lower in hotel_map:
                matched_hotel = hotel_map[hotel_name_lower]
                accom.hotel = matched_hotel
                accom.save()
                linked_count += 1
                self.stdout.write(f'  ✓ Linked "{accom.hotel_name}" → {matched_hotel.canonical_name}')
            else:
                # Try partial match
                matched_hotel = None
                for canonical_name, hotel in hotel_map.items():
                    if canonical_name in hotel_name_lower or hotel_name_lower in canonical_name:
                        matched_hotel = hotel
                        break

                if matched_hotel:
                    accom.hotel = matched_hotel
                    accom.save()
                    linked_count += 1
                    self.stdout.write(f'  ✓ Linked "{accom.hotel_name}" → {matched_hotel.canonical_name} (partial match)')
                else:
                    not_found_count += 1
                    not_found_names.add(accom.hotel_name)

        # Show unmatched hotels
        if not_found_names:
            self.stdout.write(self.style.WARNING(f'\n⚠ Could not find matches for {not_found_count} bookings:'))
            for name in sorted(not_found_names)[:20]:  # Show max 20
                self.stdout.write(f'  - {name}')

            if len(not_found_names) > 20:
                self.stdout.write(f'  ... and {len(not_found_names) - 20} more')

            self.stdout.write(self.style.WARNING(f'\n💡 To fix this, create Hotel records for these names:'))
            self.stdout.write('   python manage.py shell --settings=travel_analytics.settings.development')
            self.stdout.write('   >>> from apps.reference_data.models import Hotel')
            for name in sorted(not_found_names)[:5]:
                safe_name = name.replace("'", "\\'")
                self.stdout.write(f"   >>> Hotel.objects.create(canonical_name='{safe_name}', hotel_chain='', city='', country='')")

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n✅ Complete!'))
        self.stdout.write(f'Linked: {linked_count}')
        self.stdout.write(f'Not found: {not_found_count}')

        total_linked = AccommodationBooking.objects.filter(hotel__isnull=False).count()
        total_accoms = AccommodationBooking.objects.count()
        self.stdout.write(f'\nTotal accommodation bookings with hotel FK: {total_linked}/{total_accoms}')
