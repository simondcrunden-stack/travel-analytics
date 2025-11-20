#!/usr/bin/env python
"""
Populate sample Preferred Airline records for testing airline deals analysis.

Run this script from Django shell:
    python manage.py shell < populate_preferred_airlines.py

Or manually in shell:
    python manage.py shell
    exec(open('populate_preferred_airlines.py').read())
"""

from apps.bookings.models import PreferredAirline
from apps.organizations.models import Organization
from datetime import date, timedelta
from decimal import Decimal

print("=" * 80)
print("POPULATING PREFERRED AIRLINES")
print("=" * 80)

# Get the first organization (or specify your organization)
try:
    org = Organization.objects.first()
    if not org:
        print("❌ ERROR: No organizations found. Please create an organization first.")
        print("   You can do this in Django admin: /admin/organizations/organization/")
        exit(1)

    print(f"✅ Using organization: {org.name} ({org.code})")
except Exception as e:
    print(f"❌ ERROR: Could not get organization: {e}")
    exit(1)

# Define contract period (current year)
today = date.today()
contract_start = date(today.year, 1, 1)
contract_end = date(today.year, 12, 31)

print(f"\n📅 Contract period: {contract_start} → {contract_end}")
print("\n" + "-" * 80)

# Sample Preferred Airlines
preferred_airlines = [
    {
        'airline_iata_code': 'QF',
        'airline_name': 'Qantas Airways',
        'market_type': 'DOMESTIC',
        'markets_served': ['ALL'],
        'routes_covered': ['ALL'],  # All domestic routes
        'target_market_share': Decimal('85.00'),
        'target_revenue': Decimal('850000.00'),  # $850k annual revenue target
        'notes': 'Primary domestic carrier. Target 85% market share on all domestic routes.'
    },
    {
        'airline_iata_code': 'VA',
        'airline_name': 'Virgin Australia',
        'market_type': 'DOMESTIC',
        'markets_served': ['ALL'],
        'routes_covered': ['ALL'],
        'target_market_share': Decimal('10.00'),
        'target_revenue': Decimal('100000.00'),  # $100k annual revenue target
        'notes': 'Secondary domestic carrier. Primarily for competitive pricing and schedule flexibility.'
    },
    {
        'airline_iata_code': 'SQ',
        'airline_name': 'Singapore Airlines',
        'market_type': 'INTERNATIONAL',
        'markets_served': ['SG', 'UK', 'FR', 'DE'],  # Singapore, UK, France, Germany
        'routes_covered': ['MEL-SIN', 'SYD-SIN', 'BNE-SIN', 'PER-SIN'],
        'target_market_share': Decimal('80.00'),
        'target_revenue': Decimal('1200000.00'),  # $1.2M annual revenue target
        'notes': 'Primary carrier for Singapore and European connections via Singapore hub.'
    },
    {
        'airline_iata_code': 'EK',
        'airline_name': 'Emirates',
        'market_type': 'INTERNATIONAL',
        'markets_served': ['AE', 'UK', 'FR', 'DE', 'IT', 'ES'],  # Middle East and Europe
        'routes_covered': ['MEL-DXB', 'SYD-DXB', 'BNE-DXB', 'PER-DXB'],
        'target_market_share': Decimal('15.00'),
        'target_revenue': Decimal('225000.00'),  # $225k annual revenue target
        'notes': 'Secondary carrier for Middle East and European routes via Dubai hub.'
    },
    {
        'airline_iata_code': 'QF',
        'airline_name': 'Qantas Airways',
        'market_type': 'INTERNATIONAL',
        'markets_served': ['US', 'UK', 'NZ', 'JP', 'SG'],
        'routes_covered': ['MEL-LAX', 'SYD-LAX', 'MEL-LHR', 'SYD-LHR', 'MEL-AKL', 'SYD-AKL'],
        'target_market_share': Decimal('70.00'),
        'target_revenue': Decimal('1050000.00'),  # $1.05M annual revenue target
        'notes': 'Primary international carrier for trans-Pacific, UK, and trans-Tasman routes.'
    },
]

