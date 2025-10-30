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
    date_hierarchy = 'effective_from'
    
    fieldsets = (
        ('Rule Definition', {
            'fields': ('organization', 'rule_name', 'rule_description', 'rule_type', 'product_type')
        }),
        ('Rule Parameters', {
            'fields': ('rule_parameters',),
            'description': 'JSON configuration for rule-specific parameters'
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
    list_display = ['booking', 'traveller', 'violation_type', 'severity', 
                    'variance_amount', 'is_waived', 'detected_at']
    list_filter = ['violation_type', 'severity', 'is_waived', 'organization', 'detected_by']
    search_fields = ['booking__agent_booking_reference', 'traveller__first_name', 
                    'traveller__last_name', 'violation_description']
    date_hierarchy = 'detected_at'
    
    fieldsets = (
        ('Violation Details', {
            'fields': ('organization', 'booking', 'traveller', 'compliance_rule')
        }),
        ('Violation Information', {
            'fields': ('violation_type', 'severity', 'violation_description')
        }),
        ('Financial Impact', {
            'fields': ('expected_amount', 'actual_amount', 'variance_amount', 'currency'),
            'classes': ('collapse',)
        }),
        ('Detection', {
            'fields': ('detected_by',),
            'classes': ('collapse',)
        }),
        ('Resolution', {
            'fields': ('is_waived', 'waived_by', 'waived_at', 'waiver_reason')
        }),
    )
    
    readonly_fields = ['detected_at', 'created_at', 'updated_at']


@admin.register(ComplianceProcessingLog)
class ComplianceProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['organization', 'processing_type', 'status', 'bookings_processed',
                    'violations_detected', 'started_at', 'completed_at']
    list_filter = ['processing_type', 'status', 'organization', 'booking_type']
    search_fields = ['organization__name', 'error_message']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Processing Details', {
            'fields': ('organization', 'processing_type', 'status')
        }),
        ('Scope', {
            'fields': ('start_date', 'end_date', 'booking_type')
        }),
        ('Statistics', {
            'fields': ('bookings_processed', 'violations_detected', 'violations_resolved')
        }),
        ('Timing', {
            'fields': ('completed_at',)
        }),
        ('Errors', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('User Tracking', {
            'fields': ('initiated_by',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['started_at']


@admin.register(HighRiskDestination)
class HighRiskDestinationAdmin(admin.ModelAdmin):
    list_display = ['country_name', 'organization', 'destination_type', 'risk_level',
                    'approval_required', 'is_active', 'effective_from']
    list_filter = ['risk_level', 'destination_type', 'approval_required', 'is_active',
                   'organization', 'notify_immediately']
    search_fields = ['country_name', 'country_code', 'region_name', 'city_name',
                    'risk_description']
    date_hierarchy = 'effective_from'
    filter_horizontal = ['notification_recipients']
    
    fieldsets = (
        ('Organization', {
            'fields': ('organization',)
        }),
        ('Destination', {
            'fields': ('destination_type', 'country_code', 'country_name', 
                      'region_name', 'city_name')
        }),
        ('Radius-Based Tracking', {
            'fields': ('center_latitude', 'center_longitude', 'radius_km'),
            'classes': ('collapse',),
            'description': 'Only applicable for RADIUS destination type'
        }),
        ('Risk Assessment', {
            'fields': ('risk_level', 'risk_description')
        }),
        ('Advisory Information', {
            'fields': ('advisory_source', 'advisory_url', 'advisory_date'),
            'classes': ('collapse',)
        }),
        ('Policy', {
            'fields': ('approval_required', 'allow_travel')
        }),
        ('Notifications', {
            'fields': ('notify_immediately', 'notification_recipients')
        }),
        ('Status', {
            'fields': ('is_active', 'effective_from', 'effective_until')
        }),
        ('Metadata', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TravelRiskAlert)
class TravelRiskAlertAdmin(admin.ModelAdmin):
    list_display = ['traveller', 'matched_location', 'risk_level_at_booking',
                    'alert_status', 'approval_requested_at', 'approved_by']
    list_filter = ['alert_status', 'risk_level_at_booking', 'organization',
                   'emergency_contact_verified', 'travel_insurance_confirmed',
                   'safety_briefing_completed']
    search_fields = ['booking__agent_booking_reference', 'traveller__first_name',
                    'traveller__last_name', 'matched_location']
    date_hierarchy = 'approval_requested_at'
    
    fieldsets = (
        ('Alert Details', {
            'fields': ('organization', 'booking', 'traveller', 'high_risk_destination')
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