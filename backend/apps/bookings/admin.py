# apps/bookings/admin.py
# CORRECTED ADMIN - Session 26

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from decimal import Decimal
from .models import (
    Traveller, Booking, AirBooking, AirSegment, 
    AccommodationBooking, CarHireBooking, Invoice, ServiceFee, BookingTransaction, BookingAuditLog
)


# ============================================================================
# INLINE ADMINS (for showing related objects)
# ============================================================================

class AirSegmentInline(admin.TabularInline):
    model = AirSegment
    extra = 0
    fields = ['segment_number', 'airline_iata_code', 'airline_name', 'flight_number', 
              'origin_airport_iata_code', 'destination_airport_iata_code', 
              'departure_date', 'departure_time', 'distance_km', 'carbon_emissions_kg']
    readonly_fields = ['distance_km', 'carbon_emissions_kg']
    show_change_link = True
    
    class Media:
        css = {
            'all': ('admin/css/custom_inline_widths.css',)
        }
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        from django import forms
        
        # Segment number - very narrow
        if 'segment_number' in formset.form.base_fields:
            formset.form.base_fields['segment_number'].widget.attrs.update({
                'style': 'width: 50px;'
            })
        
        # Airline IATA code - narrow (2-3 chars)
        if 'airline_iata_code' in formset.form.base_fields:
            formset.form.base_fields['airline_iata_code'].widget = forms.TextInput(attrs={
                'style': 'width: 50px;',
                'maxlength': '3'
            })
        
        # Airline name - medium
        if 'airline_name' in formset.form.base_fields:
            formset.form.base_fields['airline_name'].widget = forms.TextInput(attrs={
                'style': 'width: 130px;'
            })
        
        # Flight number - narrow
        if 'flight_number' in formset.form.base_fields:
            formset.form.base_fields['flight_number'].widget = forms.TextInput(attrs={
                'style': 'width: 80px;'
            })
        
        # Airport IATA codes - narrow (3 chars)
        for field_name in ['origin_airport_iata_code', 'destination_airport_iata_code']:
            if field_name in formset.form.base_fields:
                formset.form.base_fields[field_name].widget = forms.TextInput(attrs={
                    'style': 'width: 50px;',
                    'maxlength': '3'
                })
        
        # Departure date - medium
        if 'departure_date' in formset.form.base_fields:
            formset.form.base_fields['departure_date'].widget.attrs.update({
                'style': 'width: 110px;'
            })
        
        # Departure time - narrow
        if 'departure_time' in formset.form.base_fields:
            formset.form.base_fields['departure_time'].widget.attrs.update({
                'style': 'width: 80px;'
            })
        
        # Distance - narrow (readonly)
        if 'distance_km' in formset.form.base_fields:
            formset.form.base_fields['distance_km'].widget.attrs.update({
                'style': 'width: 70px;'
            })
        
        # Carbon - narrow (readonly)
        if 'carbon_emissions_kg' in formset.form.base_fields:
            formset.form.base_fields['carbon_emissions_kg'].widget.attrs.update({
                'style': 'width: 70px;'
            })
        
        return formset

class AirBookingInline(admin.TabularInline):
    """Show air bookings within a main Booking"""
    model = AirBooking
    extra = 0
    fields = ['trip_type', 'travel_class', 'origin_airport_iata_code', 
              'destination_airport_iata_code', 'ticket_number', 'total_fare']
    show_change_link = True  # Allows clicking to see full air booking with segments

