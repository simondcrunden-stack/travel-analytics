from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Avg, Q
from datetime import datetime, timedelta

from apps.organizations.models import Organization
from apps.users.models import User
from apps.bookings.models import (
    Traveller, Booking, AirBooking, AirSegment,
    AccommodationBooking, CarHireBooking, Invoice, ServiceFee
)
from apps.budgets.models import FiscalYear, Budget, BudgetAlert
from apps.compliance.models import ComplianceViolation, TravelRiskAlert
from apps.reference_data.models import Airport, Airline, CurrencyExchangeRate, Country
from apps.commissions.models import Commission

from .serializers import (
    OrganizationSerializer, UserSerializer,
    TravellerListSerializer, TravellerDetailSerializer,
    BookingListSerializer, BookingDetailSerializer,
    AirBookingSerializer, AccommodationBookingSerializer, CarHireBookingSerializer,
    FiscalYearSerializer, BudgetSerializer, BudgetAlertSerializer,
    ComplianceViolationSerializer, TravelRiskAlertSerializer,
    AirportSerializer, AirlineSerializer, CurrencyExchangeRateSerializer,
    CommissionSerializer, ServiceFeeSerializer, CountrySerializer
)


# ============================================================================
# ORGANIZATION & USER VIEWSETS
# ============================================================================

class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for organizations.
    
    list: Get all organizations (filtered by user access)
    retrieve: Get specific organization details
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'ADMIN':
            return Organization.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            # Return agent's org + their customer orgs
            if user.organization:
                return Organization.objects.filter(
                    Q(id=user.organization.id) | Q(travel_agent=user.organization)
                )
            return Organization.objects.all()  # Fallback for users without org
        else:
            # Customer users - only their org
            if user.organization:
                return Organization.objects.filter(id=user.organization.id)
            return Organization.objects.none()  # Return empty if no org


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for users.
    
    me: Get current user profile
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'ADMIN':
            return User.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            # Travel agents see users in their org and customer orgs
            return User.objects.filter(
                Q(organization=user.organization) | 
                Q(organization__travel_agent=user.organization)
            )
        else:
            # Customer users see only their organization
            return User.objects.filter(organization=user.organization)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get', 'put'])
    def filter_preferences(self, request):
        """
        Get or update user's default filter preferences.
        GET /api/v1/users/filter_preferences/
        PUT /api/v1/users/filter_preferences/
        """
        profile = request.user.profile
        
        if request.method == 'GET':
            return Response({
                'default_filters': profile.default_filters,
                'home_country': profile.home_country
            })
        
        elif request.method == 'PUT':
            # Update preferences
            if 'default_filters' in request.data:
                profile.default_filters = request.data['default_filters']
            if 'home_country' in request.data:
                profile.home_country = request.data['home_country']
            profile.save()
            
            return Response({
                'default_filters': profile.default_filters,
                'home_country': profile.home_country
            })


# ============================================================================
# TRAVELLER VIEWSETS
# ============================================================================

class TravellerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for travellers.
    
    list: Get all travellers (filtered by organization access)
    retrieve: Get specific traveller details
    create: Create new traveller
    update: Update traveller
    partial_update: Partially update traveller
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'cost_center', 'department', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'ADMIN':
            return Traveller.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            # Travel agents see travellers from their customers
            return Traveller.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            # Customer users see only their organization
            return Traveller.objects.filter(organization=user.organization)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TravellerDetailSerializer
        return TravellerListSerializer
    
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        """Get all bookings for a specific traveller"""
        traveller = self.get_object()
        bookings = Booking.objects.filter(traveller=traveller).order_by('-travel_date')
        serializer = BookingListSerializer(bookings, many=True)
        return Response(serializer.data)


# ============================================================================
# BOOKING VIEWSETS
# ============================================================================

class BookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for bookings with comprehensive filtering.
    
    Supports filtering by:
    - organization, traveller, status
    - Date ranges (booking_date, travel_date)
    - Search by reference numbers
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact'],
        'organization': ['exact'],
        'traveller': ['exact'],
        'booking_date': ['gte', 'lte', 'exact'],
        'travel_date': ['gte', 'lte', 'exact'],
    }
    search_fields = ['agent_booking_reference', 'supplier_reference', 
                    'traveller__first_name', 'traveller__last_name']
    ordering_fields = ['booking_date', 'travel_date', 'total_amount', 'created_at']
    ordering = ['-travel_date']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'ADMIN':
            queryset = Booking.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            # Travel agents see bookings from their customers
            queryset = Booking.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            # Customer users see only their organization
            queryset = Booking.objects.filter(organization=user.organization)
        
        # Optimize queries with select_related
        return queryset.select_related(
            'organization', 'traveller', 'travel_arranger', 'travel_consultant'
        )
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookingDetailSerializer
        return BookingListSerializer
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get booking summary statistics.
        
        Query params:
        - start_date: Filter from date (YYYY-MM-DD)
        - end_date: Filter to date (YYYY-MM-DD)
        - organization: Filter by organization ID
        """
        queryset = self.get_queryset()
        
        # Apply date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        organization = request.query_params.get('organization')
        
        if start_date:
            queryset = queryset.filter(travel_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(travel_date__lte=end_date)
        if organization:
            queryset = queryset.filter(organization_id=organization)
        
        # Calculate statistics
        summary = {
            'total_bookings': queryset.count(),
            'total_spend': queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'by_status': list(queryset.values('status').annotate(
                count=Count('id'),
                total=Sum('total_amount')
            )),
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def carbon_report(self, request):
        """
        Get carbon emissions report for air bookings.
        """
        queryset = self.get_queryset()
        
        # Apply date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(travel_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(travel_date__lte=end_date)
        
        # Get air bookings with segments - only bookings that have air components
        air_bookings = AirBooking.objects.filter(
            booking__in=queryset
        ).prefetch_related('segments')
        
        total_carbon = 0
        total_distance = 0
        segment_count = 0
        
        for air_booking in air_bookings:
            for segment in air_booking.segments.all():
                if segment.carbon_emissions_kg:
                    total_carbon += float(segment.carbon_emissions_kg)
                if segment.distance_km:
                    total_distance += segment.distance_km
                segment_count += 1
        
        report = {
            'total_flights': air_bookings.count(),
            'total_segments': segment_count,
            'total_carbon_kg': round(total_carbon, 2),
            'total_carbon_tonnes': round(total_carbon / 1000, 2),
            'total_distance_km': total_distance,
            'average_carbon_per_flight': round(total_carbon / air_bookings.count(), 2) if air_bookings.count() > 0 else 0,
        }
        
        return Response(report)

    @action(detail=False, methods=['get'])
    @action(detail=False, methods=['get'])
    def available_countries(self, request):
        """
        Get list of countries where the organization has bookings.
        Used to populate country filter dropdowns.
        
        Returns countries that appear in:
        - Air segments (via airport lookups)
        - Accommodation bookings
        - Car hire bookings
        
        GET /api/v1/bookings/available_countries/
        """
        from apps.bookings.models import AirSegment, AccommodationBooking, CarHireBooking
        from apps.reference_data.models import Country, Airport
        from django.db.models import Q
        
        # Get user's organization
        user_org = request.user.organization
        if not user_org:
            return Response([])
        
        # Collect all country codes from bookings
        country_codes = set()
        
        # ========================================================================
        # From air segments - get airport codes, then look up countries
        # ========================================================================
        air_segments = AirSegment.objects.filter(
            air_booking__booking__organization=user_org
        ).values_list('origin_airport_iata_code', 'destination_airport_iata_code')
        
        # Collect all airport codes
        airport_codes = set()
        for origin_code, dest_code in air_segments:
            if origin_code:
                airport_codes.add(origin_code)
            if dest_code:
                airport_codes.add(dest_code)
        
        # Look up countries from airports
        # Note: Airport.country is a CharField (country name), not FK to Country
        # We'll need to map country names to country codes
        if airport_codes:
            airports = Airport.objects.filter(iata_code__in=airport_codes)
            country_names = set(a.country for a in airports if a.country)
            
            # Try to match country names to Country records
            # This is a best-effort match since Airport.country is just a string
            for country_name in country_names:
                # Try exact match on name or common_name
                try:
                    country = Country.objects.filter(
                        Q(name__iexact=country_name) | Q(common_name__iexact=country_name),
                        is_active=True
                    ).first()
                    if country:
                        country_codes.add(country.alpha_3)
                except:
                    pass
        
        # ========================================================================
        # From accommodation bookings
        # ========================================================================
        # AccommodationBooking.country should be alpha_3 code
        hotel_countries = AccommodationBooking.objects.filter(
            booking__organization=user_org
        ).values_list('country', flat=True)
        country_codes.update(filter(None, hotel_countries))
        
        # ========================================================================
        # From car hire bookings
        # ========================================================================
        # From car hire bookings
        # ========================================================================
        # CarHireBooking only has 'country' field (not pickup_country/dropoff_country)
        car_countries = CarHireBooking.objects.filter(
            booking__organization=user_org
        ).values_list('country', flat=True)
        country_codes.update(filter(None, car_countries))
        
        # ========================================================================
        # Get country details from reference data
        # ========================================================================
        if not country_codes:
            # No bookings yet, return all active countries as fallback
            countries = Country.objects.filter(
                is_active=True
            ).values('alpha_3', 'common_name', 'name').order_by('common_name')
        else:
            # Return only countries that have bookings
            countries = Country.objects.filter(
                alpha_3__in=country_codes,
                is_active=True
            ).values('alpha_3', 'common_name', 'name').order_by('common_name')
        
        # Format response
        result = [
            {
                'code': c['alpha_3'],
                'name': c['common_name'] or c['name']
            }
            for c in countries
        ]
        
        return Response(result)


# ============================================================================
# BUDGET VIEWSETS
# ============================================================================

class BudgetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for budgets with spend tracking.
    """
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['organization', 'fiscal_year', 'cost_center', 'is_active']
    search_fields = ['cost_center', 'cost_center_name']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'ADMIN':
            return Budget.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            return Budget.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            return Budget.objects.filter(organization=user.organization)


