from rest_framework import serializers
from apps.organizations.models import Organization
from apps.users.models import User
from apps.bookings.models import (
    Traveller, Booking, AirBooking, AirSegment,
    AccommodationBooking, CarHireBooking, Invoice, ServiceFee
)
from apps.budgets.models import FiscalYear, Budget, BudgetAlert
from apps.compliance.models import (
    ComplianceRule, ComplianceViolation,
    HighRiskDestination, TravelRiskAlert
)
from apps.reference_data.models import Airport, Airline, CurrencyExchangeRate
from apps.commissions.models import Commission


# ============================================================================
# USER & ORGANIZATION SERIALIZERS
# ============================================================================

class OrganizationSerializer(serializers.ModelSerializer):
    """Basic organization info"""
    travel_agent_name = serializers.CharField(source='travel_agent.name', read_only=True)
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'code', 'org_type', 'base_currency',
            'contact_email', 'contact_phone', 'travel_agent_name',
            'is_active', 'subscription_status'
        ]
        read_only_fields = ['id', 'code']


class UserSerializer(serializers.ModelSerializer):
    """User info for authentication and profile"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'phone', 'organization', 'organization_name',
            'is_active'
        ]
        read_only_fields = ['id', 'username']
        extra_kwargs = {
            'password': {'write_only': True}
        }


# ============================================================================
# TRAVELLER SERIALIZERS
# ============================================================================

class TravellerListSerializer(serializers.ModelSerializer):
    """Lightweight for lists"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Traveller
        fields = [
            'id', 'full_name', 'email', 'employee_id',
            'organization_name', 'cost_center', 'department', 'is_active'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class TravellerDetailSerializer(serializers.ModelSerializer):
    """Detailed traveller info"""
    organization = OrganizationSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Traveller
        fields = [
            'id', 'organization', 'user', 'first_name', 'last_name',
            'email', 'employee_id', 'department', 'cost_center', 
            'is_active', 'created_at', 'updated_at'
        ]


# ============================================================================
# BOOKING SERIALIZERS
# ============================================================================

class AirSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirSegment
        fields = [
            'id', 'segment_number', 'airline_iata_code', 'airline_name',  # Updated
            'flight_number', 'origin_airport_iata_code', 'destination_airport_iata_code',  # Updated
            'departure_date', 'departure_time', 'arrival_date', 'arrival_time',
            'booking_class', 'fare_basis', 'distance_km',
            'carbon_emissions_kg'  # NEW
        ]


class AirBookingSerializer(serializers.ModelSerializer):
    segments = AirSegmentSerializer(many=True, read_only=True)
    total_carbon_kg = serializers.SerializerMethodField()
    
    class Meta:
        model = AirBooking
        fields = [
            'id', 'trip_type', 'travel_class', 'ticket_number',
            'primary_airline_iata_code', 'primary_airline_name', 
            'origin_airport_iata_code', 'destination_airport_iata_code', 
            'lowest_fare_available', 'lowest_fare_currency', 'potential_savings', 
            'segments', 'total_carbon_kg'
        ]
    
    def get_total_carbon_kg(self, obj):
        """Sum carbon emissions across all segments"""
        total = sum(
            segment.carbon_emissions_kg or 0 
            for segment in obj.segments.all()
        )
        return round(total, 2)


class AccommodationBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationBooking
        fields = [
            'id', 'hotel_name', 'hotel_chain', 'city', 'country',
            'address', 'check_in_date', 'check_out_date',
            'number_of_nights', 'room_type', 'nightly_rate',
            'currency', 'nightly_rate_base', 'total_amount_base'
        ]


class CarHireBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarHireBooking
        fields = [
            'id', 'rental_company', 'vehicle_type', 'vehicle_class',
            'pickup_location', 'dropoff_location', 'pickup_city',
            'pickup_date', 'pickup_time', 'dropoff_date', 'dropoff_time',
            'number_of_days', 'daily_rate', 'currency',
            'daily_rate_base', 'total_amount_base'
        ]


class BookingListSerializer(serializers.ModelSerializer):
    """For list views - lightweight"""
    traveller_name = serializers.CharField(source='traveller.__str__', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'agent_booking_reference', 'supplier_reference',
            'booking_type', 'booking_date', 'travel_date', 'return_date',
            'status', 'traveller_name', 'organization_name',
            'currency', 'total_amount'
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    """For detail views - full data"""
    traveller = TravellerListSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    air_details = AirBookingSerializer(read_only=True)
    accommodation_details = AccommodationBookingSerializer(read_only=True)
    car_hire_details = CarHireBookingSerializer(read_only=True)
    travel_arranger_name = serializers.CharField(source='travel_arranger.__str__', read_only=True)
    travel_consultant_name = serializers.CharField(source='travel_consultant.__str__', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'organization', 'traveller', 'agent_booking_reference',
            'supplier_reference', 'booking_type', 'booking_date',
            'travel_date', 'return_date', 'status', 'currency',
            'total_amount', 'base_fare', 'taxes', 'fees',
            'total_amount_base', 'base_fare_base', 'taxes_base', 'fees_base',
            'exchange_rate', 'exchange_rate_date', 
            'travel_arranger', 'travel_arranger_name', 'travel_arranger_text',
            'travel_consultant', 'travel_consultant_name', 'travel_consultant_text',
            'air_details', 'accommodation_details', 'car_hire_details',
            'created_at', 'updated_at'
        ]


# ============================================================================
# BUDGET SERIALIZERS
# ============================================================================

class FiscalYearSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = FiscalYear
        fields = [
            'id', 'organization', 'organization_name', 'fiscal_year_type',
            'year_label', 'start_date', 'end_date', 'is_active', 'is_current'
        ]


class BudgetSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    fiscal_year_label = serializers.CharField(source='fiscal_year.year_label', read_only=True)
    budget_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = [
            'id', 'organization', 'organization_name', 'fiscal_year',
            'fiscal_year_label', 'cost_center', 'cost_center_name',
            'total_budget', 'air_budget', 'accommodation_budget',
            'car_hire_budget', 'other_budget', 'currency',
            'warning_threshold', 'critical_threshold', 'budget_status',
            'is_active', 'notes'
        ]
    
    def get_budget_status(self, obj):
        """Get current budget utilization"""
        return obj.get_budget_status()


class BudgetAlertSerializer(serializers.ModelSerializer):
    budget_detail = serializers.CharField(source='budget.__str__', read_only=True)
    
    class Meta:
        model = BudgetAlert
        fields = [
            'id', 'budget', 'budget_detail', 'alert_type',
            'percentage_used', 'amount_spent', 'is_acknowledged',
            'acknowledged_by', 'acknowledged_at', 'created_at'
        ]


# ============================================================================
# COMPLIANCE SERIALIZERS
# ============================================================================

class ComplianceViolationSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source='booking.agent_booking_reference', read_only=True)
    traveller_name = serializers.CharField(source='traveller.__str__', read_only=True)
    
    class Meta:
        model = ComplianceViolation
        fields = [
            'id', 'booking', 'booking_reference', 'traveller', 'traveller_name',
            'violation_type', 'violation_description', 'severity',
            'expected_amount', 'actual_amount', 'variance_amount', 'currency',
            'is_waived', 'waived_by', 'waiver_reason', 'detected_at'
        ]


class TravelRiskAlertSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source='booking.agent_booking_reference', read_only=True)
    traveller_name = serializers.CharField(source='traveller.__str__', read_only=True)
    destination_name = serializers.CharField(source='high_risk_destination.__str__', read_only=True)
    
    class Meta:
        model = TravelRiskAlert
        fields = [
            'id', 'booking', 'booking_reference', 'traveller', 'traveller_name',
            'high_risk_destination', 'destination_name', 'alert_status',
            'risk_level_at_booking', 'matched_location', 'approval_notes',
            'approved_by', 'approval_decision_at', 'created_at'
        ]