class AccommodationBookingInline(admin.TabularInline):
    """Show accommodation bookings within a main Booking"""
    model = AccommodationBooking
    extra = 0
    fields = ['hotel_name', 'city', 'country', 'check_in_date', 
              'check_out_date', 'number_of_nights', 'nightly_rate']

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        from django import forms
        
        # Hotel name - wider
        if 'hotel_name' in formset.form.base_fields:
            formset.form.base_fields['hotel_name'].widget = forms.TextInput(attrs={
                'style': 'width: 200px;'
            })
        
        # City - medium
        if 'city' in formset.form.base_fields:
            formset.form.base_fields['city'].widget = forms.TextInput(attrs={
                'style': 'width: 120px;'
            })
        
        # Country code - narrow
        if 'country' in formset.form.base_fields:
            formset.form.base_fields['country'].widget = forms.TextInput(attrs={
                'style': 'width: 60px;',
                'maxlength': '3'
            })
        
        # Dates - medium
        if 'check_in_date' in formset.form.base_fields:
            formset.form.base_fields['check_in_date'].widget.attrs.update({
                'style': 'width: 110px;'
            })
        
        if 'check_out_date' in formset.form.base_fields:
            formset.form.base_fields['check_out_date'].widget.attrs.update({
                'style': 'width: 110px;'
            })
        
        # Number of nights - very narrow
        if 'number_of_nights' in formset.form.base_fields:
            formset.form.base_fields['number_of_nights'].widget.attrs.update({
                'style': 'width: 60px;'
            })
        
        # Nightly rate - narrow
        if 'nightly_rate' in formset.form.base_fields:
            formset.form.base_fields['nightly_rate'].widget.attrs.update({
                'style': 'width: 90px;'
            })
        
        return formset

class CarHireBookingInline(admin.TabularInline):
    """Show car hire bookings within a main Booking"""
    model = CarHireBooking
    extra = 0
    fields = ['rental_company', 'vehicle_type', 'pickup_city', 'country',
              'pickup_date', 'dropoff_date', 'number_of_days', 'daily_rate']

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        from django import forms
        
        # Rental company - medium
        if 'rental_company' in formset.form.base_fields:
            formset.form.base_fields['rental_company'].widget = forms.TextInput(attrs={
                'style': 'width: 130px;'
            })
        
        # Vehicle type - medium
        if 'vehicle_type' in formset.form.base_fields:
            formset.form.base_fields['vehicle_type'].widget = forms.TextInput(attrs={
                'style': 'width: 120px;'
            })
        
        # Pickup city - medium
        if 'pickup_city' in formset.form.base_fields:
            formset.form.base_fields['pickup_city'].widget = forms.TextInput(attrs={
                'style': 'width: 120px;'
            })
        
        # Country - narrow (3-char code)
        if 'country' in formset.form.base_fields:
            formset.form.base_fields['country'].widget = forms.TextInput(attrs={
                'style': 'width: 60px;',
                'maxlength': '3'
            })
        
        # Dates - medium
        if 'pickup_date' in formset.form.base_fields:
            formset.form.base_fields['pickup_date'].widget.attrs.update({
                'style': 'width: 110px;'
            })
        
        if 'dropoff_date' in formset.form.base_fields:
            formset.form.base_fields['dropoff_date'].widget.attrs.update({
                'style': 'width: 110px;'
            })
        
        # Number of days - very narrow
        if 'number_of_days' in formset.form.base_fields:
            formset.form.base_fields['number_of_days'].widget.attrs.update({
                'style': 'width: 60px;'
            })
        
        # Daily rate - narrow
        if 'daily_rate' in formset.form.base_fields:
            formset.form.base_fields['daily_rate'].widget.attrs.update({
                'style': 'width: 90px;'
            })
        
        return formset

class ServiceFeeInline(admin.TabularInline):
    """Show service fees within a main Booking"""
    model = ServiceFee
    extra = 0
    fields = ['fee_type', 'fee_date', 'fee_amount', 'booking_channel']

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        from django import forms
        
        # Fee type - dropdown medium
        if 'fee_type' in formset.form.base_fields:
            formset.form.base_fields['fee_type'].widget.attrs.update({
                'style': 'width: 120px;'
            })
        
        # Fee date - medium
        if 'fee_date' in formset.form.base_fields:
            formset.form.base_fields['fee_date'].widget.attrs.update({
                'style': 'width: 110px;'
            })
        
        # Fee amount - narrow
        if 'fee_amount' in formset.form.base_fields:
            formset.form.base_fields['fee_amount'].widget.attrs.update({
                'style': 'width: 90px;'
            })
        
        # Booking channel - medium
        if 'booking_channel' in formset.form.base_fields:
            formset.form.base_fields['booking_channel'].widget = forms.TextInput(attrs={
                'style': 'width: 120px;'
            })
        
        return formset

