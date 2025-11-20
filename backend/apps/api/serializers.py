from rest_framework import serializers
from apps.organizations.models import Organization, OrganizationalNode
from apps.users.models import User
from apps.bookings.models import (
    Traveller, Booking, AirBooking, AirSegment,
    AccommodationBooking, CarHireBooking, Invoice, ServiceFee, BookingTransaction,
    PreferredAirline
)
from apps.budgets.models import FiscalYear, Budget, BudgetAlert
from apps.compliance.models import (
    ComplianceRule, ComplianceViolation,
    HighRiskDestination, TravelRiskAlert
)
from apps.reference_data.models import Airport, Airline, CurrencyExchangeRate, Country, Hotel
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
# ORGANIZATIONAL HIERARCHY SERIALIZERS
# ============================================================================

class OrganizationalNodeSerializer(serializers.ModelSerializer):
    """Basic organizational node serializer"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    full_path = serializers.SerializerMethodField()
    descendant_count = serializers.SerializerMethodField()
    traveller_count = serializers.SerializerMethodField()
    budget_count = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationalNode
        fields = [
            'id', 'organization', 'parent', 'parent_name',
            'code', 'name', 'node_type', 'description',
            'is_active', 'full_path', 'descendant_count',
            'traveller_count', 'budget_count',
            'created_at', 'updated_at',
            # MPTT fields
            'lft', 'rght', 'tree_id', 'level'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'lft', 'rght', 'tree_id', 'level']

    def get_full_path(self, obj):
        """Get hierarchical path"""
        return obj.get_full_path()

    def get_descendant_count(self, obj):
        """Get count of all descendants"""
        return obj.get_descendant_count()

    def get_traveller_count(self, obj):
        """Get count of travellers assigned to this node"""
        return obj.travellers.filter(is_active=True).count()

    def get_budget_count(self, obj):
        """Get count of budgets assigned to this node"""
        return obj.budgets.filter(is_active=True).count()


class OrganizationalNodeTreeSerializer(serializers.ModelSerializer):
    """
    Tree serializer with recursive children.
    Use for rendering full organizational hierarchy.
    """
    children = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    traveller_count = serializers.SerializerMethodField()
    budget_count = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationalNode
        fields = [
            'id', 'organization', 'parent', 'parent_name',
            'code', 'name', 'node_type', 'description',
            'is_active', 'level', 'children',
            'traveller_count', 'budget_count'
        ]

    def get_children(self, obj):
        """Recursively serialize children"""
        children = obj.get_children().filter(is_active=True)
        return OrganizationalNodeTreeSerializer(children, many=True, context=self.context).data

    def get_traveller_count(self, obj):
        """Get count of travellers assigned to this node"""
        return obj.travellers.filter(is_active=True).count()

    def get_budget_count(self, obj):
        """Get count of budgets assigned to this node"""
        return obj.budgets.filter(is_active=True).count()


class OrganizationalNodeMoveSerializer(serializers.Serializer):
    """Serializer for moving nodes in the tree"""
    target_id = serializers.UUIDField(required=True)
    position = serializers.ChoiceField(
        choices=['first-child', 'last-child', 'left', 'right'],
        default='last-child'
    )

    def validate_target_id(self, value):
        """Validate that target node exists"""
        try:
            OrganizationalNode.objects.get(id=value)
        except OrganizationalNode.DoesNotExist:
            raise serializers.ValidationError("Target node does not exist")
        return value


class OrganizationalNodeMergeSerializer(serializers.Serializer):
    """Serializer for merging nodes"""
    target_id = serializers.UUIDField(required=True)

    def validate_target_id(self, value):
        """Validate that target node exists"""
        try:
            OrganizationalNode.objects.get(id=value)
        except OrganizationalNode.DoesNotExist:
            raise serializers.ValidationError("Target node does not exist")
        return value


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
    origin_city = serializers.SerializerMethodField()
    origin_country = serializers.SerializerMethodField()
    destination_city = serializers.SerializerMethodField()
    destination_country = serializers.SerializerMethodField()
    fare_class_display = serializers.SerializerMethodField()

    class Meta:
        model = AirSegment
        fields = [
            'id', 'segment_number', 'airline_iata_code', 'airline_name',
            'flight_number', 'origin_airport_iata_code', 'destination_airport_iata_code',
            'origin_city', 'origin_country', 'destination_city', 'destination_country',
            'departure_date', 'departure_time', 'arrival_date', 'arrival_time',
            'booking_class', 'fare_basis', 'distance_km',
            'carbon_emissions_kg', 'fare_class_display'
        ]

    def get_origin_city(self, obj):
        """Get origin airport city"""
        from apps.reference_data.models import Airport
        try:
            airport = Airport.objects.get(iata_code=obj.origin_airport_iata_code)
            return airport.city
        except Airport.DoesNotExist:
            return None

    def get_origin_country(self, obj):
        """Get origin airport country"""
        from apps.reference_data.models import Airport
        try:
            airport = Airport.objects.get(iata_code=obj.origin_airport_iata_code)
            return airport.country
        except Airport.DoesNotExist:
            return None

    def get_destination_city(self, obj):
        """Get destination airport city"""
        from apps.reference_data.models import Airport
        try:
            airport = Airport.objects.get(iata_code=obj.destination_airport_iata_code)
            return airport.city
        except Airport.DoesNotExist:
            return None

    def get_destination_country(self, obj):
        """Get destination airport country"""
        from apps.reference_data.models import Airport
        try:
            airport = Airport.objects.get(iata_code=obj.destination_airport_iata_code)
            return airport.country
        except Airport.DoesNotExist:
            return None

    def get_fare_class_display(self, obj):
        """
        Get fare class display name from FareClassMapping for this segment.
        Returns fare_type if available, otherwise returns the travel_class display name.
        """
        from apps.reference_data.models import FareClassMapping

        if not obj.booking_class:
            return None

        # Get booking date from parent air booking
        booking_date = obj.air_booking.booking.booking_date

        # Try to get fare type from mapping
        fare_type = FareClassMapping.get_fare_type(
            airline_code=obj.airline_iata_code,
            fare_code=obj.booking_class,
            booking_date=booking_date
        )

        if fare_type:
            return fare_type

        # Fall back to travel class from parent air booking
        return obj.air_booking.get_travel_class_display()


class AirBookingSerializer(serializers.ModelSerializer):
    segments = AirSegmentSerializer(many=True, read_only=True)
    total_carbon_kg = serializers.SerializerMethodField()
    origin_city = serializers.SerializerMethodField()
    origin_country = serializers.SerializerMethodField()
    destination_city = serializers.SerializerMethodField()
    destination_country = serializers.SerializerMethodField()
    fare_class_display = serializers.SerializerMethodField()
    total_with_transactions = serializers.SerializerMethodField()

    class Meta:
        model = AirBooking
        fields = [
            'id', 'trip_type', 'travel_class', 'fare_class_display', 'ticket_number',
            'primary_airline_iata_code', 'primary_airline_name',
            'origin_airport_iata_code', 'destination_airport_iata_code',
            'origin_city', 'origin_country', 'destination_city', 'destination_country',
            'lowest_fare_available', 'lowest_fare_currency', 'potential_savings',
            'segments', 'total_carbon_kg', 'base_fare', 'taxes', 'fees', 'gst_amount',
            'total_fare', 'total_with_transactions', 'currency'
        ]

    def get_total_carbon_kg(self, obj):
        """Sum carbon emissions across all segments"""
        total = sum(
            segment.carbon_emissions_kg or 0
            for segment in obj.segments.all()
        )
        return round(total, 2)

    def get_origin_city(self, obj):
        """Get origin airport city"""
        from apps.reference_data.models import Airport
        try:
            airport = Airport.objects.get(iata_code=obj.origin_airport_iata_code)
            return airport.city
        except Airport.DoesNotExist:
            return None

    def get_origin_country(self, obj):
        """Get origin airport country"""
        from apps.reference_data.models import Airport
        try:
            airport = Airport.objects.get(iata_code=obj.origin_airport_iata_code)
            return airport.country
        except Airport.DoesNotExist:
            return None

    def get_destination_city(self, obj):
        """Get destination airport city"""
        from apps.reference_data.models import Airport
        try:
            airport = Airport.objects.get(iata_code=obj.destination_airport_iata_code)
            return airport.city
        except Airport.DoesNotExist:
            return None

    def get_destination_country(self, obj):
        """Get destination airport country"""
        from apps.reference_data.models import Airport
        try:
            airport = Airport.objects.get(iata_code=obj.destination_airport_iata_code)
            return airport.country
        except Airport.DoesNotExist:
            return None

    def get_fare_class_display(self, obj):
        """
        Get fare class display name from FareClassMapping.
        Returns fare_type if available, otherwise returns the travel_class display name.
        """
        from apps.reference_data.models import FareClassMapping

        # Get the first segment's booking class (fare code)
        first_segment = obj.segments.first()
        if not first_segment or not first_segment.booking_class:
            # Fall back to travel_class display
            return obj.get_travel_class_display()

        # Get booking date from parent booking
        booking_date = obj.booking.booking_date

        # Look up fare type from mapping
        fare_type = FareClassMapping.get_fare_type(
            airline_code=obj.primary_airline_iata_code or first_segment.airline_iata_code,
            fare_code=first_segment.booking_class,
            booking_date=booking_date
        )

        # If fare_type is found and not empty, use it
        if fare_type:
            return fare_type

        # Fall back to travel_class display
        return obj.get_travel_class_display()

    def get_total_with_transactions(self, obj):
        """
        Calculate total fare including all transactions (exchanges, refunds, voids, etc.)
        Returns total_fare + sum of all related transaction amounts
        """
        from django.contrib.contenttypes.models import ContentType
        from apps.bookings.models import BookingTransaction
        from decimal import Decimal

        # Start with base total_fare
        total = Decimal(str(obj.total_fare or 0))

        # Add transactions for this air booking
        air_content_type = ContentType.objects.get_for_model(obj.__class__)
        transactions = BookingTransaction.objects.filter(
            content_type=air_content_type,
            object_id=obj.id,
            status__in=['CONFIRMED', 'PENDING']
        )

        transaction_total = sum(
            Decimal(str(t.total_amount_base or t.total_amount or 0))
            for t in transactions
        )

        total += transaction_total
        return float(total)


class AccommodationBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationBooking
        fields = [
            'id', 'hotel_name', 'hotel_chain', 'city', 'country',
            'address', 'check_in_date', 'check_out_date',
            'number_of_nights', 'room_type', 'nightly_rate',
            'currency', 'nightly_rate_base', 'gst_amount', 'total_amount_base'
        ]


class CarHireBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarHireBooking
        fields = [
            'id', 'rental_company', 'vehicle_type', 'vehicle_category', 'vehicle_make_model',  # ✅ Fixed
            'pickup_location', 'pickup_city', 'pickup_date', 'pickup_time',
            'dropoff_location', 'dropoff_city', 'dropoff_date', 'dropoff_time',
            'country', 'number_of_days', 'daily_rate', 'currency',
            'daily_rate_base', 'gst_amount', 'total_amount_base'
        ]


class ServiceFeeSerializer(serializers.ModelSerializer):
    """Service fees charged on bookings"""
    class Meta:
        model = ServiceFee
        fields = [
            'id', 'fee_type', 'fee_date', 'invoice_number',
            'fee_amount', 'gst_amount', 'currency', 'booking_channel',
            'description'
        ]


class BookingTransactionSerializer(serializers.ModelSerializer):
    """Booking transactions (exchanges, refunds, modifications, etc.)"""
    created_by_name = serializers.CharField(source='created_by.__str__', read_only=True)

    class Meta:
        model = BookingTransaction
        fields = [
            'id', 'transaction_type', 'transaction_date', 'transaction_reference',
            'status', 'currency', 'base_amount', 'taxes', 'fees', 'total_amount',
            'reason', 'notes', 'created_by_name'
        ]


class BookingListSerializer(serializers.ModelSerializer):
    """For list views - now includes nested details for charts"""
    traveller_name = serializers.CharField(source='traveller.__str__', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    # Add nested details for frontend charts
    air_bookings = AirBookingSerializer(many=True, read_only=True)
    accommodation_bookings = AccommodationBookingSerializer(many=True, read_only=True)
    car_hire_bookings = CarHireBookingSerializer(many=True, read_only=True)
    service_fees = ServiceFeeSerializer(many=True, read_only=True)

    # Computed field for primary booking type
    primary_booking_type = serializers.SerializerMethodField()

    # Computed field for total amount including transactions
    total_amount_with_transactions = serializers.SerializerMethodField()

    # Computed field for trip type (DOMESTIC or INTERNATIONAL)
    trip_type = serializers.SerializerMethodField()

    # Get all transactions related to this booking's components
    transactions = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'agent_booking_reference', 'supplier_reference',
            'booking_date', 'travel_date', 'return_date',
            'status', 'traveller_name', 'organization_name',
            'currency', 'total_amount', 'total_amount_with_transactions',
            'policy_compliant', 'air_bookings', 'accommodation_bookings',
            'car_hire_bookings', 'service_fees', 'transactions',
            'primary_booking_type', 'trip_type'
        ]

    def get_primary_booking_type(self, obj):
        """Determine primary booking type based on which bookings exist"""
        # Check what type of bookings are present (priority: AIR > ACCOMMODATION > CAR)
        if obj.air_bookings.exists():
            return 'AIR'
        elif obj.accommodation_bookings.exists():
            return 'ACCOMMODATION'
        elif obj.car_hire_bookings.exists():
            return 'CAR'
        else:
            return 'OTHER'

    def get_trip_type(self, obj):
        """
        Determine if booking is DOMESTIC or INTERNATIONAL based on organization's home country.
        Priority: AIR > ACCOMMODATION > CAR
        """
        from apps.reference_data.models import Country, Airport

        # Get home country from request context
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.organization:
            home_country = 'AUS'  # Default
        else:
            home_country = request.user.organization.home_country or 'AUS'

        # Check air bookings first
        if obj.air_bookings.exists():
            for air in obj.air_bookings.all():
                if air.segments.exists():
                    all_domestic = True
                    for segment in air.segments.all():
                        # Get country codes from airports
                        try:
                            origin_airport = Airport.objects.get(iata_code=segment.origin_airport_iata_code)
                            dest_airport = Airport.objects.get(iata_code=segment.destination_airport_iata_code)

                            origin_country = Country.objects.get(name=origin_airport.country)
                            dest_country = Country.objects.get(name=dest_airport.country)

                            if origin_country.alpha_3 != home_country or dest_country.alpha_3 != home_country:
                                all_domestic = False
                                break
                        except (Airport.DoesNotExist, Country.DoesNotExist):
                            # If we can't determine, assume international to be safe
                            all_domestic = False
                            break

                    return 'DOMESTIC' if all_domestic else 'INTERNATIONAL'

        # Check accommodation bookings
        elif obj.accommodation_bookings.exists():
            for accom in obj.accommodation_bookings.all():
                if accom.country:
                    try:
                        country = Country.objects.get(name__iexact=accom.country)
                        if country.alpha_3 == home_country:
                            return 'DOMESTIC'
                        else:
                            return 'INTERNATIONAL'
                    except Country.DoesNotExist:
                        # Check fallback for Australia
                        if accom.country.upper() in ['AUSTRALIA', 'AUS'] and home_country == 'AUS':
                            return 'DOMESTIC'
                        return 'INTERNATIONAL'

        # Check car hire bookings
        elif obj.car_hire_bookings.exists():
            for car in obj.car_hire_bookings.all():
                if car.country:
                    try:
                        country = Country.objects.get(name__iexact=car.country)
                        if country.alpha_3 == home_country:
                            return 'DOMESTIC'
                        else:
                            return 'INTERNATIONAL'
                    except Country.DoesNotExist:
                        # Check fallback for Australia
                        if car.country.upper() in ['AUSTRALIA', 'AUS'] and home_country == 'AUS':
                            return 'DOMESTIC'
                        return 'INTERNATIONAL'

        # Default to DOMESTIC if we can't determine
        return 'DOMESTIC'

    def get_total_amount_with_transactions(self, obj):
        """
        Calculate total amount including all BookingTransaction records.
        This includes air, accommodation, car hire, service fees, and all transactions
        (exchanges, refunds, credits, modifications, etc.)
        """
        from django.contrib.contenttypes.models import ContentType
        from apps.bookings.models import BookingTransaction, AirBooking, AccommodationBooking, CarHireBooking, ServiceFee

        total = 0

        # Add air bookings with transactions
        for air in obj.air_bookings.all():
            air_amount = float(air.total_fare or 0)

            # Add transactions for this air booking
            air_content_type = ContentType.objects.get_for_model(AirBooking)
            air_transactions = BookingTransaction.objects.filter(
                content_type=air_content_type,
                object_id=air.id,
                status__in=['CONFIRMED', 'PENDING']
            )
            transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in air_transactions)
            air_amount += transaction_total

            total += air_amount

        # Add accommodation bookings with transactions
        for accom in obj.accommodation_bookings.all():
            accom_amount = float(accom.total_amount_base or 0)
            if accom_amount == 0 and accom.nightly_rate:
                accom_amount = float(accom.nightly_rate) * accom.number_of_nights

            # Add transactions for this accommodation
            accom_content_type = ContentType.objects.get_for_model(AccommodationBooking)
            accom_transactions = BookingTransaction.objects.filter(
                content_type=accom_content_type,
                object_id=accom.id,
                status__in=['CONFIRMED', 'PENDING']
            )
            transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in accom_transactions)
            accom_amount += transaction_total

            total += accom_amount

        # Add car hire bookings with transactions
        for car in obj.car_hire_bookings.all():
            car_amount = float(car.total_amount_base or car.total_cost or 0)

            # Add transactions for this car hire
            car_content_type = ContentType.objects.get_for_model(CarHireBooking)
            car_transactions = BookingTransaction.objects.filter(
                content_type=car_content_type,
                object_id=car.id,
                status__in=['CONFIRMED', 'PENDING']
            )
            transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in car_transactions)
            car_amount += transaction_total

            total += car_amount

        # Add service fees with transactions
        for fee in obj.service_fees.all():
            fee_amount = float(fee.fee_amount or 0)

            # Add transactions for this service fee
            fee_content_type = ContentType.objects.get_for_model(ServiceFee)
            fee_transactions = BookingTransaction.objects.filter(
                content_type=fee_content_type,
                object_id=fee.id,
                status__in=['CONFIRMED', 'PENDING']
            )
            transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in fee_transactions)
            fee_amount += transaction_total

            total += fee_amount

        return round(total, 2)

    def get_transactions(self, obj):
        """
        Get all transactions related to this booking's components.
        Collects transactions from air_bookings, accommodation_bookings, car_hire_bookings, and service_fees.
        """
        from django.contrib.contenttypes.models import ContentType
        from apps.bookings.models import BookingTransaction, AirBooking, AccommodationBooking, CarHireBooking, ServiceFee

        all_transactions = []

        # Get transactions for air bookings
        air_content_type = ContentType.objects.get_for_model(AirBooking)
        for air in obj.air_bookings.all():
            air_transactions = BookingTransaction.objects.filter(
                content_type=air_content_type,
                object_id=air.id
            )
            all_transactions.extend(air_transactions)

        # Get transactions for accommodation bookings
        accom_content_type = ContentType.objects.get_for_model(AccommodationBooking)
        for accom in obj.accommodation_bookings.all():
            accom_transactions = BookingTransaction.objects.filter(
                content_type=accom_content_type,
                object_id=accom.id
            )
            all_transactions.extend(accom_transactions)

        # Get transactions for car hire bookings
        car_content_type = ContentType.objects.get_for_model(CarHireBooking)
        for car in obj.car_hire_bookings.all():
            car_transactions = BookingTransaction.objects.filter(
                content_type=car_content_type,
                object_id=car.id
            )
            all_transactions.extend(car_transactions)

        # Get transactions for service fees
        service_fee_content_type = ContentType.objects.get_for_model(ServiceFee)
        for fee in obj.service_fees.all():
            fee_transactions = BookingTransaction.objects.filter(
                content_type=service_fee_content_type,
                object_id=fee.id
            )
            all_transactions.extend(fee_transactions)

        # Serialize the transactions
        return BookingTransactionSerializer(all_transactions, many=True).data


class BookingDetailSerializer(serializers.ModelSerializer):
    """For detail views - full data"""
    traveller = TravellerListSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    air_bookings = AirBookingSerializer(many=True, read_only=True)
    accommodation_bookings = AccommodationBookingSerializer(many=True, read_only=True)
    car_hire_bookings = CarHireBookingSerializer(many=True, read_only=True)
    travel_arranger_name = serializers.CharField(source='travel_arranger.__str__', read_only=True)
    travel_consultant_name = serializers.CharField(source='travel_consultant.__str__', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'organization', 'traveller', 'agent_booking_reference',
            'supplier_reference', 'booking_date',
            'travel_date', 'return_date', 'status', 'currency',
            'total_amount', 'base_fare', 'taxes', 'fees',
            'total_amount_base', 'base_fare_base', 'taxes_base', 'fees_base',
            'exchange_rate', 'exchange_rate_date', 
            'policy_compliant', 'advance_booking_days',
            'travel_arranger', 'travel_arranger_name', 'travel_arranger_text',
            'travel_consultant', 'travel_consultant_name', 'travel_consultant_text',
            'air_bookings', 'accommodation_bookings', 'car_hire_bookings',
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
            'total_budget', 'currency',
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
    organization_name = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceViolation
        fields = [
            'id', 'booking', 'booking_reference', 'traveller', 'traveller_name',
            'organization', 'organization_name', 'violation_type', 'violation_description', 'severity',
            'expected_amount', 'actual_amount', 'variance_amount', 'currency',
            'is_waived', 'waived_by', 'waiver_reason', 'detected_at'
        ]

    def get_organization_name(self, obj):
        if obj.organization:
            return obj.organization.name
        return None


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


class HotelSerializer(serializers.ModelSerializer):
    """Serializer for Hotel master data"""
    aliases = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Hotel
        fields = [
            'id', 'canonical_name', 'hotel_chain', 'city', 'country',
            'is_active', 'aliases', 'created_at', 'updated_at'
        ]


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
            'product_type', 'booking_date', 'supplier_name',
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

class ServiceFeeSerializer(serializers.ModelSerializer):
    """Serializer for service fees"""
    traveller_name = serializers.SerializerMethodField()
    booking_reference = serializers.SerializerMethodField()
    organization_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceFee
        fields = [
            'id', 'booking', 'booking_reference', 'traveller', 'traveller_name',
            'organization', 'organization_name', 'fee_type', 'fee_date', 'invoice_number',
            'currency', 'fee_amount', 'gst_amount', 'booking_channel', 'description', 'created_at',
        ]

    def get_traveller_name(self, obj):
        if obj.traveller:
            return f"{obj.traveller.first_name} {obj.traveller.last_name}"
        return None

    def get_booking_reference(self, obj):
        if obj.booking:
            return obj.booking.agent_booking_reference
        return None

    def get_organization_name(self, obj):
        if obj.organization:
            return obj.organization.name
        return None

# ============================================================================
# COUNTRY SERIALIZERS
# ============================================================================

class CountrySerializer(serializers.ModelSerializer):
    """
    Serializer for Country reference data.
    Returns is_domestic dynamically based on requesting user's organization.
    """
    is_domestic = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Country
        fields = [
            'alpha_3', 'alpha_2', 'numeric_code',
            'name', 'common_name', 'display_name',
            'region', 'subregion',
            'currency_code', 'phone_prefix',
            'is_active', 'is_domestic'
        ]
    
    def get_is_domestic(self, obj):
        """
        Dynamically determine if country is domestic based on request user's organization.
        Returns None if user or organization context is not available.
        """
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return None
        
        user = request.user
        if not hasattr(user, 'organization') or not user.organization:
            return None
        
        return obj.is_domestic_for_organization(user.organization)
    
    def get_display_name(self, obj):
        """Return common_name with alpha_3 code for UI display"""
        return f"{obj.common_name} ({obj.alpha_3})"


# ============================================================================
# ORGANIZATIONAL NODE SERIALIZERS (Hierarchy Structure)
# ============================================================================

class OrganizationalNodeSerializer(serializers.ModelSerializer):
    """Serializer for organizational hierarchy nodes"""
    full_path = serializers.SerializerMethodField()
    traveller_count = serializers.SerializerMethodField()
    budget_count = serializers.SerializerMethodField()
    descendant_count = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationalNode
        fields = [
            'id', 'organization', 'name', 'code', 'node_type',
            'parent', 'full_path', 'level', 'description', 'is_active',
            'traveller_count', 'budget_count', 'descendant_count',
            'children', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'level', 'created_at', 'updated_at']

    def get_full_path(self, obj):
        """Get the full hierarchical path"""
        return obj.get_full_path()

    def get_traveller_count(self, obj):
        """Get count of travellers associated with this node"""
        return obj.get_traveller_count()

    def get_budget_count(self, obj):
        """Get count of budgets associated with this node"""
        return obj.get_budget_count()

    def get_descendant_count(self, obj):
        """Get count of all descendants"""
        return obj.get_descendants().count()

    def get_children(self, obj):
        """Get immediate children (only when building tree)"""
        # Only include children if we're building a tree structure
        # This prevents infinite recursion
        if self.context.get('include_children', False):
            children = obj.children.filter(is_active=True)
            return OrganizationalNodeSerializer(
                children, many=True,
                context={**self.context, 'include_children': True}
            ).data
        return []


class OrganizationalNodeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    full_path = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = OrganizationalNode
        fields = [
            'id', 'organization', 'organization_name', 'name', 'code',
            'node_type', 'parent', 'parent_name', 'full_path', 'level',
            'is_active'
        ]

    def get_full_path(self, obj):
        """Get the full hierarchical path"""
        return obj.get_full_path()


class OrganizationalNodeTreeSerializer(serializers.ModelSerializer):
    """Serializer specifically for tree view with recursive children"""
    children = serializers.SerializerMethodField()
    traveller_count = serializers.SerializerMethodField()
    budget_count = serializers.SerializerMethodField()
    descendant_count = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationalNode
        fields = [
            'id', 'name', 'code', 'node_type', 'parent', 'level',
            'full_path', 'is_active',
            'traveller_count', 'budget_count', 'descendant_count',
            'children'
        ]

    def get_full_path(self, obj):
        """Get the full hierarchical path"""
        return obj.get_full_path()

    def get_children(self, obj):
        """Recursively serialize children"""
        # MPTT already orders children by lft, which respects the tree structure
        children = obj.children.filter(is_active=True)
        return OrganizationalNodeTreeSerializer(children, many=True, context=self.context).data

    def get_traveller_count(self, obj):
        return obj.get_traveller_count()

    def get_budget_count(self, obj):
        return obj.get_budget_count()

    def get_descendant_count(self, obj):
        return obj.children.count()


# ============================================================================
# PREFERRED AIRLINE SERIALIZERS
# ============================================================================

class PreferredAirlineSerializer(serializers.ModelSerializer):
    """
    Serializer for PreferredAirline model.
    Used for airline deals analysis and market share tracking.
    """
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.__str__', read_only=True)
    market_type_display = serializers.CharField(source='get_market_type_display', read_only=True)

    # Computed field for contract status (Active, Expired, Future)
    contract_status = serializers.SerializerMethodField()

    # Days until contract end
    days_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = PreferredAirline
        fields = [
            'id', 'organization', 'organization_name',
            'airline_iata_code', 'airline_name',
            'market_type', 'market_type_display',
            'markets_served', 'routes_covered',
            'target_market_share', 'target_revenue',
            'contract_start_date', 'contract_end_date',
            'contract_status', 'days_until_expiry',
            'is_active', 'notes',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_contract_status(self, obj):
        """
        Determine contract status based on dates and is_active flag.
        Returns: ACTIVE, EXPIRED, FUTURE, or INACTIVE
        """
        from django.utils import timezone
        today = timezone.now().date()

        if not obj.is_active:
            return 'INACTIVE'
        elif obj.contract_end_date < today:
            return 'EXPIRED'
        elif obj.contract_start_date > today:
            return 'FUTURE'
        else:
            return 'ACTIVE'

    def get_days_until_expiry(self, obj):
        """
        Calculate days until contract expires.
        Returns None if contract already expired or is inactive.
        """
        from django.utils import timezone
        today = timezone.now().date()

        if not obj.is_active or obj.contract_end_date < today:
            return None

        delta = obj.contract_end_date - today
        return delta.days