# ============================================================================
# REFERENCE DATA VIEWSETS
# ============================================================================

class AirportViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for airports - read-only"""
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['iata_code', 'name', 'city', 'country']
    lookup_field = 'iata_code'


class AirlineViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for airlines - read-only"""
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['iata_code', 'name', 'country']
    lookup_field = 'iata_code'


# ============================================================================
# COMMISSION VIEWSET
# ============================================================================

class CommissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for commissions - read-only.
    Only accessible by travel agents.
    """
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'product_type', 'supplier_name', 'earned_date']
    search_fields = ['booking__agent_booking_reference', 'booking__supplier_reference']
    ordering_fields = ['created_at', 'commission_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # Only travel agents can see commissions
        if user.user_type in ['ADMIN', 'AGENT_ADMIN', 'AGENT_USER']:
            return Commission.objects.filter(
                organization=user.organization
            ).select_related('booking', 'organization', 'traveller')
        
        return Commission.objects.none()

# ============================================================================
# SERVICE FEE VIEWSET
# ============================================================================

class ServiceFeeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for service fees"""
    serializer_class = ServiceFeeSerializer
    filterset_fields = ['organization', 'fee_type', 'traveller']
    search_fields = ['description']
    ordering_fields = ['fee_date', 'amount']
    ordering = ['-fee_date']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'ADMIN':
            return ServiceFee.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            if user.organization:
                return ServiceFee.objects.filter(
                    Q(organization=user.organization) |
                    Q(organization__travel_agent=user.organization)
                )
        elif user.user_type in ['CUSTOMER_ADMIN', 'CUSTOMER_RISK', 'CUSTOMER']:
            if user.organization:
                return ServiceFee.objects.filter(organization=user.organization)
        
        return ServiceFee.objects.none()

# ============================================================================
# COUNTRY VIEWSET
# ============================================================================

class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for countries - read-only.
    
    Endpoints:
    - GET /api/v1/countries/ - List all active countries
    - GET /api/v1/countries/{alpha_3}/ - Get specific country
    - GET /api/v1/countries/available/ - Countries available for selection
    - GET /api/v1/countries/domestic/ - Get user's domestic country
    - GET /api/v1/countries/regions/ - List regions with counts
    """
    queryset = Country.objects.filter(is_active=True)
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'alpha_3'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['alpha_3', 'alpha_2', 'name', 'common_name']
    ordering_fields = ['alpha_3', 'common_name', 'region']
    ordering = ['common_name']
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Get list of countries available for selection.
        Returns active countries with domestic flag based on user's organization.
        
        Query params:
        - region: Filter by region (e.g., ?region=Oceania)
        - subregion: Filter by subregion (e.g., ?subregion=Australia and New Zealand)
        - search: Search in name or code
        """
        queryset = self.get_queryset()
        
        # Apply filters
        region = request.query_params.get('region')
        if region:
            queryset = queryset.filter(region__iexact=region)
        
        subregion = request.query_params.get('subregion')
        if subregion:
            queryset = queryset.filter(subregion__iexact=subregion)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def domestic(self, request):
        """
        Get the domestic country for the current user's organization.
        
        Returns:
            Country details with is_domestic=True
        """
        if not hasattr(request.user, 'organization') or not request.user.organization:
            return Response(
                {'error': 'User organization not found'},
                status=400
            )
        
        try:
            country = Country.objects.get(
                alpha_3=request.user.organization.home_country,
                is_active=True
            )
            serializer = self.get_serializer(country)
            return Response(serializer.data)
        except Country.DoesNotExist:
            return Response(
                {'error': 'Domestic country not found'},
                status=404
            )
    
    @action(detail=False, methods=['get'])
    def regions(self, request):
        """
        Get list of unique regions with country counts.
        
        Returns:
            [
                {"region": "Oceania", "count": 3},
                {"region": "Asia", "count": 10},
                ...
            ]
        """
        regions = (
            Country.objects
            .filter(is_active=True)
            .values('region')
            .annotate(count=Count('alpha_3'))
            .order_by('region')
        )
        return Response(regions)