@admin.register(BookingTransaction)
class BookingTransactionAdmin(admin.ModelAdmin):

    """
    Main admin interface for BookingTransaction model.
    Provides comprehensive view of all booking amendments.
    """
    
    list_display = [
        'transaction_date',
        'transaction_type',
        'booking_reference_link',
        'booking_type_display',
        'status_badge',
        'amount_display',
        'currency',
        'transaction_reference',
    ]
    
    list_filter = [
        'transaction_type',
        'status',
        'currency',
        'transaction_date',
        'content_type',
    ]
    
    search_fields = [
        'transaction_reference',
        'reason',
        'notes',
        # Note: Can't directly search booking reference via GenericForeignKey
        # Users can filter by content_type then search
    ]
    
    date_hierarchy = 'transaction_date'
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'booking_reference_link',
        'booking_component_link',
        'amount_breakdown',
        'base_currency_breakdown',
    ]
    
    fieldsets = (
        ('Transaction Information', {
            'fields': (
                'content_type',
                'object_id',
                'booking_component_link',
                'booking_reference_link',
                'transaction_type',
                'transaction_date',
                'transaction_reference',
                'status',
            )
        }),
        ('Financial Details (Original Currency)', {
            'fields': (
                'currency',
                'base_amount',
                'taxes',
                'fees',
                'total_amount',
                'amount_breakdown',
            ),
            'classes': ('collapse',),
        }),
        ('Financial Details (Base Currency)', {
            'fields': (
                'base_amount_base',
                'taxes_base',
                'fees_base',
                'total_amount_base',
                'exchange_rate',
                'base_currency_breakdown',
            ),
            'classes': ('collapse',),
        }),
        ('Details', {
            'fields': (
                'reason',
                'notes',
            )
        }),
        ('Audit Trail', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # =============================================================================
    # CUSTOM DISPLAY METHODS
    # =============================================================================
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        """Display status with color-coded badge"""
        colors = {
            'PENDING': '#FFA500',  # Orange
            'CONFIRMED': '#28A745',  # Green
            'CANCELLED': '#DC3545',  # Red
            'REFUNDED': '#6C757D',  # Gray
        }
        color = colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @admin.display(description='Amount', ordering='total_amount')
    def amount_display(self, obj):
        """Display amount with color coding (red for refunds, green for charges)"""
        if obj.total_amount < 0:
            # Refund - show in red
            amount_str = f"{abs(obj.total_amount):,.2f}"
            return format_html(
                '<span style="color: #DC3545; font-weight: bold;">({})</span>',
                amount_str
            )
        else:
            # Charge - show in green
            amount_str = f"{obj.total_amount:,.2f}"
            return format_html(
                '<span style="color: #28A745; font-weight: bold;">{}</span>',
                amount_str
            )
    
    @admin.display(description='Booking Type')
    def booking_type_display(self, obj):
        """Display the type of booking component"""
        if obj.content_type:
            return obj.content_type.model.replace('booking', '').title()
        return 'N/A'
    
    @admin.display(description='Booking Reference')
    def booking_reference_link(self, obj):
        """Display booking reference as clickable link"""
        try:
            booking = obj.booking_component.booking
            url = reverse('admin:bookings_booking_change', args=[booking.pk])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                booking.agent_booking_reference
            )
        except AttributeError:
            return 'N/A'
    
    @admin.display(description='Booking Component')
    def booking_component_link(self, obj):
        """Display link to the actual booking component (Air/Accommodation/Car)"""
        if not obj.content_type or not obj.object_id:
            return 'N/A'
        
        try:
            app_label = obj.content_type.app_label
            model_name = obj.content_type.model
            url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.object_id])
            return format_html(
                '<a href="{}">{} Details</a>',
                url,
                obj.content_type.model.replace('booking', '').title()
            )
        except:
            return 'N/A'
    
    @admin.display(description='Amount Breakdown')
    def amount_breakdown(self, obj):
        """Show breakdown of transaction amount"""
        if obj.amount:
            base = obj.amount_base or 0  # ← Add default of 0
            gst = obj.gst_amount or 0     # ← Add default of 0
            return format_html(
                '<strong>Amount:</strong> {}<br>'
                '<strong>Base:</strong> {}<br>'
                '<strong>GST:</strong> {}',
                f'{obj.amount:,.2f}' if obj.amount else '0.00',
                f'{base:,.2f}',
                f'{gst:,.2f}'
            )
        
        return format_html(
            '<table style="font-size: 11px;">'
            '<tr><td>Base:</td><td style="text-align: right;">{}</td></tr>'
            '<tr><td>Taxes:</td><td style="text-align: right;">{}</td></tr>'
            '<tr><td>Fees:</td><td style="text-align: right;">{}</td></tr>'
            '<tr style="border-top: 1px solid #ccc; font-weight: bold;">'
            '<td>Total:</td><td style="text-align: right;">{}</td></tr>'
            '</table>',
            base_str, taxes_str, fees_str, total_str
        )
    
    @admin.display(description='Base Currency Breakdown')
    def base_currency_breakdown(self, obj):
        if not obj.total_amount_base:
            return 'Not converted'
        try:
            base_curr = obj.booking_component.booking.organization.base_currency
        except:
            base_curr = 'BASE'
        
        base_str = f"{obj.base_amount_base:,.2f}"
        taxes_str = f"{obj.taxes_base:,.2f}"
        fees_str = f"{obj.fees_base:,.2f}"
        total_str = f"{obj.total_amount_base:,.2f}"
        rate_str = str(obj.exchange_rate) if obj.exchange_rate else 'N/A'
        
        return format_html(
            '<table style="font-size: 11px;">'
            '<tr><td>Base:</td><td style="text-align: right;">{} {}</td></tr>'
            '<tr><td>Taxes:</td><td style="text-align: right;">{} {}</td></tr>'
            '<tr><td>Fees:</td><td style="text-align: right;">{} {}</td></tr>'
            '<tr style="border-top: 1px solid #ccc; font-weight: bold;">'
            '<td>Total:</td><td style="text-align: right;">{} {}</td></tr>'
            '<tr style="border-top: 1px solid #ccc; color: #666;">'
            '<td>Rate:</td><td style="text-align: right;">{}</td></tr>'
            '</table>',
            base_str, base_curr,
            taxes_str, base_curr,
            fees_str, base_curr,
            total_str, base_curr,
            rate_str
        )
    
    # =============================================================================
    # ACTIONS
    # =============================================================================
    
    @admin.action(description='Mark as Confirmed')
    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status='CONFIRMED')
        self.message_user(request, f'{updated} transaction(s) marked as confirmed.')
    
    @admin.action(description='Mark as Cancelled')
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='CANCELLED')
        self.message_user(request, f'{updated} transaction(s) marked as cancelled.')
    
    actions = [mark_confirmed, mark_cancelled]

