"""
Django Management Command: Populate Booking Details
====================================================

This script populates:
1. AirSegment data for all Air bookings (with carbon emissions)
2. AccommodationBooking data for all Hotel bookings (with countries)
3. CarHireBooking data for all Car Hire bookings (with locations)

Usage:
    cd ~/Desktop/travel-analytics/backend
    source venv/bin/activate
    python manage.py shell < populate_booking_details.py

Or copy this code into a management command:
    python manage.py populate_booking_details
"""

from apps.bookings.models import Booking, AirBooking, AirSegment, AccommodationBooking, CarHireBooking
from datetime import datetime, time

print("=" * 80)
print("TRAVEL ANALYTICS - POPULATE BOOKING DETAILS")
print("=" * 80)

# =============================================================================
# AIR BOOKINGS - Create AirBooking + AirSegments
# =============================================================================

print("\n" + "=" * 80)
print("1. POPULATING AIR BOOKINGS")
print("=" * 80)

air_bookings = Booking.objects.filter(booking_type='AIR')
print(f"\nFound {air_bookings.count()} air bookings to process")

air_booking_data = [
    {
        'reference': 'QF4356',
        'trip_type': 'RETURN',
        'travel_class': 'ECONOMY',
        'origin': 'SYD',
        'destination': 'MEL',
        'ticket': 'QF-081-2345678901',
        'airline_code': 'QF',
        'airline_name': 'Qantas',
        'segments': [
            {
                'num': 1,
                'airline_code': 'QF',
                'airline_name': 'Qantas',
                'flight': 'QF435',
                'origin': 'SYD',
                'dest': 'MEL',
                'dep_date': '2025-10-20',
                'dep_time': '08:30:00',
                'arr_date': '2025-10-20',
                'arr_time': '10:00:00',
                'class': 'Y',
                'fare_basis': 'YLRT',
            },
            {
                'num': 2,
                'airline_code': 'QF',
                'airline_name': 'Qantas',
                'flight': 'QF462',
                'origin': 'MEL',
                'dest': 'SYD',
                'dep_date': '2025-10-22',
                'dep_time': '18:15:00',
                'arr_date': '2025-10-22',
                'arr_time': '19:45:00',
                'class': 'Y',
                'fare_basis': 'YLRT',
            },
        ]
    },
    {
        'reference': 'QF7812',
        'trip_type': 'ONE_WAY',
        'travel_class': 'BUSINESS',
        'origin': 'SYD',
        'destination': 'BNE',
        'ticket': 'QF-081-2345678902',
        'airline_code': 'QF',
        'airline_name': 'Qantas',
        'segments': [
            {
                'num': 1,
                'airline_code': 'QF',
                'airline_name': 'Qantas',
                'flight': 'QF515',
                'origin': 'SYD',
                'dest': 'BNE',
                'dep_date': '2025-10-03',
                'dep_time': '14:00:00',
                'arr_date': '2025-10-03',
                'arr_time': '15:30:00',
                'class': 'J',
                'fare_basis': 'JFLEX',
            },
        ]
    },
    {
        'reference': 'SQ7289',
        'trip_type': 'RETURN',
        'travel_class': 'ECONOMY',
        'origin': 'SYD',
        'destination': 'SIN',
        'ticket': 'SQ-618-3456789012',
        'airline_code': 'SQ',
        'airline_name': 'Singapore Airlines',
        'segments': [
            {
                'num': 1,
                'airline_code': 'SQ',
                'airline_name': 'Singapore Airlines',
                'flight': 'SQ232',
                'origin': 'SYD',
                'dest': 'SIN',
                'dep_date': '2025-10-15',
                'dep_time': '10:30:00',
                'arr_date': '2025-10-15',
                'arr_time': '16:00:00',
                'class': 'Y',
                'fare_basis': 'YLWF',
            },
            {
                'num': 2,
                'airline_code': 'SQ',
                'airline_name': 'Singapore Airlines',
                'flight': 'SQ231',
                'origin': 'SIN',
                'dest': 'SYD',
                'dep_date': '2025-10-22',
                'dep_time': '22:30:00',
                'arr_date': '2025-10-23',
                'arr_time': '08:30:00',
                'class': 'Y',
                'fare_basis': 'YLWF',
            },
        ]
    },
    {
        'reference': 'VA3456',
        'trip_type': 'RETURN',
        'travel_class': 'ECONOMY',
        'origin': 'MEL',
        'destination': 'PER',
        'ticket': 'VA-795-4567890123',
        'airline_code': 'VA',
        'airline_name': 'Virgin Australia',
        'segments': [
            {
                'num': 1,
                'airline_code': 'VA',
                'airline_name': 'Virgin Australia',
                'flight': 'VA681',
                'origin': 'MEL',
                'dest': 'PER',
                'dep_date': '2025-10-28',
                'dep_time': '07:45:00',
                'arr_date': '2025-10-28',
                'arr_time': '10:45:00',
                'class': 'Y',
                'fare_basis': 'YLOW',
            },
            {
                'num': 2,
                'airline_code': 'VA',
                'airline_name': 'Virgin Australia',
                'flight': 'VA688',
                'origin': 'PER',
                'dest': 'MEL',
                'dep_date': '2025-10-31',
                'dep_time': '12:00:00',
                'arr_date': '2025-10-31',
                'arr_time': '18:00:00',
                'class': 'Y',
                'fare_basis': 'YLOW',
            },
        ]
    },
    {
        'reference': 'NZ1234',
        'trip_type': 'RETURN',
        'travel_class': 'PREMIUM_ECONOMY',
        'origin': 'SYD',
        'destination': 'AKL',
        'ticket': 'NZ-086-5678901234',
        'airline_code': 'NZ',
        'airline_name': 'Air New Zealand',
        'segments': [
            {
                'num': 1,
                'airline_code': 'NZ',
                'airline_name': 'Air New Zealand',
                'flight': 'NZ104',
                'origin': 'SYD',
                'dest': 'AKL',
                'dep_date': '2025-11-05',
                'dep_time': '13:30:00',
                'arr_date': '2025-11-05',
                'arr_time': '18:30:00',
                'class': 'W',
                'fare_basis': 'WFLEX',
            },
            {
                'num': 2,
                'airline_code': 'NZ',
                'airline_name': 'Air New Zealand',
                'flight': 'NZ107',
                'origin': 'AKL',
                'dest': 'SYD',
                'dep_date': '2025-11-12',
                'dep_time': '09:00:00',
                'arr_date': '2025-11-12',
                'arr_time': '11:00:00',
                'class': 'W',
                'fare_basis': 'WFLEX',
            },
        ]
    },
    {
        'reference': 'EK4567',
        'trip_type': 'RETURN',
        'travel_class': 'ECONOMY',
        'origin': 'SYD',
        'destination': 'AKL',
        'ticket': 'EK-176-6789012345',
        'airline_code': 'NZ',
        'airline_name': 'Air New Zealand',
        'segments': [
            {
                'num': 1,
                'airline_code': 'NZ',
                'airline_name': 'Air New Zealand',
                'flight': 'NZ106',
                'origin': 'SYD',
                'dest': 'AKL',
                'dep_date': '2025-11-18',
                'dep_time': '15:00:00',
                'arr_date': '2025-11-18',
                'arr_time': '20:00:00',
                'class': 'Y',
                'fare_basis': 'YSAVER',
            },
            {
                'num': 2,
                'airline_code': 'NZ',
                'airline_name': 'Air New Zealand',
                'flight': 'NZ109',
                'origin': 'AKL',
                'dest': 'SYD',
                'dep_date': '2025-11-25',
                'dep_time': '11:30:00',
                'arr_date': '2025-11-25',
                'arr_time': '13:30:00',
                'class': 'Y',
                'fare_basis': 'YSAVER',
            },
        ]
    },
    {
        'reference': 'JQ8901',
        'trip_type': 'ONE_WAY',
        'travel_class': 'ECONOMY',
        'origin': 'SYD',
        'destination': 'BNE',
        'ticket': 'JQ-3K-7890123456',
        'airline_code': 'JQ',
        'airline_name': 'Jetstar',
        'segments': [
            {
                'num': 1,
                'airline_code': 'JQ',
                'airline_name': 'Jetstar',
                'flight': 'JQ801',
                'origin': 'SYD',
                'dest': 'BNE',
                'dep_date': '2025-11-25',
                'dep_time': '06:00:00',
                'arr_date': '2025-11-25',
                'arr_time': '07:30:00',
                'class': 'Y',
                'fare_basis': 'YSTR',
            },
        ]
    },
    {
        'reference': 'QF1234-LATE',
        'trip_type': 'ONE_WAY',
        'travel_class': 'ECONOMY',
        'origin': 'SYD',
        'destination': 'MEL',
        'ticket': 'QF-081-8901234567',
        'airline_code': 'QF',
        'airline_name': 'Qantas',
        'segments': [
            {
                'num': 1,
                'airline_code': 'QF',
                'airline_name': 'Qantas',
                'flight': 'QF447',
                'origin': 'SYD',
                'dest': 'MEL',
                'dep_date': '2025-10-30',
                'dep_time': '19:00:00',
                'arr_date': '2025-10-30',
                'arr_time': '20:30:00',
                'class': 'Y',
                'fare_basis': 'YFULL',
            },
        ]
    },
]

