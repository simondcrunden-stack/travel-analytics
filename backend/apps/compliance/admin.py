from django.contrib import admin
from .models import (
    ComplianceRule, 
    ComplianceViolation, 
    ComplianceProcessingLog,
    HighRiskDestination,
    TravelRiskAlert
)


@admin.register(ComplianceRule)
class ComplianceRuleAdmin(admin.ModelAdmin):
    list_display = ['rule_name', 'organization', 'rule_type', 'product_type', 
                    'is_active', 'is_enforced', 'priority']
    list_filter = ['rule_type', 'product_type', 'is_active', 'is_enforced', 'organization']
    search_fields = ['rule_name', 'rule_description', 'organization__name']
    
    fieldsets = (
        ('Organization', {
            'fields': ('organization',)
        }),
        ('Rule Definition', {
            'fields': ('rule_type', 'rule_name', 'rule_description', 'product_type')
        }),
        ('Rule Parameters', {
            'fields': ('rule_parameters',),
            'description': 'JSON field for flexible rule configuration'
        }),
        ('Status & Enforcement', {
            'fields': ('is_active', 'is_enforced', 'priority')
        }),
        ('Effective Period', {
            'fields': ('effective_from', 'effective_until')
        }),
        ('Metadata', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ComplianceViolation)
class ComplianceViolationAdmin(admin.ModelAdmin):
    list_display = ['traveller', 'violation_type', 'severity', 'booking', 
                    'variance_amount', 'is_waived', 'detected_at']
    list_filter = ['violation_type', 'severity', 'is_waived', 'detected_by', 'organization']
    search_fields = ['traveller__first_name', 'traveller__last_name', 
                    'violation_description', 'booking__booking_reference']
    date_hierarchy = 'detected_at'
    
    fieldsets = (
        ('Violation Details', {
            'fields': ('booking', 'compliance_rule', 'organization', 'traveller')
        }),
        ('Violation Info', {
            'fields': ('violation_type', 'violation_description', 'severity')
        }),
        ('Financial Impact', {
            'fields': ('expected_amount', 'actual_amount', 'variance_amount', 'currency'),
            'classes': ('collapse',)
        }),
        ('Detection', {
            'fields': ('detected_by',)
        }),
        ('Resolution', {
            'fields': ('is_waived', 'waived_by', 'waived_at', 'waiver_reason'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['detected_at', 'created_at', 'updated_at']


@admin.register(ComplianceProcessingLog)
class ComplianceProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['organization', 'processing_type', 'status', 'bookings_processed',
                    'violations_detected', 'started_at', 'completed_at']
    list_filter = ['processing_type', 'status', 'booking_type', 'organization']
    search_fields = ['organization__name', 'error_message']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Processing Info', {
            'fields': ('organization', 'processing_type', 'status')
        }),
        ('Scope', {
            'fields': ('start_date', 'end_date', 'booking_type')
        }),
        ('Statistics', {
            'fields': ('bookings_processed', 'violations_detected', 'violations_resolved')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Error Info', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('User', {
            'fields': ('initiated_by',)
        }),
    )
    
    readonly_fields = ['started_at']


@admin.register(HighRiskDestination)
class HighRiskDestinationAdmin(admin.ModelAdmin):
    list_display = ['country_name', 'destination_type', 'risk_level', 'organization',
                    'approval_required', 'is_active']
    list_filter = ['risk_level', 'destination_type', 'approval_required', 
                   'is_active', 'organization']
    search_fields = ['country_name', 'region_name', 'city_name', 'country_code']
    
    fieldsets = (
        ('Organization', {
            'fields': ('organization',)
        }),
        ('Destination', {
            'fields': ('destination_type', 'country_code', 'country_name', 
                      'region_name', 'city_name')
        }),
        ('Radius Tracking', {
            'fields': ('center_latitude', 'center_longitude', 'radius_km'),
            'classes': ('collapse',),
            'description': 'For RADIUS destination type only'
        }),
        ('Risk Assessment', {
            'fields': ('risk_level', 'risk_description')
        }),
        ('Advisory Information', {
            'fields': ('advisory_source', 'advisory_url', 'advisory_date'),
            'classes': ('collapse',)
        }),
        ('Policy & Notifications', {
            'fields': ('approval_required', 'allow_travel', 'notify_immediately', 
                      'notification_recipients')
        }),
        ('Effective Period', {
            'fields': ('is_active', 'effective_from', 'effective_until')
        }),
        ('Metadata', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['notification_recipients']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TravelRiskAlert)
class TravelRiskAlertAdmin(admin.ModelAdmin):
    list_display = ['traveller', 'matched_location', 'risk_level_at_booking', 
                    'alert_status', 'approval_requested_at']
    list_filter = ['alert_status', 'risk_level_at_booking', 'emergency_contact_verified',
                   'travel_insurance_confirmed', 'organization']
    search_fields = ['traveller__first_name', 'traveller__last_name', 
                    'matched_location', 'booking__booking_reference']
    date_hierarchy = 'approval_requested_at'
    
    fieldsets = (
        ('Alert Details', {
            'fields': ('booking', 'high_risk_destination', 'organization', 'traveller')
        }),
        ('Risk Information', {
            'fields': ('alert_status', 'risk_level_at_booking', 'matched_location', 
                      'distance_from_center_km')
        }),
        ('Approval Workflow', {
            'fields': ('approval_notes', 'approved_by', 'approval_decision_at', 
                      'approval_comments')
        }),
        ('Safety Measures', {
            'fields': ('emergency_contact_verified', 'travel_insurance_confirmed', 
                      'safety_briefing_completed')
        }),
        ('Notifications', {
            'fields': ('traveller_notified', 'traveller_notified_at', 
                      'admins_notified', 'admins_notified_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['approval_requested_at', 'created_at', 'updated_at']