# Booking Audit Log Admin

@admin.register(BookingAuditLog)
class BookingAuditLogAdmin(admin.ModelAdmin):
    """
    Main admin interface for audit logs.
    Read-only view of all booking changes.
    """
    
    list_display = [
        'timestamp_display',
        'booking_link',
        'action_badge',
        'description_short',
        'user_display',
        'related_object_link',
    ]
    
    list_filter = [
        'action',
        'timestamp',
        'user',
        'content_type',
    ]
    
    search_fields = [
        'booking__agent_booking_reference',
        'description',
        'notes',
        'user_repr',
        'related_object_repr',
    ]
    
    date_hierarchy = 'timestamp'
    
    readonly_fields = [
        'id',
        'booking',
        'action',
        'timestamp',
        'content_type',
        'object_id',
        'related_object_repr',
        'field_name',
        'old_value_display',
        'new_value_display',
        'description',
        'notes',
        'user',
        'user_repr',
        'ip_address',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'timestamp',
                'booking',
                'action',
                'description',
            )
        }),
        ('Related Object', {
            'fields': (
                'content_type',
                'object_id',
                'related_object_repr',
            ),
            'classes': ('collapse',),
        }),
        ('Change Details', {
            'fields': (
                'field_name',
                'old_value_display',
                'new_value_display',
            ),
            'classes': ('collapse',),
        }),
        ('User Information', {
            'fields': (
                'user',
                'user_repr',
                'ip_address',
            ),
            'classes': ('collapse',),
        }),
        ('Additional Notes', {
            'fields': (
                'notes',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # Make everything read-only (audit logs should never be modified)
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs (for data cleanup)
        return request.user.is_superuser
    
    # =============================================================================
    # CUSTOM DISPLAY METHODS
    # =============================================================================
    
    @admin.display(description='Timestamp', ordering='timestamp')
    def timestamp_display(self, obj):
        """Display timestamp in readable format"""
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    @admin.display(description='Booking')
    def booking_link(self, obj):
        """Display booking as clickable link"""
        url = reverse('admin:bookings_booking_change', args=[obj.booking.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.booking.agent_booking_reference
        )
    
    @admin.display(description='Action')
    def action_badge(self, obj):
        """Display action with color-coded badge"""
        colors = {
            'TRANSACTION_CREATED': '#28A745',  # Green
            'TRANSACTION_MODIFIED': '#FFA500',  # Orange
            'TRANSACTION_DELETED': '#DC3545',  # Red
            'BOOKING_CREATED': '#28A745',
            'BOOKING_MODIFIED': '#FFA500',
            'BOOKING_DELETED': '#DC3545',
            'COMPONENT_CREATED': '#17A2B8',  # Cyan
            'COMPONENT_MODIFIED': '#FFC107',  # Yellow
            'COMPONENT_DELETED': '#DC3545',
            'TOTAL_RECALCULATED': '#6C757D',  # Gray
            'CURRENCY_CONVERTED': '#6C757D',
            'REFUND_PROCESSED': '#DC3545',
            'NOTE_ADDED': '#17A2B8',
            'SYSTEM_ACTION': '#6C757D',
        }
        
        color = colors.get(obj.action, '#6C757D')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold; white-space: nowrap;">{}</span>',
            color,
            obj.get_action_display()
        )
    
    @admin.display(description='Description')
    def description_short(self, obj):
        """Display truncated description"""
        if len(obj.description) > 80:
            return obj.description[:77] + '...'
        return obj.description
    
    @admin.display(description='User')
    def user_display(self, obj):
        """Display user with link if available"""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user_repr or str(obj.user))
        elif obj.user_repr:
            return obj.user_repr
        else:
            return mark_safe('<em>System</em>')
    
    @admin.display(description='Related Object')
    def related_object_link(self, obj):
        """Display link to related object if it still exists"""
        if not obj.content_type or not obj.object_id:
            return '-'
        
        try:
            app_label = obj.content_type.app_label
            model_name = obj.content_type.model
            url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.object_id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.related_object_repr or f"{model_name} #{obj.object_id}"
            )
        except:
            # Object deleted or URL doesn't exist
            return format_html(
                '<span style="color: #999;">{} (deleted)</span>',
                obj.related_object_repr or 'Object'
            )
    
    @admin.display(description='Old Value')
    def old_value_display(self, obj):
        """Display old value in readable format"""
        if not obj.old_value:
            return '-'
        
        try:
            formatted = json.dumps(obj.old_value, indent=2)
            return format_html('<pre style="margin: 0;">{}</pre>', formatted)
        except:
            return str(obj.old_value)
    
    @admin.display(description='New Value')
    def new_value_display(self, obj):
        """Display new value in readable format"""
        if not obj.new_value:
            return '-'
        
        try:
            formatted = json.dumps(obj.new_value, indent=2)
            return format_html('<pre style="margin: 0;">{}</pre>', formatted)
        except:
            return str(obj.new_value)


# =============================================================================
# INLINE ADMIN FOR BOOKING PAGE
# =============================================================================

class BookingAuditLogInline(admin.TabularInline):
    """
    Show audit log timeline on Booking detail page.
    Provides at-a-glance view of all changes.
    """
    model = BookingAuditLog
    extra = 0
    
    fields = [
        'timestamp_short',
        'action_display',
        'description',
        'user_short',
    ]
    
    readonly_fields = [
        'timestamp_short',
        'action_display',
        'description',
        'user_short',
    ]
    
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    @admin.display(description='Time')
    def timestamp_short(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M')
    
    @admin.display(description='Action')
    def action_display(self, obj):
        return obj.get_action_display()
    
    @admin.display(description='User')
    def user_short(self, obj):
        if obj.user:
            return str(obj.user)
        elif obj.user_repr:
            return obj.user_repr
        return 'System'
    
    class Meta:
        ordering = ['-timestamp']
    
    verbose_name = 'Audit Log Entry'
    verbose_name_plural = 'Audit Trail (Complete Change History)'


# =============================================================================
# USAGE IN BOOKING ADMIN
# =============================================================================
"""
To add audit log timeline to Booking admin page:

In apps/bookings/admin.py:

from .audit_admin import BookingAuditLogInline

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    inlines = [
        AirBookingInline,
        AccommodationBookingInline,
        CarHireBookingInline,
        ServiceFeeInline,
        BookingAuditLogInline,  # ← Add this
    ]
    # ... rest of config

This will show a timeline of all changes at the bottom of every Booking detail page.
"""


# =============================================================================
# CUSTOM ADMIN ACTIONS
# =============================================================================

@admin.action(description='Export selected logs as JSON')
def export_logs_as_json(modeladmin, request, queryset):
    """Export selected audit logs as JSON for external analysis"""
    import json
    from django.http import HttpResponse
    from django.core.serializers.json import DjangoJSONEncoder
    
    logs_data = []
    for log in queryset:
        logs_data.append({
            'timestamp': log.timestamp.isoformat(),
            'booking_reference': log.booking.agent_booking_reference,
            'action': log.get_action_display(),
            'description': log.description,
            'user': log.user_repr or 'System',
            'old_value': log.old_value,
            'new_value': log.new_value,
        })
    
    response = HttpResponse(
        json.dumps(logs_data, indent=2, cls=DjangoJSONEncoder),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="booking_audit_logs.json"'
    return response


# Add the action to the admin
BookingAuditLogAdmin.actions = [export_logs_as_json]


# =============================================================================
# CUSTOM LIST FILTERS
# =============================================================================

class ActionTypeListFilter(admin.SimpleListFilter):
    """Filter audit logs by category of action"""
    title = 'Action Category'
    parameter_name = 'action_category'
    
    def lookups(self, request, model_admin):
        return (
            ('transactions', 'Transaction Changes'),
            ('bookings', 'Booking Changes'),
            ('components', 'Component Changes'),
            ('financial', 'Financial Changes'),
            ('system', 'System Actions'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'transactions':
            return queryset.filter(action__in=[
                'TRANSACTION_CREATED',
                'TRANSACTION_MODIFIED',
                'TRANSACTION_DELETED',
            ])
        elif self.value() == 'bookings':
            return queryset.filter(action__in=[
                'BOOKING_CREATED',
                'BOOKING_MODIFIED',
                'BOOKING_DELETED',
                'BOOKING_STATUS_CHANGED',
            ])
        elif self.value() == 'components':
            return queryset.filter(action__in=[
                'COMPONENT_CREATED',
                'COMPONENT_MODIFIED',
                'COMPONENT_DELETED',
            ])
        elif self.value() == 'financial':
            return queryset.filter(action__in=[
                'TOTAL_RECALCULATED',
                'CURRENCY_CONVERTED',
                'REFUND_PROCESSED',
            ])
        elif self.value() == 'system':
            return queryset.filter(action='SYSTEM_ACTION')
        return queryset

# =============================================================================
# INLINE ADMIN FOR USE IN BOOKING COMPONENT ADMIN PAGES
# =============================================================================

class BookingTransactionInline(GenericTabularInline):
    """
    Inline admin to show transactions within Air/Accommodation/Car booking pages.
    Makes it easy to see all amendments directly on the booking detail page.
    """
    model = BookingTransaction
    ct_field = 'content_type'
    ct_fk_field = 'object_id'
    
    extra = 1
    
    fields = [
        'transaction_date',
        'transaction_type',
        'transaction_reference',
        'base_amount',
        'taxes',
        'fees',
        'total_amount',
        'currency',
        'status',
        'reason',
    ]
    
    readonly_fields = []
    
    verbose_name = 'Transaction'
    verbose_name_plural = 'Transaction History'

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        from django import forms
        
        # Transaction date - medium
        if 'transaction_date' in formset.form.base_fields:
            formset.form.base_fields['transaction_date'].widget.attrs.update({
                'style': 'width: 110px;'
            })
        
        # Transaction type - dropdown medium
        if 'transaction_type' in formset.form.base_fields:
            formset.form.base_fields['transaction_type'].widget.attrs.update({
                'style': 'width: 120px;'
            })
        
        # Transaction reference - medium
        if 'transaction_reference' in formset.form.base_fields:
            formset.form.base_fields['transaction_reference'].widget = forms.TextInput(attrs={
                'style': 'width: 130px;'
            })
        
        # Financial fields - narrow
        for field_name in ['base_amount', 'taxes', 'fees', 'total_amount']:
            if field_name in formset.form.base_fields:
                formset.form.base_fields[field_name].widget.attrs.update({
                    'style': 'width: 80px;'
                })
        
        # Currency - very narrow (3 chars)
        if 'currency' in formset.form.base_fields:
            formset.form.base_fields['currency'].widget = forms.TextInput(attrs={
                'style': 'width: 50px;',
                'maxlength': '3'
            })
        
        # Status - narrow dropdown
        if 'status' in formset.form.base_fields:
            formset.form.base_fields['status'].widget.attrs.update({
                'style': 'width: 100px;'
            })
        
        # Reason - single line, wider for description
        if 'reason' in formset.form.base_fields:
            formset.form.base_fields['reason'].widget = forms.TextInput(attrs={
                'style': 'width: 200px;',
                'placeholder': 'Brief reason'
            })
        
        return formset


# ============================================================================
# MAIN MODEL ADMINS
# ============================================================================

@admin.register(Traveller)
class TravellerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'organization', 'employee_id', 'is_active']
    list_filter = ['organization', 'is_active', 'department']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'user')
        }),
        ('Organization', {
            'fields': ('organization', 'employee_id', 'department', 'cost_center')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # FIXED: Removed 'booking_type' from list_display and list_filter
    list_display = ['agent_booking_reference', 'supplier_reference', 'traveller', 
                    'organization', 'travel_date', 'total_amount', 'currency', 'status']
    list_filter = ['status', 'organization', 'travel_date', 'policy_compliant']  # Removed booking_type
    search_fields = ['agent_booking_reference', 'supplier_reference', 
                     'traveller__first_name', 'traveller__last_name']
    date_hierarchy = 'travel_date'
    
    # NEW: Show all component bookings as inlines
    inlines = [
        AirBookingInline,
        AccommodationBookingInline,
        CarHireBookingInline,
        ServiceFeeInline,
        BookingAuditLogInline,
    ]
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('agent_booking_reference', 'supplier_reference', 'status'),
            'description': 'Master booking reference (e.g., GPT001)'
        }),
        ('Parties', {
            'fields': ('organization', 'traveller', 
                      'travel_arranger', 'travel_arranger_text',
                      'travel_consultant', 'travel_consultant_text')
        }),
        ('Dates', {
            'fields': ('booking_date', 'travel_date', 'return_date')
        }),
        ('Financial', {
            'fields': ('currency', 'total_amount', 'base_fare', 'taxes', 'fees'),
            'description': 'Total amount = sum of all air bookings + hotels + cars + fees'
        }),
        ('Currency Conversion', {
            'fields': ('total_amount_base', 'exchange_rate', 'exchange_rate_date'),
        }),
        ('Compliance', {
            'fields': ('policy_compliant', 'advance_booking_days')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AirBooking)
class AirBookingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'trip_type', 'travel_class', 'origin_airport_iata_code', 
                    'destination_airport_iata_code', 'ticket_number', 'total_fare']
    list_filter = ['trip_type', 'travel_class', 'primary_airline_iata_code']
    search_fields = ['booking__agent_booking_reference', 'ticket_number', 
                    'origin_airport_iata_code', 'destination_airport_iata_code']
    
    inlines = [AirSegmentInline, BookingTransactionInline]
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Flight Details', {
            'fields': ('trip_type', 'travel_class', 'ticket_number')
        }),
        ('Route', {
            'fields': ('origin_airport_iata_code', 'destination_airport_iata_code')
        }),
        ('Airline', {
            'fields': ('primary_airline_iata_code', 'primary_airline_name')
        }),
        ('Financial Breakdown', {
            'fields': ('base_fare', 'taxes', 'gst_amount', 'total_fare')
        }),
        ('Compliance', {
            'fields': ('lowest_fare_available', 'lowest_fare_currency', 'potential_savings')
        }),
    )


