from django.core.management.base import BaseCommand
from apps.reference_data.models import Country


class Command(BaseCommand):
    help = 'Populate countries table with ISO 3166-1 data for common travel destinations'

    def handle(self, *args, **options):
        self.stdout.write('Populating countries table...')
        
        countries_data = [
            # Oceania - Australia & New Zealand
            {'alpha_3': 'AUS', 'alpha_2': 'AU', 'numeric_code': '036',
             'name': 'Australia', 'common_name': 'Australia',
             'region': 'Oceania', 'subregion': 'Australia and New Zealand',
             'currency_code': 'AUD', 'phone_prefix': '+61'},
            {'alpha_3': 'NZL', 'alpha_2': 'NZ', 'numeric_code': '554',
             'name': 'New Zealand', 'common_name': 'New Zealand',
             'region': 'Oceania', 'subregion': 'Australia and New Zealand',
             'currency_code': 'NZD', 'phone_prefix': '+64'},
            
            # Asia - South-Eastern Asia
            {'alpha_3': 'SGP', 'alpha_2': 'SG', 'numeric_code': '702',
             'name': 'Singapore', 'common_name': 'Singapore',
             'region': 'Asia', 'subregion': 'South-Eastern Asia',
             'currency_code': 'SGD', 'phone_prefix': '+65'},
            {'alpha_3': 'THA', 'alpha_2': 'TH', 'numeric_code': '764',
             'name': 'Thailand', 'common_name': 'Thailand',
             'region': 'Asia', 'subregion': 'South-Eastern Asia',
             'currency_code': 'THB', 'phone_prefix': '+66'},
            {'alpha_3': 'MYS', 'alpha_2': 'MY', 'numeric_code': '458',
             'name': 'Malaysia', 'common_name': 'Malaysia',
             'region': 'Asia', 'subregion': 'South-Eastern Asia',
             'currency_code': 'MYR', 'phone_prefix': '+60'},
            {'alpha_3': 'IDN', 'alpha_2': 'ID', 'numeric_code': '360',
             'name': 'Indonesia', 'common_name': 'Indonesia',
             'region': 'Asia', 'subregion': 'South-Eastern Asia',
             'currency_code': 'IDR', 'phone_prefix': '+62'},
            {'alpha_3': 'VNM', 'alpha_2': 'VN', 'numeric_code': '704',
             'name': 'Viet Nam', 'common_name': 'Vietnam',
             'region': 'Asia', 'subregion': 'South-Eastern Asia',
             'currency_code': 'VND', 'phone_prefix': '+84'},
            {'alpha_3': 'PHL', 'alpha_2': 'PH', 'numeric_code': '608',
             'name': 'Philippines', 'common_name': 'Philippines',
             'region': 'Asia', 'subregion': 'South-Eastern Asia',
             'currency_code': 'PHP', 'phone_prefix': '+63'},
            
            # Asia - Eastern Asia
            {'alpha_3': 'JPN', 'alpha_2': 'JP', 'numeric_code': '392',
             'name': 'Japan', 'common_name': 'Japan',
             'region': 'Asia', 'subregion': 'Eastern Asia',
             'currency_code': 'JPY', 'phone_prefix': '+81'},
            {'alpha_3': 'CHN', 'alpha_2': 'CN', 'numeric_code': '156',
             'name': 'China', 'common_name': 'China',
             'region': 'Asia', 'subregion': 'Eastern Asia',
             'currency_code': 'CNY', 'phone_prefix': '+86'},
            {'alpha_3': 'KOR', 'alpha_2': 'KR', 'numeric_code': '410',
             'name': 'Korea (Republic of)', 'common_name': 'South Korea',
             'region': 'Asia', 'subregion': 'Eastern Asia',
             'currency_code': 'KRW', 'phone_prefix': '+82'},
            {'alpha_3': 'HKG', 'alpha_2': 'HK', 'numeric_code': '344',
             'name': 'Hong Kong', 'common_name': 'Hong Kong',
             'region': 'Asia', 'subregion': 'Eastern Asia',
             'currency_code': 'HKD', 'phone_prefix': '+852'},
            
            # Asia - Southern Asia
            {'alpha_3': 'IND', 'alpha_2': 'IN', 'numeric_code': '356',
             'name': 'India', 'common_name': 'India',
             'region': 'Asia', 'subregion': 'Southern Asia',
             'currency_code': 'INR', 'phone_prefix': '+91'},
            
            # Americas
            {'alpha_3': 'USA', 'alpha_2': 'US', 'numeric_code': '840',
             'name': 'United States of America', 'common_name': 'United States',
             'region': 'Americas', 'subregion': 'Northern America',
             'currency_code': 'USD', 'phone_prefix': '+1'},
            {'alpha_3': 'CAN', 'alpha_2': 'CA', 'numeric_code': '124',
             'name': 'Canada', 'common_name': 'Canada',
             'region': 'Americas', 'subregion': 'Northern America',
             'currency_code': 'CAD', 'phone_prefix': '+1'},
            
            # Europe
            {'alpha_3': 'GBR', 'alpha_2': 'GB', 'numeric_code': '826',
             'name': 'United Kingdom of Great Britain and Northern Ireland',
             'common_name': 'United Kingdom',
             'region': 'Europe', 'subregion': 'Northern Europe',
             'currency_code': 'GBP', 'phone_prefix': '+44'},
            {'alpha_3': 'FRA', 'alpha_2': 'FR', 'numeric_code': '250',
             'name': 'France', 'common_name': 'France',
             'region': 'Europe', 'subregion': 'Western Europe',
             'currency_code': 'EUR', 'phone_prefix': '+33'},
            {'alpha_3': 'DEU', 'alpha_2': 'DE', 'numeric_code': '276',
             'name': 'Germany', 'common_name': 'Germany',
             'region': 'Europe', 'subregion': 'Western Europe',
             'currency_code': 'EUR', 'phone_prefix': '+49'},
            {'alpha_3': 'ITA', 'alpha_2': 'IT', 'numeric_code': '380',
             'name': 'Italy', 'common_name': 'Italy',
             'region': 'Europe', 'subregion': 'Southern Europe',
             'currency_code': 'EUR', 'phone_prefix': '+39'},
            {'alpha_3': 'ESP', 'alpha_2': 'ES', 'numeric_code': '724',
             'name': 'Spain', 'common_name': 'Spain',
             'region': 'Europe', 'subregion': 'Southern Europe',
             'currency_code': 'EUR', 'phone_prefix': '+34'},
            {'alpha_3': 'NLD', 'alpha_2': 'NL', 'numeric_code': '528',
             'name': 'Netherlands', 'common_name': 'Netherlands',
             'region': 'Europe', 'subregion': 'Western Europe',
             'currency_code': 'EUR', 'phone_prefix': '+31'},
            {'alpha_3': 'CHE', 'alpha_2': 'CH', 'numeric_code': '756',
             'name': 'Switzerland', 'common_name': 'Switzerland',
             'region': 'Europe', 'subregion': 'Western Europe',
             'currency_code': 'CHF', 'phone_prefix': '+41'},
            
            # Middle East
            {'alpha_3': 'ARE', 'alpha_2': 'AE', 'numeric_code': '784',
             'name': 'United Arab Emirates', 'common_name': 'UAE',
             'region': 'Asia', 'subregion': 'Western Asia',
             'currency_code': 'AED', 'phone_prefix': '+971'},
            
            # Pacific
            {'alpha_3': 'FJI', 'alpha_2': 'FJ', 'numeric_code': '242',
             'name': 'Fiji', 'common_name': 'Fiji',
             'region': 'Oceania', 'subregion': 'Melanesia',
             'currency_code': 'FJD', 'phone_prefix': '+679'},
        ]
        
        created_count = 0
        updated_count = 0
        
        for country_data in countries_data:
            country, created = Country.objects.update_or_create(
                alpha_3=country_data['alpha_3'],
                defaults=country_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {country.name} ({country.alpha_3})'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'→ Updated: {country.name} ({country.alpha_3})'))
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(
            f'Successfully processed {len(countries_data)} countries:\n'
            f'  - Created: {created_count}\n'
            f'  - Updated: {updated_count}'
        ))
        self.stdout.write('='*60)