for data in air_booking_data:
    try:
        booking = Booking.objects.get(agent_booking_reference=data['reference'])
        
        # Create or update AirBooking
        air_booking, created = AirBooking.objects.update_or_create(
            booking=booking,
            defaults={
                'trip_type': data['trip_type'],
                'travel_class': data['travel_class'],
                'origin_airport_iata_code': data['origin'],
                'destination_airport_iata_code': data['destination'],
                'ticket_number': data['ticket'],
                'primary_airline_iata_code': data['airline_code'],
                'primary_airline_name': data['airline_name'],
            }
        )
        
        action = "Created" if created else "Updated"
        print(f"\n{action} AirBooking for {data['reference']}")
        
        # Create segments
        for seg in data['segments']:
            segment, seg_created = AirSegment.objects.update_or_create(
                air_booking=air_booking,
                segment_number=seg['num'],
                defaults={
                    'airline_iata_code': seg['airline_code'],
                    'airline_name': seg['airline_name'],
                    'flight_number': seg['flight'],
                    'origin_airport_iata_code': seg['origin'],
                    'destination_airport_iata_code': seg['dest'],
                    'departure_date': seg['dep_date'],
                    'departure_time': seg['dep_time'],
                    'arrival_date': seg['arr_date'],
                    'arrival_time': seg['arr_time'],
                    'booking_class': seg['class'],
                    'fare_basis': seg.get('fare_basis', ''),
                }
            )
            
            # Trigger save to calculate distance and carbon
            segment.save()
            
            seg_action = "Created" if seg_created else "Updated"
            print(f"  {seg_action} Segment {seg['num']}: {seg['origin']}→{seg['dest']} "
                  f"({segment.distance_km}km, {segment.carbon_emissions_kg}kg CO2)")
        
    except Booking.DoesNotExist:
        print(f"\n⚠️  Booking {data['reference']} not found - skipping")
    except Exception as e:
        print(f"\n❌ Error processing {data['reference']}: {str(e)}")