@admin.register(AirSegment)
class AirSegmentAdmin(admin.ModelAdmin):
    list_display = ['air_booking', 'segment_number', 'airline_iata_code', 'flight_number',
                    'origin_airport_iata_code', 'destination_airport_iata_code', 
                    'departure_date', 'distance_km', 'carbon_emissions_kg']
    list_filter = ['airline_iata_code', 'departure_date']
    search_fields = ['air_booking__booking__agent_booking_reference', 'flight_number',
                    'origin_airport_iata_code', 'destination_airport_iata_code']
    readonly_fields = ['distance_km', 'carbon_emissions_kg']
    
    fieldsets = (
        ('Air Booking', {
            'fields': ('air_booking', 'segment_number')
        }),
        ('Flight', {
            'fields': ('airline_iata_code', 'airline_name', 'flight_number')
        }),
        ('Route', {
            'fields': ('origin_airport_iata_code', 'destination_airport_iata_code')
        }),
        ('Schedule', {
            'fields': ('departure_date', 'departure_time', 'arrival_date', 'arrival_time')
        }),
        ('Booking Details', {
            'fields': ('booking_class', 'fare_basis')
        }),
        ('Calculated Fields', {
            'fields': ('distance_km', 'carbon_emissions_kg'),
            'description': 'Auto-calculated on save'
        }),
    )


