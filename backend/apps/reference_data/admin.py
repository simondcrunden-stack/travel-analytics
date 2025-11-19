from django.contrib import admin
from .models import (
    Airport, Airline, FareClassMapping, CurrencyExchangeRate, Country,
    HotelChain, CarRentalCompany, Hotel, HotelAlias
)


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ['iata_code', 'name', 'city', 'country', 'timezone']
    list_filter = ['country']
    search_fields = ['iata_code', 'name', 'city', 'country']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('iata_code', 'name')
        }),
        ('Location', {
            'fields': ('city', 'country', 'timezone')
        }),
        ('Coordinates', {
            'fields': ('latitude', 'longitude')
        }),
    )


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ['iata_code', 'name', 'country', 'alliance']
    list_filter = ['alliance', 'country']
    search_fields = ['iata_code', 'name', 'country']

    fieldsets = (
        ('Basic Information', {
            'fields': ('iata_code', 'name')
        }),
        ('Additional Details', {
            'fields': ('country', 'alliance')
        }),
    )


@admin.register(FareClassMapping)
class FareClassMappingAdmin(admin.ModelAdmin):
    """
    Admin for managing airline fare class mappings with temporal validity.

    Use this to:
    - Define DEFAULT mappings (airline=blank) that apply to all airlines
    - Define AIRLINE-SPECIFIC mappings that override defaults
    - Track fare structure changes over time with valid_from/valid_to dates
    - Update historical bookings when fare structures change

    Priority: Airline-specific mappings override defaults.
    """
    list_display = ['mapping_type', 'airline', 'fare_code', 'travel_class', 'fare_type',
                    'valid_from', 'valid_to', 'is_active']
    list_filter = ['travel_class', 'is_active', 'valid_from']
    search_fields = ['airline__iata_code', 'airline__name', 'fare_code', 'fare_type']
    date_hierarchy = 'valid_from'

    fieldsets = (
        ('Mapping Type', {
            'fields': ('airline',),
            'description': 'Leave BLANK for default mapping (applies to all airlines). '
                          'Select airline for airline-specific override.'
        }),
        ('Fare Code', {
            'fields': ('fare_code',),
            'description': 'Enter the fare class code (e.g., Y, D, O, J)'
        }),
        ('Classification', {
            'fields': ('travel_class', 'fare_type'),
            'description': 'Standardized travel class and optional fare brand name'
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_to'),
            'description': 'Date range when this mapping is valid. Leave valid_to blank for ongoing mappings.'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',),
            'description': 'Document fare structure changes, special conditions, etc.'
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    # Make it easier to add multiple mappings
    save_as = True

    # Order: defaults first, then by airline, fare code, and most recent first
    ordering = ['airline__iata_code', 'fare_code', '-valid_from']

    def mapping_type(self, obj):
        """Display whether this is a default or airline-specific mapping"""
        if obj.airline:
            return f"✈ {obj.airline.iata_code}"
        return "⭐ DEFAULT"
    mapping_type.short_description = 'Type'
    mapping_type.admin_order_field = 'airline'

    def get_readonly_fields(self, request, obj=None):
        """Make airline and fare_code readonly after creation to prevent accidental changes"""
        if obj:  # Editing existing object
            return self.readonly_fields + ['airline', 'fare_code']
        return self.readonly_fields


@admin.register(CurrencyExchangeRate)
class CurrencyExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['from_currency', 'to_currency', 'exchange_rate', 'rate_date', 'rate_source']
    list_filter = ['from_currency', 'to_currency', 'rate_date']
    search_fields = ['from_currency', 'to_currency', 'rate_source']
    date_hierarchy = 'rate_date'
    
    fieldsets = (
        ('Currency Pair', {
            'fields': ('from_currency', 'to_currency')
        }),
        ('Exchange Rate', {
            'fields': ('exchange_rate', 'rate_date', 'rate_source')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    # Make it easier to add multiple rates
    save_as = True

@admin.register(HotelChain)
class HotelChainAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'is_preferred', 'has_corporate_rate', 
                    'account_manager_name', 'is_active']
    list_filter = ['tier', 'is_preferred', 'has_corporate_rate', 'is_active']
    search_fields = ['name', 'alternative_names', 'account_manager_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'alternative_names', 'website')
        }),
        ('Supplier Status', {
            'fields': ('is_preferred', 'tier', 'is_active')
        }),
        ('Corporate Rates', {
            'fields': ('has_corporate_rate', 'corporate_discount_percentage')
        }),
        ('Account Manager', {
            'fields': ('account_manager_name', 'account_manager_email', 'account_manager_phone'),
            'classes': ('collapse',)
        }),
        ('Contract Details', {
            'fields': ('contract_start_date', 'contract_end_date'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CarRentalCompany)
class CarRentalCompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'is_preferred', 'has_corporate_rate',
                    'account_manager_name', 'is_active']
    list_filter = ['tier', 'is_preferred', 'has_corporate_rate', 'is_active']
    search_fields = ['name', 'alternative_names', 'account_manager_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'alternative_names', 'website')
        }),
        ('Supplier Status', {
            'fields': ('is_preferred', 'tier', 'is_active')
        }),
        ('Corporate Rates', {
            'fields': ('has_corporate_rate', 'corporate_discount_percentage')
        }),
        ('Account Manager', {
            'fields': ('account_manager_name', 'account_manager_email', 'account_manager_phone'),
            'classes': ('collapse',)
        }),
        ('Contract Details', {
            'fields': ('contract_start_date', 'contract_end_date'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['alpha_3', 'name', 'alpha_2', 'region', 'subregion',
                    'currency_code', 'is_active']
    list_filter = ['region', 'subregion', 'is_active']
    search_fields = ['name', 'common_name', 'alpha_2', 'alpha_3']

    fieldsets = (
        ('ISO Codes', {
            'fields': ('alpha_3', 'alpha_2', 'numeric_code')
        }),
        ('Names', {
            'fields': ('name', 'common_name')
        }),
        ('Regional Classification', {
            'fields': ('region', 'subregion')
        }),
        ('Travel Details', {
            'fields': ('currency_code', 'phone_prefix')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


# ============================================================================
# HOTEL MASTER DATA ADMIN
# ============================================================================

class HotelAliasInline(admin.TabularInline):
    """Inline display of hotel aliases"""
    model = HotelAlias
    extra = 1
    fields = ['alias_name', 'reason', 'is_active', 'notes']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    """
    Admin for Hotel master data.

    Use this to:
    - Create canonical hotel records
    - Manage hotel aliases (previous names, rebrands)
    - Merge duplicate hotels
    """
    list_display = ['canonical_name', 'hotel_chain', 'city', 'country',
                    'is_active', 'alias_count', 'booking_count']
    list_filter = ['is_active', 'hotel_chain', 'country']
    search_fields = ['canonical_name', 'hotel_chain', 'city', 'aliases__alias_name']
    inlines = [HotelAliasInline]

    fieldsets = (
        ('Canonical Name', {
            'fields': ('canonical_name',),
            'description': 'This is the official/current name shown everywhere'
        }),
        ('Hotel Details', {
            'fields': ('hotel_chain', 'city', 'country')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def alias_count(self, obj):
        """Number of active aliases"""
        return obj.aliases.filter(is_active=True).count()
    alias_count.short_description = 'Aliases'

    def booking_count(self, obj):
        """Number of bookings linked to this hotel"""
        return obj.bookings.count()
    booking_count.short_description = 'Bookings'


@admin.register(HotelAlias)
class HotelAliasAdmin(admin.ModelAdmin):
    """
    Admin for hotel aliases.

    Create aliases when:
    - Hotel rebrands (e.g., "Sheraton" → "Marriott")
    - Common misspellings
    - Abbreviations
    """
    list_display = ['alias_name', 'hotel', 'reason', 'is_active', 'created_at']
    list_filter = ['is_active', 'reason', 'hotel__hotel_chain']
    search_fields = ['alias_name', 'hotel__canonical_name', 'hotel__hotel_chain']

    fieldsets = (
        ('Alias Details', {
            'fields': ('hotel', 'alias_name')
        }),
        ('Reason', {
            'fields': ('reason', 'notes')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']