print(f"\n✅ Processed {len(air_booking_data)} air bookings")

# =============================================================================
# ACCOMMODATION BOOKINGS
# =============================================================================

print("\n" + "=" * 80)
print("2. POPULATING ACCOMMODATION BOOKINGS")
print("=" * 80)

hotel_bookings = Booking.objects.filter(booking_type='HOTEL')
print(f"\nFound {hotel_bookings.count()} hotel bookings to process")

accommodation_data = [
    {
        'reference': 'HTL-SYD-123',
        'hotel_name': 'Hilton Sydney',
        'hotel_chain': 'Hilton',
        'city': 'Sydney',
        'country': 'Australia',
        'address': '488 George Street, Sydney NSW 2000',
        'check_in': '2025-10-18',
        'check_out': '2025-10-21',
        'nights': 3,
        'room_type': 'Executive King Room',
        'nightly_rate': 320.00,
        'currency': 'AUD',
    },
    {
        'reference': 'HTL-SIN-456',
        'hotel_name': 'Marina Bay Sands',
        'hotel_chain': 'Marina Bay Sands',
        'city': 'Singapore',
        'country': 'Singapore',
        'address': '10 Bayfront Avenue, Singapore 018956',
        'check_in': '2025-10-15',
        'check_out': '2025-10-22',
        'nights': 7,
        'room_type': 'Deluxe Room',
        'nightly_rate': 450.00,
        'currency': 'SGD',
    },
    {
        'reference': 'HTL-AKL-654',
        'hotel_name': 'SkyCity Hotel Auckland',
        'hotel_chain': 'SkyCity',
        'city': 'Auckland',
        'country': 'New Zealand',
        'address': 'Corner Victoria & Federal Streets, Auckland 1010',
        'check_in': '2025-11-15',
        'check_out': '2025-11-20',
        'nights': 5,
        'room_type': 'Superior Room',
        'nightly_rate': 180.00,
        'currency': 'NZD',
    },
    {
        'reference': 'HTL-PER-789',
        'hotel_name': 'Crown Towers Perth',
        'hotel_chain': 'Crown',
        'city': 'Perth',
        'country': 'Australia',
        'address': 'Great Eastern Highway, Burswood WA 6100',
        'check_in': '2025-11-10',
        'check_out': '2025-11-13',
        'nights': 3,
        'room_type': 'Deluxe King Room',
        'nightly_rate': 240.00,
        'currency': 'AUD',
    },
]