@admin.register(AccommodationBooking)
class AccommodationBookingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'hotel_name', 'city', 'country', 
                    'check_in_date', 'number_of_nights', 'nightly_rate', 'currency']
    list_filter = ['country', 'city', 'hotel_chain']
    search_fields = ['booking__agent_booking_reference', 'hotel_name', 'city']
    
    inlines = [BookingTransactionInline]

    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Hotel', {
            'fields': ('hotel_name', 'hotel_chain')
        }),
        ('Location', {
            'fields': ('city', 'country', 'address')
        }),
        ('Stay Details', {
            'fields': ('check_in_date', 'check_out_date', 'number_of_nights', 'room_type')
        }),
        ('Rate', {
            'fields': ('nightly_rate', 'currency', 'nightly_rate_base', 'total_amount_base')
        }),
    )


@admin.register(CarHireBooking)
class CarHireBookingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'rental_company', 'vehicle_type', 
                    'pickup_city', 'country', 'pickup_date', 'number_of_days', 'daily_rate']
    list_filter = ['country', 'rental_company', 'vehicle_type']
    search_fields = ['booking__agent_booking_reference', 'rental_company', 'pickup_city']
    
    inlines = [BookingTransactionInline]

    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Rental Company & Vehicle', {
            'fields': ('rental_company', 'vehicle_type', 'vehicle_category', 'vehicle_make_model')
        }),
        ('Pickup', {
            'fields': ('pickup_location', 'pickup_city', 'pickup_date', 'pickup_time')
        }),
        ('Dropoff', {
            'fields': ('dropoff_location', 'dropoff_city', 'dropoff_date', 'dropoff_time')
        }),
        ('Location', {
            'fields': ('country',)
        }),
        ('Rate', {
            'fields': ('number_of_days', 'daily_rate', 'currency', 'daily_rate_base', 'total_amount_base')
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    # FIXED: Changed 'invoice_amount' to 'total_amount'
    list_display = ['invoice_number', 'organization', 'invoice_date', 
                    'due_date', 'total_amount', 'payment_status']
    list_filter = ['payment_status', 'organization', 'invoice_date']
    search_fields = ['invoice_number', 'organization__name']
    date_hierarchy = 'invoice_date'
    
    fieldsets = (
        ('Invoice Details', {
            'fields': ('invoice_number', 'invoice_date', 'due_date')
        }),
        ('Related', {
            'fields': ('organization', 'booking')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'gst_amount', 'total_amount', 'currency')
        }),
        ('Payment', {
            'fields': ('payment_status', 'payment_date')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )


@admin.register(ServiceFee)
class ServiceFeeAdmin(admin.ModelAdmin):
    # FIXED: Changed 'amount' to 'fee_amount'
    list_display = ['fee_type', 'organization', 'traveller', 
                    'fee_date', 'fee_amount', 'booking_channel']
    list_filter = ['fee_type', 'organization', 'booking_channel', 'fee_date']
    search_fields = ['organization__name', 'traveller__first_name', 'traveller__last_name']
    date_hierarchy = 'fee_date'
    
    fieldsets = (
        ('Fee Details', {
            'fields': ('fee_type', 'fee_date', 'fee_amount', 'currency')
        }),
        ('Related', {
            'fields': ('booking', 'organization', 'traveller')
        }),
        ('Channel', {
            'fields': ('booking_channel',)
        }),
        ('Import Tracking', {
            'fields': ('import_batch',)
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Make import_batch optional for manual entries"""
        form = super().get_form(request, obj, **kwargs)
        if 'import_batch' in form.base_fields:
            form.base_fields['import_batch'].required = False
        return form