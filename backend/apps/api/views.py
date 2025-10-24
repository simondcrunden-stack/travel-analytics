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
from apps.reference_data.models import Airport, Airline, CurrencyExchangeRate
from apps.commissions.models import Commission

from .serializers import (
    OrganizationSerializer, UserSerializer,
    TravellerListSerializer, TravellerDetailSerializer,
    BookingListSerializer, BookingDetailSerializer,
    AirBookingSerializer, AccommodationBookingSerializer, CarHireBookingSerializer,
    FiscalYearSerializer, BudgetSerializer, BudgetAlertSerializer,
    ComplianceViolationSerializer, TravelRiskAlertSerializer,
    AirportSerializer, AirlineSerializer, CurrencyExchangeRateSerializer,
    CommissionSerializer, ServiceFeeSerializer
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
    - organization, traveller, booking_type, status
    - Date ranges (booking_date, travel_date)
    - Search by reference numbers
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'booking_type': ['exact'],
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
            'by_type': list(queryset.values('booking_type').annotate(
                count=Count('id'),
                total=Sum('total_amount')
            )),
            'by_status': list(queryset.values('status').annotate(
                count=Count('id')
            )),
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def carbon_report(self, request):
        """
        Get carbon emissions report for air bookings.
        """
        queryset = self.get_queryset().filter(booking_type='AIR')
        
        # Apply date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(travel_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(travel_date__lte=end_date)
        
        # Get air bookings with segments
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