for data in accommodation_data:
    try:
        booking = Booking.objects.get(agent_booking_reference=data['reference'])
        
        # Calculate total amount
        total = data['nightly_rate'] * data['nights']
        
        accommodation, created = AccommodationBooking.objects.update_or_create(
            booking=booking,
            defaults={
                'hotel_name': data['hotel_name'],
                'hotel_chain': data['hotel_chain'],
                'city': data['city'],
                'country': data['country'],
                'address': data['address'],
                'check_in_date': data['check_in'],
                'check_out_date': data['check_out'],
                'number_of_nights': data['nights'],
                'room_type': data['room_type'],
                'nightly_rate': data['nightly_rate'],
                'currency': data['currency'],
                'nightly_rate_base': data['nightly_rate'],  # Simplified - would need currency conversion
                'total_amount_base': total,
            }
        )
        
        action = "Created" if created else "Updated"
        print(f"\n{action} AccommodationBooking for {data['reference']}")
        print(f"  {data['hotel_name']} - {data['city']}, {data['country']}")
        print(f"  {data['nights']} nights @ ${data['nightly_rate']}/{data['currency']} = ${total}")
        
    except Booking.DoesNotExist:
        print(f"\n⚠️  Booking {data['reference']} not found - skipping")
    except Exception as e:
        print(f"\n❌ Error processing {data['reference']}: {str(e)}")

print(f"\n✅ Processed {len(accommodation_data)} hotel bookings")

# =============================================================================
# CAR HIRE BOOKINGS
# =============================================================================

print("\n" + "=" * 80)
print("3. POPULATING CAR HIRE BOOKINGS")
print("=" * 80)

car_bookings = Booking.objects.filter(booking_type='CAR')
print(f"\nFound {car_bookings.count()} car hire bookings to process")