print("\n📝 Creating Preferred Airline records...\n")

created_count = 0
updated_count = 0
error_count = 0

for airline_data in preferred_airlines:
    try:
        # Check if this airline contract already exists
        existing = PreferredAirline.objects.filter(
            organization=org,
            airline_iata_code=airline_data['airline_iata_code'],
            market_type=airline_data['market_type'],
            contract_start_date=contract_start
        ).first()

        if existing:
            # Update existing record
            for key, value in airline_data.items():
                setattr(existing, key, value)
            existing.contract_start_date = contract_start
            existing.contract_end_date = contract_end
            existing.is_active = True
            existing.save()

            print(f"✏️  UPDATED: {airline_data['airline_name']} - {airline_data['market_type']}")
            print(f"    Target Market Share: {airline_data['target_market_share']}%")
            if airline_data.get('target_revenue'):
                print(f"    Target Revenue: ${airline_data['target_revenue']:,.0f}")
            updated_count += 1
        else:
            # Create new record
            PreferredAirline.objects.create(
                organization=org,
                airline_iata_code=airline_data['airline_iata_code'],
                airline_name=airline_data['airline_name'],
                market_type=airline_data['market_type'],
                markets_served=airline_data['markets_served'],
                routes_covered=airline_data['routes_covered'],
                target_market_share=airline_data['target_market_share'],
                target_revenue=airline_data.get('target_revenue'),
                contract_start_date=contract_start,
                contract_end_date=contract_end,
                is_active=True,
                notes=airline_data['notes']
            )

            print(f"✅ CREATED: {airline_data['airline_name']} - {airline_data['market_type']}")
            print(f"    Target Market Share: {airline_data['target_market_share']}%")
            if airline_data.get('target_revenue'):
                print(f"    Target Revenue: ${airline_data['target_revenue']:,.0f}")
            created_count += 1

        # Show routes/markets
        if airline_data['routes_covered'] == ['ALL']:
            print(f"    Routes: ALL")
        else:
            print(f"    Routes: {', '.join(airline_data['routes_covered'][:3])}{'...' if len(airline_data['routes_covered']) > 3 else ''}")

        if airline_data['markets_served'] == ['ALL']:
            print(f"    Markets: ALL")
        else:
            print(f"    Markets: {', '.join(airline_data['markets_served'])}")

        print()

    except Exception as e:
        print(f"❌ ERROR creating {airline_data['airline_name']} - {airline_data['market_type']}: {e}\n")
        error_count += 1

print("-" * 80)
print("\n📊 SUMMARY:")
print(f"   ✅ Created: {created_count}")
print(f"   ✏️  Updated: {updated_count}")
print(f"   ❌ Errors: {error_count}")
print(f"   📝 Total: {created_count + updated_count} preferred airline contracts")

# Display final list
print("\n" + "=" * 80)
print("PREFERRED AIRLINES IN DATABASE")
print("=" * 80)

all_preferred = PreferredAirline.objects.filter(organization=org, is_active=True).order_by('market_type', 'airline_name')

if all_preferred.exists():
    for pref in all_preferred:
        status = "✅ Active" if pref.is_contract_active() else "❌ Inactive"
        print(f"\n{status} | {pref.airline_name} ({pref.airline_iata_code}) - {pref.market_type}")
        print(f"         Target Market Share: {pref.target_market_share}%")
        if pref.target_revenue:
            print(f"         Target Revenue: ${pref.target_revenue:,.0f}")
        print(f"         Period: {pref.contract_start_date} → {pref.contract_end_date}")
else:
    print("(None found)")

print("\n" + "=" * 80)
print("✅ DONE! You can now view these in Django Admin:")
print("   http://localhost:8000/admin/bookings/preferredairline/")
print("=" * 80)
