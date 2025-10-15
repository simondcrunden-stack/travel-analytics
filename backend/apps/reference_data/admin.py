from django.contrib import admin
from .models import Airport, Airline, CurrencyExchangeRate
from .models import Airport, Airline, CurrencyExchangeRate, HotelChain, CarRentalCompany


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
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
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