car_hire_data = [
    {
        'reference': 'HERTZ-MEL-456',
        'rental_company': 'Hertz',
        'vehicle_type': 'Compact',
        'vehicle_category': 'Economy',
        'vehicle_make_model': 'Toyota Corolla or similar',
        'pickup_location': 'Melbourne Airport',
        'dropoff_location': 'Melbourne Airport',
        'pickup_city': 'Melbourne',
        'dropoff_city': 'Melbourne',
        'country': 'Australia',
        'pickup_date': '2025-10-25',
        'pickup_time': '10:00:00',
        'dropoff_date': '2025-10-27',
        'dropoff_time': '10:00:00',
        'days': 2,
        'daily_rate': 120.00,
        'currency': 'AUD',
    },
    {
        'reference': 'BUDGET-AKL-789',
        'rental_company': 'Budget',
        'vehicle_type': 'SUV',
        'vehicle_category': 'Full-size SUV',
        'vehicle_make_model': 'Toyota RAV4 or similar',
        'pickup_location': 'Auckland Airport',
        'dropoff_location': 'Auckland Airport',
        'pickup_city': 'Auckland',
        'dropoff_city': 'Auckland',
        'country': 'New Zealand',
        'pickup_date': '2025-11-15',
        'pickup_time': '14:00:00',
        'dropoff_date': '2025-11-20',
        'dropoff_time': '14:00:00',
        'days': 5,
        'daily_rate': 84.00,
        'currency': 'NZD',
    },
    {
        'reference': 'AVIS-PER-321',
        'rental_company': 'Avis',
        'vehicle_type': 'Sedan',
        'vehicle_category': 'Intermediate',
        'vehicle_make_model': 'Hyundai Elantra or similar',
        'pickup_location': 'Perth Airport',
        'dropoff_location': 'Perth Airport',
        'pickup_city': 'Perth',
        'dropoff_city': 'Perth',
        'country': 'Australia',
        'pickup_date': '2025-11-08',
        'pickup_time': '09:00:00',
        'dropoff_date': '2025-11-11',
        'dropoff_time': '09:00:00',
        'days': 3,
        'daily_rate': 95.00,
        'currency': 'AUD',
    },
]

for data in car_hire_data:
    try:
        booking = Booking.objects.get(agent_booking_reference=data['reference'])
        
        # Calculate total amount
        total = data['daily_rate'] * data['days']
        
        car_hire, created = CarHireBooking.objects.update_or_create(
            booking=booking,
            defaults={
                'rental_company': data['rental_company'],
                'vehicle_type': data['vehicle_type'],
                'vehicle_category': data['vehicle_category'],
                'vehicle_make_model': data['vehicle_make_model'],
                'pickup_location': data['pickup_location'],
                'dropoff_location': data['dropoff_location'],
                'pickup_city': data['pickup_city'],
                'dropoff_city': data['dropoff_city'],
                'country': data['country'],
                'pickup_date': data['pickup_date'],
                'pickup_time': data['pickup_time'],
                'dropoff_date': data['dropoff_date'],
                'dropoff_time': data['dropoff_time'],
                'number_of_days': data['days'],
                'daily_rate': data['daily_rate'],
                'currency': data['currency'],
                'daily_rate_base': data['daily_rate'],  # Simplified - would need currency conversion
                'total_amount_base': total,
            }
        )
        
        action = "Created" if created else "Updated"
        print(f"\n{action} CarHireBooking for {data['reference']}")
        print(f"  {data['rental_company']} - {data['vehicle_type']} ({data['vehicle_make_model']})")
        print(f"  {data['pickup_city']}, {data['country']}")
        print(f"  {data['days']} days @ ${data['daily_rate']}/{data['currency']} = ${total}")
        
    except Booking.DoesNotExist:
        print(f"\n⚠️  Booking {data['reference']} not found - skipping")
    except Exception as e:
        print(f"\n❌ Error processing {data['reference']}: {str(e)}")

print(f"\n✅ Processed {len(car_hire_data)} car hire bookings")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print(f"\nAir Bookings: {AirBooking.objects.count()}")
print(f"Air Segments: {AirSegment.objects.count()}")
print(f"Accommodation Bookings: {AccommodationBooking.objects.count()}")
print(f"Car Hire Bookings: {CarHireBooking.objects.count()}")

print("\n" + "=" * 80)
print("✅ ALL BOOKING DETAILS POPULATED SUCCESSFULLY!")
print("=" * 80)

print("\n📊 Next Steps:")
print("1. Visit Django Admin to verify the data")
print("2. Check carbon emissions in AirSegment records")
print("3. Verify countries appear in AccommodationBooking and CarHireBooking")
print("4. Test your Vue.js dashboards with the new data")
print("\n")