# ============================================================================
# REFERENCE DATA SERIALIZERS
# ============================================================================

class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ['iata_code', 'name', 'city', 'country', 'latitude', 'longitude', 'timezone']


class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ['iata_code', 'name', 'country', 'alliance']


class CurrencyExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyExchangeRate
        fields = [
            'id', 'from_currency', 'to_currency', 'exchange_rate',
            'rate_date', 'rate_source'
        ]

class CommissionSerializer(serializers.ModelSerializer):
    """Commission records with booking details"""
    booking_reference = serializers.CharField(
        source='booking.agent_booking_reference', 
        read_only=True
    )
    supplier_reference_booking = serializers.CharField(
        source='booking.supplier_reference', 
        read_only=True
    )
    organization_name = serializers.CharField(
        source='organization.name', 
        read_only=True
    )
    booking_type = serializers.CharField(
        source='booking.booking_type', 
        read_only=True
    )
    booking_date = serializers.DateField(
        source='booking.booking_date', 
        read_only=True
    )
    commission_rate_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Commission
        fields = [
            'id', 'booking', 'booking_reference', 
            'supplier_reference_booking', 'organization', 'organization_name',
            'product_type', 'booking_type', 'booking_date', 'supplier_name',
            'commission_amount', 'currency', 'commission_amount_base',
            'booking_amount', 'commission_rate_percentage', 'earned_date',
            'commission_period', 'notes', 'created_at', 'updated_at',
            'exchange_rate', 'exchange_rate_date', 'import_batch',
            'supplier_reference'  # This is the actual model field
        ]
    
    def get_commission_rate_percentage(self, obj):
        """Calculate commission rate as percentage"""
        if obj.booking_amount and obj.booking_amount > 0:
            return round((obj.commission_amount / obj.booking_amount) * 100, 2)
        return None