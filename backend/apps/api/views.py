from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Avg, Q
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, timedelta

from apps.organizations.models import Organization, OrganizationalNode
from apps.users.models import User
from apps.bookings.models import (
    Traveller, Booking, AirBooking, AirSegment,
    AccommodationBooking, CarHireBooking, Invoice, ServiceFee, BookingTransaction,
    PreferredAirline, PreferredHotel, PreferredCarHire, OtherProduct
)
from apps.budgets.models import FiscalYear, Budget, BudgetAlert
from apps.compliance.models import ComplianceViolation, TravelRiskAlert
from apps.reference_data.models import Airport, Airline, CurrencyExchangeRate, Country
from apps.commissions.models import Commission

from .serializers import (
    OrganizationSerializer, UserSerializer,
    OrganizationalNodeSerializer, OrganizationalNodeTreeSerializer,
    OrganizationalNodeMoveSerializer, OrganizationalNodeMergeSerializer,
    TravellerListSerializer, TravellerDetailSerializer,
    BookingListSerializer, BookingDetailSerializer,
    AirBookingSerializer, AccommodationBookingSerializer, CarHireBookingSerializer,
    FiscalYearSerializer, BudgetSerializer, BudgetAlertSerializer,
    ComplianceViolationSerializer, TravelRiskAlertSerializer,
    AirportSerializer, AirlineSerializer, CurrencyExchangeRateSerializer,
    CommissionSerializer, ServiceFeeSerializer, CountrySerializer,
    OrganizationalNodeSerializer, OrganizationalNodeListSerializer, OrganizationalNodeTreeSerializer,
    PreferredAirlineSerializer, PreferredHotelSerializer, PreferredCarHireSerializer
)


# ============================================================================
# ORGANIZATION & USER VIEWSETS
# ============================================================================

class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for organizations.

    list: Get all organizations (filtered by user access)
    retrieve: Get specific organization details

    Query parameters:
    - org_type: Filter by organization type (AGENT, CUSTOMER)
    - travel_agent: Filter by travel agent ID (for customer orgs)
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Base queryset based on user type
        if user.user_type == 'ADMIN':
            queryset = Organization.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            # Return agent's org + their customer orgs
            if user.organization:
                queryset = Organization.objects.filter(
                    Q(id=user.organization.id) | Q(travel_agent=user.organization)
                )
            else:
                queryset = Organization.objects.all()  # Fallback for users without org
        else:
            # Customer users - only their org
            if user.organization:
                queryset = Organization.objects.filter(id=user.organization.id)
            else:
                queryset = Organization.objects.none()  # Return empty if no org

        # Apply additional filters from query parameters
        org_type = self.request.query_params.get('org_type', None)
        if org_type:
            queryset = queryset.filter(org_type=org_type)

        travel_agent_id = self.request.query_params.get('travel_agent', None)
        if travel_agent_id:
            queryset = queryset.filter(travel_agent_id=travel_agent_id)

        return queryset


class OrganizationalNodeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for organizational hierarchy management.

    Supports full CRUD operations plus tree-specific actions:
    - tree: Get full organizational tree
    - roots: Get root nodes only
    - children: Get children of a specific node
    - ancestors: Get ancestors of a specific node
    - descendants: Get descendants of a specific node
    - move: Move a node to a new position in the tree
    - merge: Merge a node into another node
    """
    serializer_class = OrganizationalNodeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'node_type', 'is_active', 'parent']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'created_at']
    ordering = ['lft']  # MPTT left value for tree order

    def get_queryset(self):
        """Filter by user's organization access"""
        user = self.request.user

        if user.user_type == 'ADMIN':
            return OrganizationalNode.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            # Return nodes for agent's org + their customer orgs
            if user.organization:
                return OrganizationalNode.objects.filter(
                    Q(organization=user.organization) |
                    Q(organization__travel_agent=user.organization)
                )
            return OrganizationalNode.objects.all()
        else:
            # Customer users - only their org
            if user.organization:
                return OrganizationalNode.objects.filter(organization=user.organization)
            return OrganizationalNode.objects.none()

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Get full organizational tree for the user's organization.

        Returns complete hierarchy with nested children.
        Query params:
        - organization_id: Filter by specific organization (optional)
        """
        organization_id = request.query_params.get('organization_id')

        queryset = self.get_queryset()
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        # Get root nodes (no parent) and build tree from there
        root_nodes = queryset.filter(parent__isnull=True, is_active=True)
        serializer = OrganizationalNodeTreeSerializer(
            root_nodes,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def roots(self, request):
        """Get all root nodes (nodes without parents)"""
        queryset = self.get_queryset().filter(parent__isnull=True, is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get direct children of a node"""
        node = self.get_object()
        children = node.get_children().filter(is_active=True)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        """Get all ancestors of a node (path to root)"""
        node = self.get_object()
        ancestors = node.get_ancestors()
        serializer = self.get_serializer(ancestors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        """Get all descendants of a node (entire subtree)"""
        node = self.get_object()
        descendants = node.get_descendants().filter(is_active=True)
        serializer = self.get_serializer(descendants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """
        Move a node to a new position in the tree.

        Body:
        {
            "target_id": "uuid-of-target-node",
            "position": "first-child" | "last-child" | "left" | "right"
        }
        """
        node = self.get_object()
        serializer = OrganizationalNodeMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_id = serializer.validated_data['target_id']
        position = serializer.validated_data['position']

        try:
            target = OrganizationalNode.objects.get(id=target_id)

            # Validate move is within same organization
            if node.organization_id != target.organization_id:
                return Response(
                    {"error": "Cannot move node to different organization"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Perform move using MPTT
            node.move_to(target, position)
            node.save()

            serializer = self.get_serializer(node)
            return Response(serializer.data)

        except OrganizationalNode.DoesNotExist:
            return Response(
                {"error": "Target node not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def merge(self, request, pk=None):
        """
        Merge this node into another node.

        Body:
        {
            "target_id": "uuid-of-target-node"
        }

        This will:
        1. Move all children to target node
        2. Update all travellers to target node
        3. Update all budgets to target node
        4. Mark this node as inactive
        """
        node = self.get_object()
        serializer = OrganizationalNodeMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_id = serializer.validated_data['target_id']

        try:
            target = OrganizationalNode.objects.get(id=target_id)

            # Validate merge
            if not node.can_be_merged_with(target):
                return Response(
                    {"error": "Cannot merge these nodes. Check organization, node type, and hierarchy."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Perform merge
            node.merge_into(target)

            return Response({
                "message": f"Successfully merged {node.name} into {target.name}",
                "target": self.get_serializer(target).data
            })

        except OrganizationalNode.DoesNotExist:
            return Response(
                {"error": "Target node not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


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
    - organization, traveller (single or multiple), status
    - Date ranges (booking_date, travel_date)
    - Search by reference numbers
    - Destination filters (domestic/international/regions)
    - Country filters (single or multiple)
    - City/location search
    - Travel consultant (single or multiple)
    - Supplier filter

    Response includes summary statistics:
    - total_spend: Sum of all booking amounts
    - total_emissions: Sum of carbon emissions (kg CO2)
    - compliance_rate: Percentage of compliant bookings
    - booking_count: Total number of bookings
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

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookingDetailSerializer
        return BookingListSerializer
    
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
        
        # Apply advanced filters
        queryset = self._apply_advanced_filters(queryset, user)
        
        # Optimize queries with select_related and prefetch_related
        return queryset.select_related(
            'organization', 'traveller', 'travel_arranger', 'travel_consultant'
        ).prefetch_related(
            'air_bookings__segments',
            'accommodation_bookings',
            'car_hire_bookings'
        )
    
    def _apply_advanced_filters(self, queryset, user):
        
        from apps.reference_data.models import Airport, Country
        from apps.bookings.models import AirSegment, AccommodationBooking, CarHireBooking
        from django.db.models import Q, Exists, OuterRef
        
        # Get filter parameters
        travellers = self.request.query_params.get('travellers', '')
        countries = self.request.query_params.get('countries', '')
        destination_preset = self.request.query_params.get('destination_preset', '')
        city = self.request.query_params.get('city', '')
        travel_consultant = self.request.query_params.get('travel_consultant', '')
        travel_consultants = self.request.query_params.get('travel_consultants', '')
        supplier = self.request.query_params.get('supplier', '')
        booking_type = self.request.query_params.get('booking_type', '')
        
        # ========================================================================
        # TRAVELLERS FILTER (Multi-select)
        # ========================================================================
        if travellers:
            traveller_ids = [t.strip() for t in travellers.split(',') if t.strip()]
            if traveller_ids:
                queryset = queryset.filter(traveller_id__in=traveller_ids)

        # ========================================================================
        # BOOKING TYPE FILTER
        # ========================================================================
        if booking_type:
            if booking_type == 'AIR':
                queryset = queryset.filter(air_bookings__isnull=False).distinct()
            elif booking_type == 'HOTEL':
                queryset = queryset.filter(accommodation_bookings__isnull=False).distinct()
            elif booking_type == 'CAR':
                queryset = queryset.filter(car_hire_bookings__isnull=False).distinct()

        # ========================================================================
        # COUNTRIES FILTER (Multi-select) - SMART LOGIC
        # ========================================================================
        if countries:
            country_codes = [c.strip() for c in countries.split(',') if c.strip()]
            if country_codes:
                # Get user's home country
                user_home_country_code = 'AUS'  # Default
                if hasattr(user, 'organization') and user.organization:
                    user_home_country_code = user.organization.home_country or 'AUS'
                
                # Convert country codes to country names
                country_names = []
                for code in country_codes:
                    try:
                        country = Country.objects.get(alpha_3=code)
                        country_names.append(country.name)
                    except Country.DoesNotExist:
                        try:
                            country = Country.objects.get(alpha_2=code)
                            country_names.append(country.name)
                        except Country.DoesNotExist:
                            country_names.append(code)
                
                # Get all airports in the selected countries
                country_airports = list(Airport.objects.filter(
                    country__in=country_names
                ).values_list('iata_code', flat=True))
                
                # SMART LOGIC: Determine filter type based on selection
                # If filtering by ONLY home country → STRICT (all segments within)
                # Otherwise → TOUCHES (any segment touches selected countries)
                
                filtering_home_country_only = (
                    len(country_codes) == 1 and 
                    country_codes[0] == user_home_country_code
                )
                
                booking_ids_matching = []
                
                for booking in queryset.prefetch_related('air_bookings__segments'):
                    has_air_bookings = booking.air_bookings.exists()
                    
                    if has_air_bookings:
                        if filtering_home_country_only:
                            # STRICT: ALL segments must be within home country
                            all_segments_within = True
                            
                            for air_booking in booking.air_bookings.all():
                                for segment in air_booking.segments.all():
                                    origin_in = segment.origin_airport_iata_code in country_airports
                                    dest_in = segment.destination_airport_iata_code in country_airports
                                    
                                    if not (origin_in and dest_in):
                                        all_segments_within = False
                                        break
                                
                                if not all_segments_within:
                                    break
                            
                            if all_segments_within:
                                booking_ids_matching.append(booking.id)
                        else:
                            # TOUCHES: ANY segment touches selected countries
                            touches_countries = False
                            
                            for air_booking in booking.air_bookings.all():
                                for segment in air_booking.segments.all():
                                    origin_in = segment.origin_airport_iata_code in country_airports
                                    dest_in = segment.destination_airport_iata_code in country_airports
                                    
                                    if origin_in or dest_in:
                                        touches_countries = True
                                        break
                                
                                if touches_countries:
                                    break
                            
                            if touches_countries:
                                booking_ids_matching.append(booking.id)
                    else:
                        # For non-air bookings, check accommodation/car hire
                        has_matching_accom = booking.accommodation_bookings.filter(
                            country__in=country_names
                        ).exists()
                        
                        has_matching_car = booking.car_hire_bookings.filter(
                            country__in=country_names
                        ).exists()
                        
                        if has_matching_accom or has_matching_car:
                            booking_ids_matching.append(booking.id)
                
                queryset = queryset.filter(id__in=booking_ids_matching)
        
        # ========================================================================
        # DESTINATION PRESET FILTERS - FIXED SESSION 49
        # ========================================================================
        if destination_preset:
            # Get user's home country
            user_country_code = 'AUS'  # Default
            if hasattr(user, 'organization') and user.organization:
                user_country_code = user.organization.home_country or 'AUS'
            
            # Convert to country name
            try:
                user_country_obj = Country.objects.get(alpha_3=user_country_code)
                user_country_name = user_country_obj.name
            except Country.DoesNotExist:
                user_country_name = 'Australia'
            
            if destination_preset == 'within_user_country':
                # DOMESTIC: ALL segments must be within user's country (STRICT)
                domestic_airports = list(Airport.objects.filter(
                    country=user_country_name
                ).values_list('iata_code', flat=True))
                
                booking_ids_domestic = []
                
                for booking in queryset.prefetch_related('air_bookings__segments'):
                    if booking.air_bookings.exists():
                        all_domestic = True
                        
                        for air_booking in booking.air_bookings.all():
                            for segment in air_booking.segments.all():
                                origin_domestic = segment.origin_airport_iata_code in domestic_airports
                                dest_domestic = segment.destination_airport_iata_code in domestic_airports
                                
                                if not (origin_domestic and dest_domestic):
                                    all_domestic = False
                                    break
                            
                            if not all_domestic:
                                break
                        
                        if all_domestic:
                            booking_ids_domestic.append(booking.id)
                
                queryset = queryset.filter(id__in=booking_ids_domestic)
            
            elif destination_preset == 'outside_user_country':
                # INTERNATIONAL: At least ONE segment outside user's country
                domestic_airports = list(Airport.objects.filter(
                    country=user_country_name
                ).values_list('iata_code', flat=True))
                
                booking_ids_international = []
                
                for booking in queryset.prefetch_related('air_bookings__segments'):
                    if booking.air_bookings.exists():
                        has_international = False
                        
                        for air_booking in booking.air_bookings.all():
                            for segment in air_booking.segments.all():
                                origin_domestic = segment.origin_airport_iata_code in domestic_airports
                                dest_domestic = segment.destination_airport_iata_code in domestic_airports
                                
                                if not origin_domestic or not dest_domestic:
                                    has_international = True
                                    break
                            
                            if has_international:
                                break
                        
                        if has_international:
                            booking_ids_international.append(booking.id)
                
                queryset = queryset.filter(id__in=booking_ids_international)
            
            elif destination_preset in ['asia', 'europe', 'oceania', 'americas', 'africa', 'middle_east', 
                                        'north_america', 'south_america']:
                # REGIONAL FILTERS: Destination touches selected region
                region_map = {
                    'asia': 'Asia',
                    'europe': 'Europe',
                    'oceania': 'Oceania',
                    'americas': 'Americas',
                    'africa': 'Africa',
                    'middle_east': 'Middle East',
                    'north_america': 'Americas',
                    'south_america': 'Americas',
                }
                
                region_name = region_map.get(destination_preset)
                
                if region_name:
                    region_countries = Country.objects.filter(
                        region=region_name
                    ).values_list('name', flat=True)
                    
                    region_airports = list(Airport.objects.filter(
                        country__in=region_countries
                    ).values_list('iata_code', flat=True))
                    
                    booking_ids_regional = []
                    
                    for booking in queryset.prefetch_related('air_bookings__segments'):
                        if booking.air_bookings.exists():
                            has_regional_dest = False
                            
                            for air_booking in booking.air_bookings.all():
                                for segment in air_booking.segments.all():
                                    if segment.destination_airport_iata_code in region_airports:
                                        has_regional_dest = True
                                        break
                                
                                if has_regional_dest:
                                    break
                            
                            if has_regional_dest:
                                booking_ids_regional.append(booking.id)
                    
                    queryset = queryset.filter(id__in=booking_ids_regional)
        
        # ========================================================================
        # CITY/LOCATION SEARCH - NEW SESSION 49
        # ========================================================================
        if city:
            city_search = city.strip().lower()
            city_q = Q()
            
            # Air bookings: Search in airport cities
            air_booking_airports = Airport.objects.filter(
                Q(city__icontains=city_search) | Q(name__icontains=city_search)
            ).values_list('iata_code', flat=True)
            
            city_q |= Q(
                air_bookings__segments__origin_airport_iata_code__in=air_booking_airports
            ) | Q(
                air_bookings__segments__destination_airport_iata_code__in=air_booking_airports
            )
            
            # Accommodation bookings
            city_q |= Q(accommodation_bookings__city__icontains=city_search)
            
            # Car hire bookings
            city_q |= Q(
                Q(car_hire_bookings__pickup_city__icontains=city_search) |
                Q(car_hire_bookings__dropoff_city__icontains=city_search)
            )
            
            queryset = queryset.filter(city_q).distinct()
        
        # ========================================================================
        # TRAVEL CONSULTANT FILTER (Multi-select)
        # ========================================================================
        if travel_consultants:
            consultant_ids = [c.strip() for c in travel_consultants.split(',') if c.strip()]
            if consultant_ids:
                queryset = queryset.filter(travel_consultant_id__in=consultant_ids)
        elif travel_consultant:
            queryset = queryset.filter(travel_consultant_id=travel_consultant)
        
        # ========================================================================
        # SUPPLIER FILTER
        # ========================================================================
        if supplier:
            supplier_search = supplier.strip()
            supplier_q = Q()

            supplier_q |= Q(air_bookings__primary_airline_name__icontains=supplier_search)
            supplier_q |= Q(accommodation_bookings__hotel_name__icontains=supplier_search)
            supplier_q |= Q(car_hire_bookings__rental_company__icontains=supplier_search)

            queryset = queryset.filter(supplier_q).distinct()
        
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Override list to include summary statistics with the response.

        Returns:
        {
            "count": 150,
            "next": null,
            "previous": null,
            "results": [...],
            "summary": {
                "total_spend": 125000.50,
                "total_emissions": 45000,
                "compliance_rate": 85,
                "booking_count": 150
            }
        }
        """
        # Get the filtered queryset
        queryset = self.filter_queryset(self.get_queryset())

        # Calculate summary statistics on the filtered queryset
        from decimal import Decimal
        from django.contrib.contenttypes.models import ContentType

        # Get booking_type to determine which amounts to sum
        booking_type = self.request.query_params.get('booking_type', '')
        booking_ids = list(queryset.values_list('id', flat=True))

        # Calculate base amounts based on booking_type
        total_spend = Decimal('0')

        if booking_type == 'AIR':
            # Sum total air fares (including taxes and GST) for summary cards
            total_spend = AirBooking.objects.filter(
                booking_id__in=booking_ids
            ).aggregate(total=Sum('total_fare'))['total'] or Decimal('0')
        elif booking_type == 'HOTEL':
            # Sum only accommodation amounts
            total_spend = AccommodationBooking.objects.filter(
                booking_id__in=booking_ids
            ).aggregate(total=Sum('total_amount_base'))['total'] or Decimal('0')
        elif booking_type == 'CAR':
            # Sum only car hire amounts
            total_spend = CarHireBooking.objects.filter(
                booking_id__in=booking_ids
            ).aggregate(total=Sum('total_amount_base'))['total'] or Decimal('0')
        else:
            # No filter - sum all booking amounts
            total_spend = queryset.aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0')

        # Add transaction amounts (exchanges, refunds, voids, reissues)
        # Filter transactions based on booking_type
        if booking_ids:
            # Get content types for booking-related models
            booking_ct = ContentType.objects.get_for_model(Booking)
            air_booking_ct = ContentType.objects.get_for_model(AirBooking)
            accommodation_ct = ContentType.objects.get_for_model(AccommodationBooking)
            car_hire_ct = ContentType.objects.get_for_model(CarHireBooking)

            if booking_type == 'AIR':
                # Only include air-related transactions
                air_booking_ids = AirBooking.objects.filter(
                    booking_id__in=booking_ids
                ).values_list('id', flat=True)

                air_transactions = BookingTransaction.objects.filter(
                    content_type=air_booking_ct,
                    object_id__in=air_booking_ids,
                    status__in=['CONFIRMED', 'PENDING']
                ).aggregate(total=Sum('total_amount_base'))['total'] or Decimal('0')

                total_spend += air_transactions

            elif booking_type == 'HOTEL':
                # Only include accommodation-related transactions
                accommodation_ids = AccommodationBooking.objects.filter(
                    booking_id__in=booking_ids
                ).values_list('id', flat=True)

                accommodation_transactions = BookingTransaction.objects.filter(
                    content_type=accommodation_ct,
                    object_id__in=accommodation_ids,
                    status__in=['CONFIRMED', 'PENDING']
                ).aggregate(total=Sum('total_amount_base'))['total'] or Decimal('0')

                total_spend += accommodation_transactions

            elif booking_type == 'CAR':
                # Only include car hire-related transactions
                car_hire_ids = CarHireBooking.objects.filter(
                    booking_id__in=booking_ids
                ).values_list('id', flat=True)

                car_hire_transactions = BookingTransaction.objects.filter(
                    content_type=car_hire_ct,
                    object_id__in=car_hire_ids,
                    status__in=['CONFIRMED', 'PENDING']
                ).aggregate(total=Sum('total_amount_base'))['total'] or Decimal('0')

                total_spend += car_hire_transactions

            else:
                # No filter - include all transaction types
                booking_transactions = BookingTransaction.objects.filter(
                    content_type=booking_ct,
                    object_id__in=booking_ids,
                    status__in=['CONFIRMED', 'PENDING']
                ).aggregate(total=Sum('total_amount_base'))['total'] or Decimal('0')

                # Get sub-booking transactions
                air_booking_ids = AirBooking.objects.filter(
                    booking_id__in=booking_ids
                ).values_list('id', flat=True)

                air_transactions = BookingTransaction.objects.filter(
                    content_type=air_booking_ct,
                    object_id__in=air_booking_ids,
                    status__in=['CONFIRMED', 'PENDING']
                ).aggregate(total=Sum('total_amount_base'))['total'] or Decimal('0')

                accommodation_ids = AccommodationBooking.objects.filter(
                    booking_id__in=booking_ids
                ).values_list('id', flat=True)

                accommodation_transactions = BookingTransaction.objects.filter(
                    content_type=accommodation_ct,
                    object_id__in=accommodation_ids,
                    status__in=['CONFIRMED', 'PENDING']
                ).aggregate(total=Sum('total_amount_base'))['total'] or Decimal('0')

                car_hire_ids = CarHireBooking.objects.filter(
                    booking_id__in=booking_ids
                ).values_list('id', flat=True)

                car_hire_transactions = BookingTransaction.objects.filter(
                    content_type=car_hire_ct,
                    object_id__in=car_hire_ids,
                    status__in=['CONFIRMED', 'PENDING']
                ).aggregate(total=Sum('total_amount_base'))['total'] or Decimal('0')

                # Add all transactions to total spend
                total_spend += booking_transactions + air_transactions + accommodation_transactions + car_hire_transactions

        # Add service fees and other products (when no specific booking_type filter)
        # This ensures summary includes ALL product types
        if not booking_type and booking_ids:
            service_fee_ct = ContentType.objects.get_for_model(ServiceFee)
            other_product_ct = ContentType.objects.get_for_model(OtherProduct)

            # Get service fee IDs for these bookings
            service_fee_ids = ServiceFee.objects.filter(
                booking_id__in=booking_ids
            ).values_list('id', flat=True)

            # Sum service fees
            service_fees_total = ServiceFee.objects.filter(
                booking_id__in=booking_ids
            ).aggregate(total=Sum('fee_amount'))['total'] or Decimal('0')

            # Add service fee transactions
            service_fee_transactions = BookingTransaction.objects.filter(
                content_type=service_fee_ct,
                object_id__in=service_fee_ids,
                status__in=['CONFIRMED', 'PENDING']
            ).aggregate(total=Sum('total_amount_base'))['total'] or Decimal('0')

            # Get other product IDs for these bookings
            other_product_ids = OtherProduct.objects.filter(
                booking_id__in=booking_ids
            ).values_list('id', flat=True)

            # Sum other products (insurance, cruise, etc.)
            other_products_total = OtherProduct.objects.filter(
                booking_id__in=booking_ids
            ).aggregate(total=Sum('amount_base'))['total'] or Decimal('0')

            # Add other product transactions
            other_product_transactions = BookingTransaction.objects.filter(
                content_type=other_product_ct,
                object_id__in=other_product_ids,
                status__in=['CONFIRMED', 'PENDING']
            ).aggregate(total=Sum('total_amount_base'))['total'] or Decimal('0')

            # Add to total spend
            total_spend += service_fees_total + service_fee_transactions + other_products_total + other_product_transactions

        # Calculate total emissions from air bookings
        # NOTE: We calculate from segments (same logic as serializer) because
        # the air_booking.total_carbon_kg field may not be populated
        total_emissions = 0
        for booking in queryset.prefetch_related('air_bookings__segments'):
            for air_booking in booking.air_bookings.all():
                # Sum carbon from all segments in this air booking
                for segment in air_booking.segments.all():
                    if segment.carbon_emissions_kg:
                        total_emissions += float(segment.carbon_emissions_kg)

        # Calculate compliance rate
        booking_count = queryset.count()
        if booking_count > 0:
            compliant_count = queryset.filter(policy_compliant=True).count()
            compliance_rate = round((compliant_count / booking_count) * 100)
        else:
            compliance_rate = 0

        # Build summary object
        summary = {
            'total_spend': float(total_spend),
            'total_emissions': round(total_emissions),
            'compliance_rate': compliance_rate,
            'booking_count': booking_count
        }

        # Get paginated response
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            # Add summary to response data
            response.data['summary'] = summary
            return response

        # Non-paginated response
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'count': booking_count,
            'summary': summary
        })

    @action(detail=False, methods=['get'])
    def available_countries(self, request):
        """
        Get list of countries that appear in the user's accessible bookings.
        Uses the same queryset logic as get_queryset() for consistency.
        Supports filtering by organization via query params.
        """
        user = request.user

        # Build base queryset using same logic as get_queryset()
        if user.user_type == 'ADMIN':
            base_queryset = Booking.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            # Travel agents see bookings from their customers
            base_queryset = Booking.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            # Customer users see only their organization
            base_queryset = Booking.objects.filter(organization=user.organization)

        # Apply organization filter if provided in query params
        organization_id = request.query_params.get('organization')
        if organization_id:
            base_queryset = base_queryset.filter(organization_id=organization_id)
        
        # Collect unique country names
        countries_set = set()
        
        # Get countries from air segments
        air_segments = AirSegment.objects.filter(
            air_booking__booking__in=base_queryset
        ).values_list('origin_airport_iata_code', 'destination_airport_iata_code')
        
        # Build list of unique IATA codes
        iata_codes = set()
        for origin_code, dest_code in air_segments:
            if origin_code:
                iata_codes.add(origin_code)
            if dest_code:
                iata_codes.add(dest_code)
        
        # Get countries from airports
        if iata_codes:
            airports = Airport.objects.filter(iata_code__in=iata_codes).values_list('country', flat=True)
            countries_set.update(airports)
        
        # Get countries from accommodation bookings
        accommodation_countries = AccommodationBooking.objects.filter(
            booking__in=base_queryset,
            country__isnull=False
        ).values_list('country', flat=True).distinct()
        countries_set.update(accommodation_countries)
        
        # Get countries from car hire bookings
        car_hire_countries = CarHireBooking.objects.filter(
            booking__in=base_queryset,
            country__isnull=False
        ).values_list('country', flat=True).distinct()
        countries_set.update(car_hire_countries)
        
        # Convert country names to Country objects with codes
        from apps.reference_data.models import Country
        country_data = []
        
        for country_name in countries_set:
            try:
                country = Country.objects.get(name=country_name)
                country_data.append({
                    'code': country.alpha_3,
                    'name': country.name
                })
            except Country.DoesNotExist:
                # If country not in reference data, still include it
                country_data.append({
                    'code': country_name[:3].upper(),
                    'name': country_name
                })
        
        # Sort by name
        country_data.sort(key=lambda x: x['name'])

        return Response(country_data)

    @action(detail=False, methods=['get'])
    def trip_map_data(self, request):
        """
        Get aggregated trip data for map visualization.

        Returns destinations with:
        - Coordinates (latitude/longitude)
        - Number of trips
        - Number of unique travellers
        - Total spend
        - Average spend per trip

        Includes both air travel destinations AND accommodation-only destinations.
        Uses the same queryset logic as get_queryset() for security.
        """
        from collections import defaultdict
        from django.db.models import Count, Sum, Avg

        user = request.user

        # Build base queryset using same logic as get_queryset()
        if user.user_type == 'ADMIN':
            base_queryset = Booking.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            base_queryset = Booking.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            base_queryset = Booking.objects.filter(organization=user.organization)

        # Apply advanced filters from request
        base_queryset = self._apply_advanced_filters(base_queryset, user)

        # Aggregate by destination - supports both air and accommodation destinations
        destination_data = defaultdict(lambda: {
            'destination_type': None,  # 'airport' or 'city'
            'trips': 0,
            'travellers': set(),
            'total_spend': 0,
            'bookings': set()  # Track unique bookings per destination
        })

        # Process AIR bookings - use destination airport code
        air_bookings = AirBooking.objects.filter(
            booking__in=base_queryset
        ).select_related('booking', 'booking__traveller')

        for ab in air_bookings:
            dest = ab.destination_airport_iata_code
            if dest:
                destination_data[dest]['destination_type'] = 'airport'
                destination_data[dest]['trips'] += 1
                destination_data[dest]['travellers'].add(ab.booking.traveller.id if ab.booking.traveller else None)
                destination_data[dest]['bookings'].add(ab.booking.id)

        # Process ACCOMMODATION bookings - use city name (for bookings without air travel)
        accommodation_bookings = AccommodationBooking.objects.filter(
            booking__in=base_queryset
        ).select_related('booking', 'booking__traveller')

        for accom in accommodation_bookings:
            # Only add accommodation as a destination if the booking doesn't already have air travel
            booking_id = accom.booking.id

            # Check if this booking already has an air destination
            booking_has_air = any(booking_id in data['bookings']
                                 for data in destination_data.values()
                                 if data['destination_type'] == 'airport')

            # If no air travel, use accommodation city as destination
            if not booking_has_air and accom.city:
                city_key = f"CITY_{accom.city.upper()}"  # Prefix to avoid collision with airport codes
                destination_data[city_key]['destination_type'] = 'city'
                destination_data[city_key]['city_name'] = accom.city
                destination_data[city_key]['country_name'] = accom.country or 'Unknown'
                destination_data[city_key]['trips'] += 1
                destination_data[city_key]['travellers'].add(accom.booking.traveller.id if accom.booking.traveller else None)
                destination_data[city_key]['bookings'].add(booking_id)

        # Calculate complete spend for each booking (including transactions, service fees, other products)
        booking_totals = {}
        all_bookings = set()
        for data in destination_data.values():
            all_bookings.update(data['bookings'])

        for booking_id in all_bookings:
            if booking_id not in booking_totals:
                # Calculate total for this booking
                booking = Booking.objects.prefetch_related(
                    'air_bookings',
                    'accommodation_bookings',
                    'car_hire_bookings',
                    'service_fees',
                    'other_products'
                ).get(id=booking_id)

                total = 0

                # Air bookings with transactions
                for air in booking.air_bookings.all():
                    air_amount = float(air.total_fare or 0)
                    air_content_type = ContentType.objects.get_for_model(AirBooking)
                    air_transactions = BookingTransaction.objects.filter(
                        content_type=air_content_type,
                        object_id=air.id,
                        status__in=['CONFIRMED', 'PENDING']
                    )
                    air_amount += sum(float(t.total_amount_base or t.total_amount or 0) for t in air_transactions)
                    total += air_amount

                # Accommodation bookings with transactions
                for accom in booking.accommodation_bookings.all():
                    accom_amount = float(accom.total_amount_base or 0)
                    accom_content_type = ContentType.objects.get_for_model(AccommodationBooking)
                    accom_transactions = BookingTransaction.objects.filter(
                        content_type=accom_content_type,
                        object_id=accom.id,
                        status__in=['CONFIRMED', 'PENDING']
                    )
                    accom_amount += sum(float(t.total_amount_base or t.total_amount or 0) for t in accom_transactions)
                    total += accom_amount

                # Car hire bookings with transactions
                for car in booking.car_hire_bookings.all():
                    car_amount = float(car.total_amount_base or 0)
                    car_content_type = ContentType.objects.get_for_model(CarHireBooking)
                    car_transactions = BookingTransaction.objects.filter(
                        content_type=car_content_type,
                        object_id=car.id,
                        status__in=['CONFIRMED', 'PENDING']
                    )
                    car_amount += sum(float(t.total_amount_base or t.total_amount or 0) for t in car_transactions)
                    total += car_amount

                # Service fees with transactions
                for fee in booking.service_fees.all():
                    fee_amount = float(fee.fee_amount or 0)
                    fee_content_type = ContentType.objects.get_for_model(ServiceFee)
                    fee_transactions = BookingTransaction.objects.filter(
                        content_type=fee_content_type,
                        object_id=fee.id,
                        status__in=['CONFIRMED', 'PENDING']
                    )
                    fee_amount += sum(float(t.total_amount_base or t.total_amount or 0) for t in fee_transactions)
                    total += fee_amount

                # Other products with transactions
                for other in booking.other_products.all():
                    other_amount = float(other.amount_base or other.amount or 0)
                    other_content_type = ContentType.objects.get_for_model(OtherProduct)
                    other_transactions = BookingTransaction.objects.filter(
                        content_type=other_content_type,
                        object_id=other.id,
                        status__in=['CONFIRMED', 'PENDING']
                    )
                    other_amount += sum(float(t.total_amount_base or t.total_amount or 0) for t in other_transactions)
                    total += other_amount

                booking_totals[booking_id] = total

        # Add booking totals to destination data
        for dest_key, data in destination_data.items():
            for booking_id in data['bookings']:
                data['total_spend'] += booking_totals.get(booking_id, 0)

        # Get coordinates and build result
        result = []

        for dest_key, data in destination_data.items():
            try:
                if data['destination_type'] == 'airport':
                    # Use airport coordinates
                    airport = Airport.objects.get(iata_code=dest_key)
                    if airport.latitude and airport.longitude:
                        result.append({
                            'code': dest_key,
                            'name': airport.name,
                            'city': airport.city,
                            'country': airport.country or 'Unknown',
                            'latitude': float(airport.latitude),
                            'longitude': float(airport.longitude),
                            'trips': data['trips'],
                            'travellers': len(data['travellers']),
                            'total_spend': round(data['total_spend'], 2),
                            'avg_spend': round(data['total_spend'] / data['trips'], 2) if data['trips'] > 0 else 0,
                            'destination_type': 'airport'
                        })

                elif data['destination_type'] == 'city':
                    # Try to find an airport in this city to get coordinates
                    city_name = data.get('city_name', '')
                    country_name = data.get('country_name', '')

                    # Look for airport in this city
                    city_airport = Airport.objects.filter(
                        city__iexact=city_name
                    ).first()

                    if city_airport and city_airport.latitude and city_airport.longitude:
                        result.append({
                            'code': dest_key,
                            'name': f"{city_name} (Accommodation)",
                            'city': city_name,
                            'country': country_name,
                            'latitude': float(city_airport.latitude),
                            'longitude': float(city_airport.longitude),
                            'trips': data['trips'],
                            'travellers': len(data['travellers']),
                            'total_spend': round(data['total_spend'], 2),
                            'avg_spend': round(data['total_spend'] / data['trips'], 2) if data['trips'] > 0 else 0,
                            'destination_type': 'city'
                        })
            except (Airport.DoesNotExist, KeyError):
                # Skip destinations without coordinate data
                continue

        # Sort by number of trips (descending)
        result.sort(key=lambda x: x['trips'], reverse=True)

        return Response(result)

    @action(detail=False, methods=['get'])
    def top_routes_destinations(self, request):
        """
        Get top routes and destinations analysis for dashboard.

        Returns:
        - Top routes (combined round-trips: MEL ⇄ SIN)
        - Top destinations by country (excluding < 24hr transits)
        - Most traveled destinations (actual stops, not transits)
        """
        from collections import defaultdict, Counter
        from datetime import datetime, timedelta

        user = request.user
        limit = int(request.query_params.get('limit', 10))

        # Build base queryset using same logic as get_queryset()
        if user.user_type == 'ADMIN':
            base_queryset = Booking.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            base_queryset = Booking.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            base_queryset = Booking.objects.filter(organization=user.organization)

        # Apply advanced filters from request
        base_queryset = self._apply_advanced_filters(base_queryset, user)

        # Get all air bookings with their segments
        air_bookings = AirBooking.objects.filter(
            booking__in=base_queryset
        ).select_related('booking', 'booking__traveller').prefetch_related('segments')

        # Track route pairs, destinations by country, and actual destination stops
        route_pairs = defaultdict(lambda: {
            'trips': 0,
            'travellers': set(),
            'total_spend': 0
        })

        country_destinations = defaultdict(lambda: {
            'trips': 0,
            'travellers': set(),
            'total_spend': 0,
            'cities': set(),
            'total_duration': timedelta()
        })

        destination_stops = defaultdict(lambda: {
            'trips': 0,
            'travellers': set(),
            'total_spend': 0,
            'total_duration': timedelta()
        })

        # Process each air booking
        for air_booking in air_bookings:
            booking = air_booking.booking
            segments = list(air_booking.segments.all().order_by('segment_number'))

            if not segments:
                continue

            # Identify actual destination stops (not transits) and track duration
            actual_destinations = set()
            destination_durations = {}  # Track duration for each destination in this booking

            # Get the trip origin to exclude it from destinations (don't count returning home)
            first_origin = segments[0].origin_airport_iata_code if segments else None

            for i, segment in enumerate(segments):
                dest_code = segment.destination_airport_iata_code

                # Check if this is a transit or actual stop
                is_transit = False
                stay_duration = None

                if i < len(segments) - 1:  # Not the final destination
                    next_segment = segments[i + 1]
                    # If next segment departs from same airport
                    if next_segment.origin_airport_iata_code == dest_code:
                        # Calculate layover time
                        if (segment.arrival_date and segment.arrival_time and
                            next_segment.departure_date and next_segment.departure_time):
                            arrival_dt = datetime.combine(segment.arrival_date, segment.arrival_time)
                            departure_dt = datetime.combine(next_segment.departure_date, next_segment.departure_time)
                            layover = departure_dt - arrival_dt
                            stay_duration = layover
                            # If layover < 24 hours, it's a transit
                            if layover < timedelta(hours=24):
                                is_transit = True
                else:
                    # Final destination - skip if it's the origin (round trip returning home)
                    if dest_code == first_origin:
                        continue

                # If not a transit and not the origin, it's an actual destination
                if not is_transit and dest_code != first_origin:
                    actual_destinations.add(dest_code)
                    if stay_duration and dest_code:
                        # Track the duration for this destination
                        if dest_code not in destination_durations:
                            destination_durations[dest_code] = timedelta()
                        destination_durations[dest_code] += stay_duration

            # Track route pairs (combine round trips)
            if len(segments) >= 2:
                first_origin = segments[0].origin_airport_iata_code
                last_destination = segments[-1].destination_airport_iata_code

                # For round trips (origin = final destination), create routes to actual destinations
                if first_origin == last_destination:
                    # Create routes from origin to each actual destination visited
                    for dest_code in actual_destinations:
                        if dest_code != first_origin:  # Don't create origin to origin routes
                            route_key = tuple(sorted([first_origin, dest_code]))
                            route_pairs[route_key]['trips'] += 1
                            if booking.traveller:
                                route_pairs[route_key]['travellers'].add(booking.traveller.id)
                            route_pairs[route_key]['total_spend'] += float(booking.total_amount or 0)
                else:
                    # One-way trip: use first origin and last destination
                    if first_origin and last_destination:
                        route_key = tuple(sorted([first_origin, last_destination]))
                        route_pairs[route_key]['trips'] += 1
                        if booking.traveller:
                            route_pairs[route_key]['travellers'].add(booking.traveller.id)
                        route_pairs[route_key]['total_spend'] += float(booking.total_amount or 0)

            # Track actual destination stops
            for dest_code in actual_destinations:
                destination_stops[dest_code]['trips'] += 1
                if booking.traveller:
                    destination_stops[dest_code]['travellers'].add(booking.traveller.id)
                destination_stops[dest_code]['total_spend'] += float(booking.total_amount or 0)
                # Add duration if we tracked it for this destination
                if dest_code in destination_durations:
                    destination_stops[dest_code]['total_duration'] += destination_durations[dest_code]

        # Get airport details for all airports
        from apps.reference_data.models import Airport

        all_airport_codes = set()
        for route_key in route_pairs.keys():
            all_airport_codes.update(route_key)
        all_airport_codes.update(destination_stops.keys())

        airports = {a.iata_code: a for a in Airport.objects.filter(iata_code__in=all_airport_codes)}

        # Aggregate destinations by country
        for dest_code, data in destination_stops.items():
            airport = airports.get(dest_code)
            if airport and airport.country:
                country_destinations[airport.country]['trips'] += data['trips']
                country_destinations[airport.country]['travellers'].update(data['travellers'])
                country_destinations[airport.country]['total_spend'] += data['total_spend']
                country_destinations[airport.country]['total_duration'] += data['total_duration']
                if airport.city:
                    country_destinations[airport.country]['cities'].add(airport.city)

        # Format top routes (round-trip combined)
        top_routes = []
        for route_key, data in sorted(route_pairs.items(), key=lambda x: x[1]['trips'], reverse=True)[:limit]:
            airport1 = airports.get(route_key[0])
            airport2 = airports.get(route_key[1])

            top_routes.append({
                'route': f"{route_key[0]} ⇄ {route_key[1]}",
                'airport1': route_key[0],
                'airport1_city': airport1.city if airport1 else route_key[0],
                'airport2': route_key[1],
                'airport2_city': airport2.city if airport2 else route_key[1],
                'trips': data['trips'],
                'unique_travellers': len(data['travellers']),
                'total_spend': round(data['total_spend'], 2),
                'avg_spend_per_trip': round(data['total_spend'] / data['trips'], 2) if data['trips'] > 0 else 0
            })

        # Helper function to format duration
        def format_duration(td):
            """Format timedelta as days and hours"""
            if not td or td.total_seconds() == 0:
                return "0 hours"
            total_hours = td.total_seconds() / 3600
            days = int(total_hours // 24)
            hours = int(total_hours % 24)
            if days > 0:
                return f"{days}d {hours}h" if hours > 0 else f"{days}d"
            return f"{hours}h"

        # Format top destinations by country
        top_destinations = []
        for country, data in sorted(country_destinations.items(), key=lambda x: x[1]['trips'], reverse=True)[:limit]:
            cities_list = ', '.join(sorted(data['cities'])[:3])
            if len(data['cities']) > 3:
                cities_list += f" +{len(data['cities']) - 3} more"

            top_destinations.append({
                'country': country,
                'cities': cities_list,
                'trips': data['trips'],
                'unique_travellers': len(data['travellers']),
                'total_spend': round(data['total_spend'], 2),
                'avg_spend_per_trip': round(data['total_spend'] / data['trips'], 2) if data['trips'] > 0 else 0,
                'total_duration_seconds': int(data['total_duration'].total_seconds()),
                'total_duration': format_duration(data['total_duration'])
            })

        # Format top destination airports (actual stops, not transits)
        top_destination_airports = []
        for dest_code, data in sorted(destination_stops.items(), key=lambda x: x[1]['trips'], reverse=True)[:limit]:
            airport = airports.get(dest_code)

            top_destination_airports.append({
                'airport': dest_code,
                'city': airport.city if airport else dest_code,
                'country': airport.country if airport else 'Unknown',
                'trips': data['trips'],
                'unique_travellers': len(data['travellers']),
                'total_spend': round(data['total_spend'], 2),
                'avg_spend_per_trip': round(data['total_spend'] / data['trips'], 2) if data['trips'] > 0 else 0,
                'total_duration_seconds': int(data['total_duration'].total_seconds()),
                'total_duration': format_duration(data['total_duration'])
            })

        return Response({
            'top_routes': top_routes,
            'top_destinations': top_destinations,
            'top_destination_airports': top_destination_airports
        })

    @action(detail=False, methods=['get'])
    def sustainability_analytics(self, request):
        """
        Get comprehensive sustainability and carbon emissions analytics.

        Returns:
        - Total emissions breakdown (by trip type, by category)
        - Monthly emissions trend
        - Top carbon emitters (travellers)
        - Carbon efficiency metrics
        - Emissions by route
        """
        from collections import defaultdict
        from datetime import datetime
        from decimal import Decimal

        user = request.user

        # Build base queryset using same logic as get_queryset()
        if user.user_type == 'ADMIN':
            base_queryset = Booking.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            base_queryset = Booking.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            base_queryset = Booking.objects.filter(organization=user.organization)

        # Apply advanced filters from request
        base_queryset = self._apply_advanced_filters(base_queryset, user)

        # Initialize totals
        total_emissions = Decimal('0')
        total_emissions_domestic = Decimal('0')
        total_emissions_international = Decimal('0')
        total_emissions_air = Decimal('0')
        total_spend = Decimal('0')
        monthly_emissions = defaultdict(lambda: {'carbon_kg': 0, 'trips': 0})
        traveller_emissions = defaultdict(lambda: {'carbon_kg': 0, 'trips': 0, 'name': ''})
        route_emissions = defaultdict(lambda: {'carbon_kg': 0, 'trips': 0})

        # Get user's home country for domestic/international classification
        user_country_code = 'AUS'
        if hasattr(user, 'organization') and user.organization:
            user_country_code = user.organization.home_country or 'AUS'

        from apps.reference_data.models import Country, Airport
        try:
            user_country_obj = Country.objects.get(alpha_3=user_country_code)
            user_country_name = user_country_obj.name
        except Country.DoesNotExist:
            user_country_name = 'Australia'

        domestic_airports = list(Airport.objects.filter(
            country=user_country_name
        ).values_list('iata_code', flat=True))

        # Process all bookings with air travel
        air_bookings = AirBooking.objects.filter(
            booking__in=base_queryset
        ).select_related('booking', 'booking__traveller').prefetch_related('segments')

        for air_booking in air_bookings:
            booking = air_booking.booking
            carbon_kg = float(air_booking.total_carbon_kg or 0)

            # Add to total
            total_emissions += Decimal(str(carbon_kg))
            total_emissions_air += Decimal(str(carbon_kg))
            total_spend += booking.total_amount or Decimal('0')

            # Determine if domestic or international
            is_domestic = True
            for segment in air_booking.segments.all():
                origin_domestic = segment.origin_airport_iata_code in domestic_airports
                dest_domestic = segment.destination_airport_iata_code in domestic_airports
                if not (origin_domestic and dest_domestic):
                    is_domestic = False
                    break

            if is_domestic:
                total_emissions_domestic += Decimal(str(carbon_kg))
            else:
                total_emissions_international += Decimal(str(carbon_kg))

            # Monthly trend
            if booking.travel_date:
                month_key = booking.travel_date.strftime('%Y-%m')
                monthly_emissions[month_key]['carbon_kg'] += carbon_kg
                monthly_emissions[month_key]['trips'] += 1

            # Traveller emissions
            if booking.traveller:
                traveller_id = booking.traveller.id
                traveller_emissions[traveller_id]['carbon_kg'] += carbon_kg
                traveller_emissions[traveller_id]['trips'] += 1
                traveller_emissions[traveller_id]['name'] = f"{booking.traveller.first_name} {booking.traveller.last_name}"

            # Route emissions (use first segment for route)
            first_segment = air_booking.segments.first()
            if first_segment:
                route_key = f"{first_segment.origin_airport_iata_code}-{first_segment.destination_airport_iata_code}"
                route_emissions[route_key]['carbon_kg'] += carbon_kg
                route_emissions[route_key]['trips'] += 1
                route_emissions[route_key]['route'] = route_key

        # Format monthly trend (sorted by month)
        monthly_trend = []
        for month_key in sorted(monthly_emissions.keys()):
            data = monthly_emissions[month_key]
            monthly_trend.append({
                'month': month_key,
                'carbon_kg': round(data['carbon_kg'], 2),
                'trips': data['trips']
            })

        # Format top carbon emitters (travellers)
        top_emitters = []
        for traveller_id, data in sorted(traveller_emissions.items(), key=lambda x: x[1]['carbon_kg'], reverse=True)[:10]:
            top_emitters.append({
                'traveller_id': traveller_id,
                'traveller_name': data['name'],
                'carbon_kg': round(data['carbon_kg'], 2),
                'trips': data['trips'],
                'avg_carbon_per_trip': round(data['carbon_kg'] / data['trips'], 2) if data['trips'] > 0 else 0
            })

        # Format top routes by emissions
        top_routes_by_emissions = []
        for route_key, data in sorted(route_emissions.items(), key=lambda x: x[1]['carbon_kg'], reverse=True)[:10]:
            top_routes_by_emissions.append({
                'route': route_key,
                'carbon_kg': round(data['carbon_kg'], 2),
                'trips': data['trips'],
                'avg_carbon_per_trip': round(data['carbon_kg'] / data['trips'], 2) if data['trips'] > 0 else 0
            })

        # Calculate carbon efficiency (kg CO2 per dollar spent)
        carbon_efficiency = float(total_emissions / total_spend) if total_spend > 0 else 0

        return Response({
            'summary': {
                'total_emissions_kg': float(total_emissions),
                'total_emissions_tonnes': round(float(total_emissions) / 1000, 2),
                'domestic_emissions_kg': float(total_emissions_domestic),
                'international_emissions_kg': float(total_emissions_international),
                'air_emissions_kg': float(total_emissions_air),
                'total_spend': float(total_spend),
                'carbon_efficiency': round(carbon_efficiency, 4)
            },
            'monthly_trend': monthly_trend,
            'top_emitters': top_emitters,
            'top_routes_by_emissions': top_routes_by_emissions
        })

    @action(detail=False, methods=['get'])
    def supplier_autocomplete(self, request):
        """
        Get autocomplete suggestions for suppliers based on type.
        Query params:
        - type: 'airline', 'hotel', or 'car_rental'
        - search: optional search query
        - organization: optional organization filter
        """
        user = request.user
        supplier_type = request.query_params.get('type', '')
        search_query = request.query_params.get('search', '')
        organization_id = request.query_params.get('organization')

        # Build base queryset using same logic as get_queryset()
        if user.user_type == 'ADMIN':
            base_queryset = Booking.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            base_queryset = Booking.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            base_queryset = Booking.objects.filter(organization=user.organization)

        # Apply organization filter if provided
        if organization_id:
            base_queryset = base_queryset.filter(organization_id=organization_id)

        results = []

        if supplier_type == 'airline':
            # Get airlines from air bookings
            from apps.reference_data.models import Airline
            airline_codes = AirBooking.objects.filter(
                booking__in=base_queryset,
                primary_airline_iata_code__isnull=False
            ).exclude(
                primary_airline_iata_code=''
            ).values_list('primary_airline_iata_code', flat=True).distinct()

            airlines = Airline.objects.filter(iata_code__in=airline_codes)

            if search_query:
                airlines = airlines.filter(
                    Q(name__icontains=search_query) |
                    Q(iata_code__icontains=search_query)
                )

            results = [
                {
                    'value': airline.name,
                    'label': f"{airline.name} ({airline.iata_code})",
                    'subtitle': None
                }
                for airline in airlines[:50]
            ]

        elif supplier_type == 'hotel':
            # Get hotels from master data (Hotel model)
            from apps.reference_data.models import Hotel, HotelAlias

            # Start with hotels that have bookings in the base queryset
            hotel_ids = AccommodationBooking.objects.filter(
                booking__in=base_queryset,
                hotel__isnull=False
            ).values_list('hotel_id', flat=True).distinct()

            hotels = Hotel.objects.filter(
                id__in=hotel_ids,
                is_active=True
            )

            if search_query:
                # Search both canonical name and aliases
                hotels = hotels.filter(
                    Q(canonical_name__icontains=search_query) |
                    Q(hotel_chain__icontains=search_query) |
                    Q(aliases__alias_name__icontains=search_query, aliases__is_active=True)
                ).distinct()

            results = [
                {
                    'value': hotel.canonical_name,
                    'label': f"{hotel.canonical_name} ({hotel.hotel_chain})" if hotel.hotel_chain else hotel.canonical_name,
                    'subtitle': None
                }
                for hotel in hotels[:50]
            ]

        elif supplier_type == 'car_rental':
            # Get unique rental companies
            companies = CarHireBooking.objects.filter(
                booking__in=base_queryset,
                rental_company__isnull=False
            ).values_list('rental_company', flat=True).distinct()

            if search_query:
                companies = CarHireBooking.objects.filter(
                    booking__in=base_queryset,
                    rental_company__icontains=search_query
                ).values_list('rental_company', flat=True).distinct()

            results = [
                {
                    'value': company,
                    'label': company,
                    'subtitle': None
                }
                for company in sorted(companies)[:50]
            ]

        return Response(results)

    @action(detail=False, methods=['get'])
    def city_autocomplete(self, request):
        """
        Get autocomplete suggestions for cities.
        Query params:
        - search: optional search query
        - organization: optional organization filter
        """
        user = request.user
        search_query = request.query_params.get('search', '')
        organization_id = request.query_params.get('organization')

        # Build base queryset using same logic as get_queryset()
        if user.user_type == 'ADMIN':
            base_queryset = Booking.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            base_queryset = Booking.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            base_queryset = Booking.objects.filter(organization=user.organization)

        # Apply organization filter if provided
        if organization_id:
            base_queryset = base_queryset.filter(organization_id=organization_id)

        cities = set()

        # Get cities from air segments (via airports)
        from apps.reference_data.models import Airport
        air_segments = AirSegment.objects.filter(
            air_booking__booking__in=base_queryset
        ).values_list('origin_airport_iata_code', 'destination_airport_iata_code')

        iata_codes = set()
        for origin_code, dest_code in air_segments:
            if origin_code:
                iata_codes.add(origin_code)
            if dest_code:
                iata_codes.add(dest_code)

        if iata_codes:
            airport_cities = Airport.objects.filter(
                iata_code__in=iata_codes
            ).values_list('city', flat=True).distinct()
            cities.update(airport_cities)

        # Get cities from accommodation
        accommodation_cities = AccommodationBooking.objects.filter(
            booking__in=base_queryset,
            city__isnull=False
        ).values_list('city', flat=True).distinct()
        cities.update(accommodation_cities)

        # Get cities from car hire
        car_pickup_cities = CarHireBooking.objects.filter(
            booking__in=base_queryset,
            pickup_city__isnull=False
        ).values_list('pickup_city', flat=True).distinct()
        cities.update(car_pickup_cities)

        car_dropoff_cities = CarHireBooking.objects.filter(
            booking__in=base_queryset,
            dropoff_city__isnull=False
        ).values_list('dropoff_city', flat=True).distinct()
        cities.update(car_dropoff_cities)

        # Filter by search query if provided
        if search_query:
            cities = [city for city in cities if search_query.lower() in city.lower()]

        # Sort and format results
        city_list = sorted(cities)[:50]
        results = [
            {
                'value': city,
                'label': city,
                'subtitle': None
            }
            for city in city_list
        ]

        return Response(results)

    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """
        Get executive dashboard summary with domestic/international breakdown.
        Returns comprehensive metrics for the dashboard view.
        """
        user = request.user

        # Build base queryset using same logic as get_queryset()
        if user.user_type == 'ADMIN':
            base_queryset = Booking.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            base_queryset = Booking.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            base_queryset = Booking.objects.filter(organization=user.organization)

        # Apply filters from query params (reuse existing filter logic)
        organization_id = request.query_params.get('organization')
        if organization_id:
            base_queryset = base_queryset.filter(organization_id=organization_id)

        # Get organization's home country for domestic/international classification
        home_country = 'AUS'  # Default
        if organization_id:
            try:
                org = Organization.objects.get(id=organization_id)
                home_country = org.home_country
            except Organization.DoesNotExist:
                pass
        elif user.organization:
            home_country = user.organization.home_country

        # Initialize summary data
        summary = {
            'total_bookings': 0,
            'total_spend': 0,
            'total_spend_domestic': 0,
            'total_spend_international': 0,
            'air_bookings': 0,
            'air_spend': 0,
            'air_spend_domestic': 0,
            'air_spend_international': 0,
            'accommodation_bookings': 0,
            'accommodation_spend': 0,
            'accommodation_spend_domestic': 0,
            'accommodation_spend_international': 0,
            'car_hire_bookings': 0,
            'car_hire_spend': 0,
            'car_hire_spend_domestic': 0,
            'car_hire_spend_international': 0,
            'service_fees_count': 0,
            'service_fees_spend': 0,
            'other_products_count': 0,
            'other_products_spend': 0,
            'total_carbon_kg': 0,
            'compliance_rate': 0,
            'violation_count': 0,
            'critical_violations': 0,
        }

        bookings = base_queryset.select_related('organization', 'traveller').prefetch_related(
            'air_bookings__segments',
            'accommodation_bookings',
            'car_hire_bookings',
            'service_fees',
            'other_products',
            'violations'
        )

        summary['total_bookings'] = bookings.count()

        # Process each booking
        for booking in bookings:
            # Track booking-level domestic/international status
            # A booking is international if ANY component is international
            # Only if ALL components are domestic is the booking domestic
            booking_is_domestic = True  # Default to domestic unless we find international components
            has_travel_components = False  # Track if booking has any travel components

            # AIR BOOKINGS
            if booking.air_bookings.exists():
                for air in booking.air_bookings.all():
                    has_travel_components = True
                    # Calculate air spend (total fare including taxes/GST for dashboard)
                    air_amount = float(air.total_fare or 0)

                    # Add any exchange tickets, refunds, or other transactions for this air booking
                    air_content_type = ContentType.objects.get_for_model(AirBooking)
                    air_transactions = BookingTransaction.objects.filter(
                        content_type=air_content_type,
                        object_id=air.id,
                        status__in=['CONFIRMED', 'PENDING']  # Exclude CANCELLED transactions
                    )

                    # Sum transaction amounts (can be negative for refunds)
                    transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in air_transactions)
                    air_amount += transaction_total

                    summary['air_spend'] += air_amount
                    summary['air_bookings'] += 1

                    # Classify as domestic or international
                    is_domestic = False
                    if air.segments.exists():
                        # Check if all segments are domestic
                        all_domestic = True
                        for segment in air.segments.all():
                            if segment.origin_airport and segment.destination_airport:
                                # Get country codes from airport country names
                                origin_country_code = None
                                dest_country_code = None

                                if segment.origin_airport.country:
                                    try:
                                        origin_country = Country.objects.get(name__iexact=segment.origin_airport.country)
                                        origin_country_code = origin_country.alpha_3
                                    except Country.DoesNotExist:
                                        # Fallback for common country names
                                        if segment.origin_airport.country.upper() in ['AUSTRALIA', 'AUS']:
                                            origin_country_code = 'AUS'

                                if segment.destination_airport.country:
                                    try:
                                        dest_country = Country.objects.get(name__iexact=segment.destination_airport.country)
                                        dest_country_code = dest_country.alpha_3
                                    except Country.DoesNotExist:
                                        # Fallback for common country names
                                        if segment.destination_airport.country.upper() in ['AUSTRALIA', 'AUS']:
                                            dest_country_code = 'AUS'

                                if origin_country_code != home_country or dest_country_code != home_country:
                                    all_domestic = False
                                    break
                        is_domestic = all_domestic

                    if is_domestic:
                        summary['air_spend_domestic'] += air_amount
                    else:
                        summary['air_spend_international'] += air_amount
                        booking_is_domestic = False  # Mark booking as international

                    # Add carbon emissions
                    summary['total_carbon_kg'] += float(air.total_carbon_kg or 0)

            # ACCOMMODATION BOOKINGS
            if booking.accommodation_bookings.exists():
                for accom in booking.accommodation_bookings.all():
                    has_travel_components = True
                    # total_amount_base is already the total (nightly_rate * nights), don't multiply again
                    accom_amount = float(accom.total_amount_base or 0)
                    # Fallback: calculate from nightly rate if total_amount_base is not set
                    if accom_amount == 0 and accom.nightly_rate:
                        accom_amount = float(accom.nightly_rate) * accom.number_of_nights

                    # Add any modifications, cancellations, or other transactions for this accommodation
                    accom_content_type = ContentType.objects.get_for_model(AccommodationBooking)
                    accom_transactions = BookingTransaction.objects.filter(
                        content_type=accom_content_type,
                        object_id=accom.id,
                        status__in=['CONFIRMED', 'PENDING']
                    )

                    # Sum transaction amounts (can be negative for refunds)
                    transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in accom_transactions)
                    accom_amount += transaction_total

                    summary['accommodation_spend'] += accom_amount
                    summary['accommodation_bookings'] += 1

                    # Classify as domestic or international based on country
                    # Get country code from reference data if available
                    is_domestic = False
                    if accom.country:
                        try:
                            country = Country.objects.get(name__iexact=accom.country)
                            is_domestic = (country.alpha_3 == home_country)
                        except Country.DoesNotExist:
                            # Fallback: check if country name matches home country name
                            is_domestic = (accom.country.upper() in ['AUSTRALIA', 'AUS']) if home_country == 'AUS' else False

                    if is_domestic:
                        summary['accommodation_spend_domestic'] += accom_amount
                    else:
                        summary['accommodation_spend_international'] += accom_amount
                        booking_is_domestic = False  # Mark booking as international

            # CAR HIRE BOOKINGS
            if booking.car_hire_bookings.exists():
                for car in booking.car_hire_bookings.all():
                    has_travel_components = True
                    car_amount = float(car.total_amount_base or car.total_cost or 0)

                    # Add any modifications, cancellations, or other transactions for this car hire
                    car_content_type = ContentType.objects.get_for_model(CarHireBooking)
                    car_transactions = BookingTransaction.objects.filter(
                        content_type=car_content_type,
                        object_id=car.id,
                        status__in=['CONFIRMED', 'PENDING']
                    )

                    # Sum transaction amounts (can be negative for refunds)
                    transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in car_transactions)
                    car_amount += transaction_total

                    summary['car_hire_spend'] += car_amount
                    summary['car_hire_bookings'] += 1

                    # Classify as domestic or international
                    is_domestic = False
                    if car.country:
                        try:
                            country = Country.objects.get(name__iexact=car.country)
                            is_domestic = (country.alpha_3 == home_country)
                        except Country.DoesNotExist:
                            is_domestic = (car.country.upper() in ['AUSTRALIA', 'AUS']) if home_country == 'AUS' else False

                    if is_domestic:
                        summary['car_hire_spend_domestic'] += car_amount
                    else:
                        summary['car_hire_spend_international'] += car_amount
                        booking_is_domestic = False  # Mark booking as international

            # SERVICE FEES - Classified based on booking-level domestic/international status
            if booking.service_fees.exists():
                for fee in booking.service_fees.all():
                    fee_amount = float(fee.fee_amount or 0)

                    # Add any transactions for this service fee (if applicable)
                    fee_content_type = ContentType.objects.get_for_model(ServiceFee)
                    fee_transactions = BookingTransaction.objects.filter(
                        content_type=fee_content_type,
                        object_id=fee.id,
                        status__in=['CONFIRMED', 'PENDING']
                    )

                    # Sum transaction amounts
                    transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in fee_transactions)
                    fee_amount += transaction_total

                    summary['service_fees_spend'] += fee_amount
                    summary['service_fees_count'] += 1

                    # Apply booking-level classification
                    if has_travel_components:
                        if booking_is_domestic:
                            summary['total_spend_domestic'] += fee_amount
                        else:
                            summary['total_spend_international'] += fee_amount

            # OTHER PRODUCTS (Insurance, Cruise, etc.) - Classified based on booking-level domestic/international status
            if booking.other_products.exists():
                from apps.bookings.models import OtherProduct
                for other in booking.other_products.all():
                    other_amount = float(other.amount_base or other.amount or 0)

                    # Add any transactions for this other product (if applicable)
                    other_content_type = ContentType.objects.get_for_model(OtherProduct)
                    other_transactions = BookingTransaction.objects.filter(
                        content_type=other_content_type,
                        object_id=other.id,
                        status__in=['CONFIRMED', 'PENDING']
                    )

                    # Sum transaction amounts
                    transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in other_transactions)
                    other_amount += transaction_total

                    summary['other_products_spend'] += other_amount
                    summary['other_products_count'] += 1

                    # Apply booking-level classification
                    if has_travel_components:
                        if booking_is_domestic:
                            summary['total_spend_domestic'] += other_amount
                        else:
                            summary['total_spend_international'] += other_amount

        # Calculate total spend
        summary['total_spend'] = summary['air_spend'] + summary['accommodation_spend'] + summary['car_hire_spend'] + summary['service_fees_spend'] + summary['other_products_spend']

        # Calculate domestic/international totals
        # Note: total_spend_domestic and total_spend_international already include service fees and other products (added incrementally above)
        # Now add the travel components (air, accommodation, car hire)
        summary['total_spend_domestic'] += summary['air_spend_domestic'] + summary['accommodation_spend_domestic'] + summary['car_hire_spend_domestic']
        summary['total_spend_international'] += summary['air_spend_international'] + summary['accommodation_spend_international'] + summary['car_hire_spend_international']

        # Get compliance data
        violations = ComplianceViolation.objects.filter(booking__in=bookings)
        summary['violation_count'] = violations.count()
        summary['critical_violations'] = violations.filter(severity='CRITICAL').count()

        # Calculate compliance rate
        if summary['total_bookings'] > 0:
            compliant_bookings = summary['total_bookings'] - bookings.filter(violations__isnull=False).distinct().count()
            summary['compliance_rate'] = round((compliant_bookings / summary['total_bookings']) * 100, 1)

        return Response(summary)

    @action(detail=False, methods=['get'])
    def top_rankings(self, request):
        """
        Get top rankings for cost centers and travellers.
        Returns top performers by trip count, spend, carbon, and compliance.
        """
        user = request.user

        # Build base queryset using same logic as get_queryset()
        if user.user_type == 'ADMIN':
            base_queryset = Booking.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            base_queryset = Booking.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            base_queryset = Booking.objects.filter(organization=user.organization)

        # Apply filters from query params
        organization_id = request.query_params.get('organization')
        if organization_id:
            base_queryset = base_queryset.filter(organization_id=organization_id)

        bookings = base_queryset.select_related('organization', 'traveller').prefetch_related(
            'air_bookings__segments',
            'accommodation_bookings',
            'car_hire_bookings',
            'service_fees',
            'other_products',
            'violations'
        )

        # Aggregate by cost center
        cost_center_data = {}
        traveller_data = {}

        for booking in bookings:
            # cost_center is on Traveller model, not Booking model
            cost_center = booking.traveller.cost_center if (booking.traveller and booking.traveller.cost_center) else 'Unassigned'
            traveller_id = str(booking.traveller.id) if booking.traveller else 'Unknown'
            traveller_name = str(booking.traveller) if booking.traveller else 'Unknown'

            # Initialize cost center aggregation
            if cost_center not in cost_center_data:
                cost_center_data[cost_center] = {
                    'cost_center': cost_center,
                    'trip_count': 0,
                    'total_spend': 0,
                    'total_carbon_kg': 0,
                    'total_bookings': 0,
                    'compliant_bookings': 0,
                    'lost_savings': 0,
                    'cost_of_change': 0
                }

            # Initialize traveller aggregation
            if traveller_id not in traveller_data:
                traveller_data[traveller_id] = {
                    'traveller_id': traveller_id,
                    'traveller_name': traveller_name,
                    'trip_count': 0,
                    'total_spend': 0,
                    'total_carbon_kg': 0,
                    'total_bookings': 0,
                    'compliant_bookings': 0,
                    'lost_savings': 0,
                    'cost_of_change': 0
                }

            # Calculate booking spend
            booking_spend = 0

            # Add air spend (total fare including taxes/GST for dashboard, plus transactions)
            for air in booking.air_bookings.all():
                air_amount = float(air.total_fare or 0)

                # Add any exchange tickets, refunds, or other transactions
                air_content_type = ContentType.objects.get_for_model(AirBooking)
                air_transactions = BookingTransaction.objects.filter(
                    content_type=air_content_type,
                    object_id=air.id,
                    status__in=['CONFIRMED', 'PENDING']
                )
                transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in air_transactions)
                air_amount += transaction_total

                # Calculate cost of change (exchange and reissue fees only)
                change_transactions = BookingTransaction.objects.filter(
                    content_type=air_content_type,
                    object_id=air.id,
                    transaction_type__in=['EXCHANGE', 'REISSUE'],
                    status__in=['CONFIRMED', 'PENDING']
                )
                change_cost = sum(float(t.total_amount_base or t.total_amount or 0) for t in change_transactions)
                cost_center_data[cost_center]['cost_of_change'] += change_cost
                traveller_data[traveller_id]['cost_of_change'] += change_cost

                # Add potential savings (lost savings)
                potential_savings = float(air.potential_savings or 0)
                cost_center_data[cost_center]['lost_savings'] += potential_savings
                traveller_data[traveller_id]['lost_savings'] += potential_savings

                booking_spend += air_amount
                cost_center_data[cost_center]['total_carbon_kg'] += float(air.total_carbon_kg or 0)
                traveller_data[traveller_id]['total_carbon_kg'] += float(air.total_carbon_kg or 0)

            # Add accommodation spend (including modifications, cancellations, etc.)
            for accom in booking.accommodation_bookings.all():
                accom_amount = float(accom.total_amount_base or 0)
                if accom_amount == 0 and accom.nightly_rate:
                    accom_amount = float(accom.nightly_rate) * accom.number_of_nights

                # Add any modifications or transactions
                accom_content_type = ContentType.objects.get_for_model(AccommodationBooking)
                accom_transactions = BookingTransaction.objects.filter(
                    content_type=accom_content_type,
                    object_id=accom.id,
                    status__in=['CONFIRMED', 'PENDING']
                )
                transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in accom_transactions)
                accom_amount += transaction_total

                booking_spend += accom_amount

            # Add car hire spend (including modifications, cancellations, etc.)
            for car in booking.car_hire_bookings.all():
                car_amount = float(car.total_amount_base or 0)

                # Add any modifications or transactions
                car_content_type = ContentType.objects.get_for_model(CarHireBooking)
                car_transactions = BookingTransaction.objects.filter(
                    content_type=car_content_type,
                    object_id=car.id,
                    status__in=['CONFIRMED', 'PENDING']
                )
                transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in car_transactions)
                car_amount += transaction_total

                booking_spend += car_amount

            # Add service fees spend (including any transactions)
            for fee in booking.service_fees.all():
                fee_amount = float(fee.fee_amount or 0)

                # Add any transactions
                fee_content_type = ContentType.objects.get_for_model(ServiceFee)
                fee_transactions = BookingTransaction.objects.filter(
                    content_type=fee_content_type,
                    object_id=fee.id,
                    status__in=['CONFIRMED', 'PENDING']
                )
                transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in fee_transactions)
                fee_amount += transaction_total

                booking_spend += fee_amount

            # Add other products spend (insurance, cruise, etc. - including any transactions)
            for other in booking.other_products.all():
                other_amount = float(other.amount_base or other.amount or 0)

                # Add any transactions
                other_content_type = ContentType.objects.get_for_model(OtherProduct)
                other_transactions = BookingTransaction.objects.filter(
                    content_type=other_content_type,
                    object_id=other.id,
                    status__in=['CONFIRMED', 'PENDING']
                )
                transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in other_transactions)
                other_amount += transaction_total

                booking_spend += other_amount

            # Update aggregations
            cost_center_data[cost_center]['trip_count'] += 1
            cost_center_data[cost_center]['total_spend'] += booking_spend
            cost_center_data[cost_center]['total_bookings'] += 1

            traveller_data[traveller_id]['trip_count'] += 1
            traveller_data[traveller_id]['total_spend'] += booking_spend
            traveller_data[traveller_id]['total_bookings'] += 1

            # Check compliance
            has_violations = booking.violations.exists()
            if not has_violations:
                cost_center_data[cost_center]['compliant_bookings'] += 1
                traveller_data[traveller_id]['compliant_bookings'] += 1

        # Calculate compliance rates and format results
        cost_centers = []
        for cc_data in cost_center_data.values():
            compliance_rate = 0
            if cc_data['total_bookings'] > 0:
                compliance_rate = round((cc_data['compliant_bookings'] / cc_data['total_bookings']) * 100, 1)
            cost_centers.append({
                'cost_center': cc_data['cost_center'],
                'trip_count': cc_data['trip_count'],
                'total_spend': cc_data['total_spend'],
                'total_carbon_kg': cc_data['total_carbon_kg'],
                'compliance_rate': compliance_rate,
                'lost_savings': cc_data['lost_savings'],
                'cost_of_change': cc_data['cost_of_change']
            })

        travellers = []
        for t_data in traveller_data.values():
            if t_data['traveller_id'] == 'Unknown':
                continue  # Skip unknown travellers
            compliance_rate = 0
            if t_data['total_bookings'] > 0:
                compliance_rate = round((t_data['compliant_bookings'] / t_data['total_bookings']) * 100, 1)
            travellers.append({
                'traveller_id': t_data['traveller_id'],
                'traveller_name': t_data['traveller_name'],
                'trip_count': t_data['trip_count'],
                'total_spend': t_data['total_spend'],
                'total_carbon_kg': t_data['total_carbon_kg'],
                'compliance_rate': compliance_rate,
                'lost_savings': t_data['lost_savings'],
                'cost_of_change': t_data['cost_of_change']
            })

        # Sort and get top N for each category
        limit = int(request.query_params.get('limit', 10))

        rankings = {
            'cost_centers': {
                'by_trips': sorted(cost_centers, key=lambda x: x['trip_count'], reverse=True)[:limit],
                'by_spend': sorted(cost_centers, key=lambda x: x['total_spend'], reverse=True)[:limit],
                'by_carbon': sorted(cost_centers, key=lambda x: x['total_carbon_kg'], reverse=True)[:limit],
                'by_compliance': sorted(cost_centers, key=lambda x: x['compliance_rate'], reverse=True)[:limit],
                'by_lost_savings': sorted(cost_centers, key=lambda x: x['lost_savings'], reverse=True)[:limit],
                'by_cost_of_change': sorted(cost_centers, key=lambda x: x['cost_of_change'], reverse=True)[:limit],
            },
            'travellers': {
                'by_trips': sorted(travellers, key=lambda x: x['trip_count'], reverse=True)[:limit],
                'by_spend': sorted(travellers, key=lambda x: x['total_spend'], reverse=True)[:limit],
                'by_carbon': sorted(travellers, key=lambda x: x['total_carbon_kg'], reverse=True)[:limit],
                'by_compliance': sorted(travellers, key=lambda x: x['compliance_rate'], reverse=True)[:limit],
                'by_lost_savings': sorted(travellers, key=lambda x: x['lost_savings'], reverse=True)[:limit],
                'by_cost_of_change': sorted(travellers, key=lambda x: x['cost_of_change'], reverse=True)[:limit],
            }
        }

        return Response(rankings)


# ============================================================================
# BUDGET VIEWSETS
# ============================================================================

class FiscalYearViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for fiscal years.
    """
    serializer_class = FiscalYearSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['organization', 'is_active', 'is_current']

    def get_queryset(self):
        user = self.request.user

        if user.user_type == 'ADMIN':
            return FiscalYear.objects.all().order_by('-start_date')
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            return FiscalYear.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            ).order_by('-start_date')
        else:
            return FiscalYear.objects.filter(
                organization=user.organization
            ).order_by('-start_date')


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

    @action(detail=False, methods=['get'])
    def budget_summary(self, request):
        """
        Get aggregated budget summary for dashboard display.
        Returns overall budget vs actual with status breakdown.
        """
        user = request.user

        # Get organization ID from query params or user's organization
        organization_id = request.query_params.get('organization')

        # Build base queryset
        if user.user_type == 'ADMIN':
            budgets_qs = Budget.objects.filter(is_active=True)
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            budgets_qs = Budget.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization),
                is_active=True
            )
        else:
            budgets_qs = Budget.objects.filter(
                organization=user.organization,
                is_active=True
            )

        # Filter by organization if specified
        if organization_id:
            budgets_qs = budgets_qs.filter(organization_id=organization_id)

        # Get current fiscal year budgets (or all if no current FY)
        try:
            if organization_id:
                org = Organization.objects.get(id=organization_id)
            elif user.organization:
                org = user.organization
            else:
                org = None

            if org:
                current_fy = FiscalYear.objects.filter(
                    organization=org,
                    is_current=True
                ).first()

                if current_fy:
                    budgets_qs = budgets_qs.filter(fiscal_year=current_fy)
        except Organization.DoesNotExist:
            pass

        budgets = budgets_qs.select_related('organization', 'fiscal_year')

        # Initialize summary
        summary = {
            'total_budgets': 0,
            'total_allocated': 0,
            'total_spent': 0,
            'total_remaining': 0,
            'overall_utilization': 0,
            'budgets_ok': 0,
            'budgets_warning': 0,
            'budgets_critical': 0,
            'budgets_exceeded': 0,
            'critical_budgets': [],  # List of cost centers that are critical/exceeded
        }

        # Process each budget
        for budget in budgets:
            summary['total_budgets'] += 1
            summary['total_allocated'] += float(budget.total_budget)

            # Get budget status (includes spent, remaining, percentage, status)
            status_info = budget.get_budget_status()
            spent = float(status_info['spent'])
            remaining = float(status_info['remaining'])
            percentage = status_info['percentage']
            status = status_info['status']

            summary['total_spent'] += spent
            summary['total_remaining'] += remaining

            # Count by status
            if percentage > 100:
                summary['budgets_exceeded'] += 1
                summary['critical_budgets'].append({
                    'cost_center': budget.cost_center,
                    'cost_center_name': budget.cost_center_name,
                    'allocated': float(budget.total_budget),
                    'spent': spent,
                    'percentage': percentage,
                    'status': 'EXCEEDED'
                })
            elif status == 'CRITICAL':
                summary['budgets_critical'] += 1
                summary['critical_budgets'].append({
                    'cost_center': budget.cost_center,
                    'cost_center_name': budget.cost_center_name,
                    'allocated': float(budget.total_budget),
                    'spent': spent,
                    'percentage': percentage,
                    'status': status
                })
            elif status == 'WARNING':
                summary['budgets_warning'] += 1
            else:
                summary['budgets_ok'] += 1

        # Calculate overall utilization
        if summary['total_allocated'] > 0:
            summary['overall_utilization'] = round(
                (summary['total_spent'] / summary['total_allocated']) * 100,
                1
            )

        return Response(summary)

    @action(detail=False, methods=['get'])
    def burn_rate_analysis(self, request):
        """
        Get budget burn rate analysis and forecasting.

        Returns:
        - Monthly spending trend
        - Burn rate (spending per month)
        - Projected spend for fiscal year
        - Budget forecast and risk assessment
        """
        from collections import defaultdict
        from datetime import datetime, timedelta, date
        from decimal import Decimal
        from calendar import monthrange

        def add_months(source_date, months):
            """Add months to a date"""
            month = source_date.month - 1 + months
            year = source_date.year + month // 12
            month = month % 12 + 1
            day = min(source_date.day, monthrange(year, month)[1])
            return date(year, month, day)

        user = request.user
        organization_id = request.query_params.get('organization')

        # Build base budget queryset
        if user.user_type == 'ADMIN':
            budgets_qs = Budget.objects.filter(is_active=True)
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            budgets_qs = Budget.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization),
                is_active=True
            )
        else:
            budgets_qs = Budget.objects.filter(
                organization=user.organization,
                is_active=True
            )

        # Filter by organization if specified
        if organization_id:
            budgets_qs = budgets_qs.filter(organization_id=organization_id)

        # Get current fiscal year
        try:
            if organization_id:
                org = Organization.objects.get(id=organization_id)
            elif user.organization:
                org = user.organization
            else:
                org = None

            if org:
                current_fy = FiscalYear.objects.filter(
                    organization=org,
                    is_current=True
                ).first()

                if not current_fy:
                    return Response({
                        'error': 'No current fiscal year found'
                    }, status=400)

                budgets_qs = budgets_qs.filter(fiscal_year=current_fy)

                fy_start = current_fy.start_date
                fy_end = current_fy.end_date
            else:
                return Response({
                    'error': 'No organization found'
                }, status=400)
        except Organization.DoesNotExist:
            return Response({
                'error': 'Organization not found'
            }, status=404)

        # Get bookings for this organization in the fiscal year
        if user.user_type == 'ADMIN':
            bookings_qs = Booking.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            bookings_qs = Booking.objects.filter(
                Q(organization=user.organization) |
                Q(organization__travel_agent=user.organization)
            )
        else:
            bookings_qs = Booking.objects.filter(organization=user.organization)

        if organization_id:
            bookings_qs = bookings_qs.filter(organization_id=organization_id)

        # Filter bookings by fiscal year
        bookings_qs = bookings_qs.filter(
            travel_date__gte=fy_start,
            travel_date__lte=fy_end
        )

        # Calculate monthly spending
        monthly_spend = defaultdict(Decimal)
        for booking in bookings_qs:
            month_key = booking.travel_date.strftime('%Y-%m')
            monthly_spend[month_key] += booking.total_amount or Decimal('0')

        # Get total budget allocated
        total_budget = sum(float(b.total_budget) for b in budgets_qs)
        total_spent = sum(float(v) for v in monthly_spend.values())

        # Calculate months elapsed and remaining
        today = datetime.now().date()
        months_elapsed = ((today.year - fy_start.year) * 12 + today.month - fy_start.month) + 1
        total_months = ((fy_end.year - fy_start.year) * 12 + fy_end.month - fy_start.month) + 1
        months_remaining = total_months - months_elapsed

        # Calculate burn rate (average spend per month)
        burn_rate = total_spent / months_elapsed if months_elapsed > 0 else 0

        # Project end-of-year spend
        projected_total_spend = total_spent + (burn_rate * months_remaining)

        # Calculate budget health
        if total_budget > 0:
            current_utilization = (total_spent / total_budget) * 100
            projected_utilization = (projected_total_spend / total_budget) * 100

            if projected_utilization > 100:
                status = 'WILL_EXCEED'
                risk_level = 'HIGH'
            elif projected_utilization > 95:
                status = 'AT_RISK'
                risk_level = 'MEDIUM'
            elif projected_utilization > 80:
                status = 'ON_TRACK_WARN'
                risk_level = 'LOW'
            else:
                status = 'ON_TRACK'
                risk_level = 'LOW'
        else:
            current_utilization = 0
            projected_utilization = 0
            status = 'NO_BUDGET'
            risk_level = 'UNKNOWN'

        # Format monthly trend data
        monthly_trend = []
        current_month = fy_start
        cumulative_spend = 0
        cumulative_budget_allocation = 0
        monthly_budget_allocation = total_budget / total_months if total_months > 0 else 0

        while current_month <= fy_end:
            month_key = current_month.strftime('%Y-%m')
            month_spend = float(monthly_spend.get(month_key, 0))
            cumulative_spend += month_spend
            cumulative_budget_allocation += monthly_budget_allocation

            monthly_trend.append({
                'month': month_key,
                'spend': round(month_spend, 2),
                'cumulative_spend': round(cumulative_spend, 2),
                'cumulative_budget': round(cumulative_budget_allocation, 2),
                'is_actual': current_month <= today
            })

            current_month = add_months(current_month, 1)

        return Response({
            'fiscal_year': {
                'start_date': fy_start.isoformat(),
                'end_date': fy_end.isoformat(),
                'total_months': total_months,
                'months_elapsed': months_elapsed,
                'months_remaining': months_remaining
            },
            'summary': {
                'total_budget': round(total_budget, 2),
                'total_spent': round(total_spent, 2),
                'burn_rate': round(burn_rate, 2),
                'projected_total_spend': round(projected_total_spend, 2),
                'projected_overrun': round(max(0, projected_total_spend - total_budget), 2),
                'current_utilization': round(current_utilization, 2),
                'projected_utilization': round(projected_utilization, 2),
                'status': status,
                'risk_level': risk_level
            },
            'monthly_trend': monthly_trend
        })


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
    filterset_fields = ['organization', 'fee_type', 'traveller', 'booking_channel']
    search_fields = ['description']
    ordering_fields = ['fee_date', 'fee_amount']
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

    @action(detail=False, methods=['get'])
    def fee_type_choices(self, request):
        """
        Get available fee type choices from the model.
        Returns dynamic list so new fee types can be added without frontend changes.
        """
        choices = [
            {'value': choice[0], 'label': choice[1]}
            for choice in ServiceFee.FEE_TYPES
        ]
        return Response(choices)

# ============================================================================
# COMPLIANCE VIEWSET
# ============================================================================

class ComplianceViolationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for compliance violations"""
    serializer_class = ComplianceViolationSerializer
    filterset_fields = ['organization', 'violation_type', 'severity', 'is_waived']
    search_fields = ['booking__agent_booking_reference', 'traveller__first_name', 'traveller__last_name', 'violation_description']
    ordering_fields = ['detected_at', 'variance_amount', 'severity']
    ordering = ['-detected_at']

    def get_queryset(self):
        user = self.request.user

        if user.user_type == 'ADMIN':
            return ComplianceViolation.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            if user.organization:
                return ComplianceViolation.objects.filter(
                    Q(organization=user.organization) |
                    Q(organization__travel_agent=user.organization)
                )
        elif user.user_type in ['CUSTOMER_ADMIN', 'CUSTOMER_RISK', 'CUSTOMER']:
            if user.organization:
                return ComplianceViolation.objects.filter(organization=user.organization)

        return ComplianceViolation.objects.none()

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


# ============================================================================
# ORGANIZATIONAL NODE VIEWSET (Hierarchy Management)
# ============================================================================

class OrganizationalNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing organizational hierarchy nodes.

    Provides:
    - CRUD operations on organizational nodes
    - Tree structure retrieval
    - Root nodes listing
    - Move and merge operations
    """
    serializer_class = OrganizationalNodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['organization', 'node_type', 'parent', 'is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'level', 'lft', 'created_at']
    ordering = ['tree_id', 'lft']  # MPTT tree ordering

    def get_queryset(self):
        """
        Filter organizational nodes based on user's access level.
        """
        user = self.request.user

        # System admins can see all nodes
        if user.user_type == 'ADMIN':
            queryset = OrganizationalNode.objects.all()
        # Travel agents can see nodes for their organization and customer orgs
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            if user.organization:
                # Get customer organization IDs
                customer_org_ids = user.organization.customers.values_list('id', flat=True)
                queryset = OrganizationalNode.objects.filter(
                    organization__in=customer_org_ids
                )
            else:
                queryset = OrganizationalNode.objects.none()
        # Regular users see only their organization's nodes
        else:
            if user.organization:
                queryset = OrganizationalNode.objects.filter(
                    organization=user.organization
                )
            else:
                queryset = OrganizationalNode.objects.none()

        # Apply organization filter from query params if admin
        organization_id = self.request.query_params.get('organization', None)
        if organization_id and user.user_type == 'ADMIN':
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.select_related('organization', 'parent')

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return OrganizationalNodeListSerializer
        elif self.action == 'tree':
            return OrganizationalNodeTreeSerializer
        return OrganizationalNodeSerializer

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Get organizational hierarchy as a tree structure.

        Query params:
        - organization: Filter by organization ID (required for non-admins)

        Returns tree with nested children.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Get only root nodes (no parent)
        root_nodes = queryset.filter(parent__isnull=True, is_active=True)

        serializer = OrganizationalNodeTreeSerializer(
            root_nodes,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def roots(self, request):
        """Get all root nodes (nodes without parent)"""
        queryset = self.filter_queryset(self.get_queryset())
        root_nodes = queryset.filter(parent__isnull=True)

        serializer = self.get_serializer(root_nodes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get immediate children of a node"""
        node = self.get_object()
        children = node.children.filter(is_active=True)

        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        """Get all ancestors of a node"""
        node = self.get_object()
        ancestors = node.get_ancestors()

        serializer = self.get_serializer(ancestors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        """Get all descendants of a node"""
        node = self.get_object()
        descendants = node.get_descendants()

        serializer = self.get_serializer(descendants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """
        Move a node to a new parent.

        Body:
        - target_id: ID of the new parent node (null for root)
        - position: 'first-child', 'last-child', 'left', 'right' (default: 'last-child')
        """
        node = self.get_object()
        target_id = request.data.get('target_id')

        try:
            if target_id:
                target = OrganizationalNode.objects.get(id=target_id)
                # Prevent moving to own descendant
                if node.id in [d.id for d in target.get_descendants(include_self=True)]:
                    return Response(
                        {'error': 'Cannot move node to its own descendant'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                node.parent = target
            else:
                node.parent = None

            node.save()

            serializer = self.get_serializer(node)
            return Response(serializer.data)

        except OrganizationalNode.DoesNotExist:
            return Response(
                {'error': 'Target node not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def merge(self, request, pk=None):
        """
        Merge this node into a target node.
        All children and references are moved to the target.

        Body:
        - target_id: ID of the node to merge into
        """
        source_node = self.get_object()
        target_id = request.data.get('target_id')

        if not target_id:
            return Response(
                {'error': 'target_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_node = OrganizationalNode.objects.get(id=target_id)

            # Cannot merge into self
            if source_node.id == target_node.id:
                return Response(
                    {'error': 'Cannot merge node into itself'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Cannot merge into descendant
            if target_node.id in [d.id for d in source_node.get_descendants()]:
                return Response(
                    {'error': 'Cannot merge into descendant node'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Move all children to target
            for child in source_node.children.all():
                child.parent = target_node
                child.save()

            # Move travellers if they exist
            if hasattr(source_node, 'travellers'):
                source_node.travellers.all().update(organizational_node=target_node)

            # Move budgets if they exist
            if hasattr(source_node, 'budgets'):
                source_node.budgets.all().update(organizational_node=target_node)

            # Delete source node
            source_node.delete()

            # Return updated target
            serializer = self.get_serializer(target_node)
            return Response(serializer.data)

        except OrganizationalNode.DoesNotExist:
            return Response(
                {'error': 'Target node not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def perform_destroy(self, instance):
        """Check if node can be deleted before destroying"""
        if not instance.can_delete():
            raise ValidationError(
                'Cannot delete node with children or associated records. '
                'Please reassign or delete them first.'
            )
        instance.delete()


# ============================================================================
# PREFERRED AIRLINE VIEWSET
# ============================================================================

class PreferredAirlineViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing preferred airline contracts.

    Supports:
    - List all preferred airlines for accessible organizations
    - Retrieve specific preferred airline details
    - Create new preferred airline contracts
    - Update existing contracts
    - Delete contracts
    - Filter by organization, market_type, airline, contract status

    Query parameters:
    - organization: Filter by organization ID
    - market_type: Filter by DOMESTIC or INTERNATIONAL
    - airline_iata_code: Filter by airline code
    - is_active: Filter by active status (true/false)
    - contract_status: Filter by ACTIVE, EXPIRED, FUTURE, INACTIVE
    """
    serializer_class = PreferredAirlineSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'market_type', 'airline_iata_code', 'is_active']
    search_fields = ['airline_name', 'airline_iata_code', 'notes']
    ordering_fields = ['airline_name', 'contract_start_date', 'contract_end_date', 'target_market_share', 'target_revenue', 'created_at']
    ordering = ['organization', 'market_type', 'airline_name']

    def get_queryset(self):
        """
        Filter preferred airlines based on user's organization access.
        Only show airlines for organizations the user has access to.
        """
        user = self.request.user

        if user.user_type == 'ADMIN':
            queryset = PreferredAirline.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            # Travel agents see preferred airlines for their customer organizations
            if user.organization:
                queryset = PreferredAirline.objects.filter(
                    Q(organization=user.organization) |
                    Q(organization__travel_agent=user.organization)
                )
            else:
                queryset = PreferredAirline.objects.all()
        else:
            # Customer users see only their organization's preferred airlines
            if user.organization:
                queryset = PreferredAirline.objects.filter(organization=user.organization)
            else:
                queryset = PreferredAirline.objects.none()

        # Filter by contract_status if provided (custom filter)
        contract_status = self.request.query_params.get('contract_status', None)
        if contract_status:
            from django.utils import timezone
            today = timezone.now().date()

            if contract_status == 'ACTIVE':
                queryset = queryset.filter(
                    is_active=True,
                    contract_start_date__lte=today,
                    contract_end_date__gte=today
                )
            elif contract_status == 'EXPIRED':
                queryset = queryset.filter(
                    is_active=True,
                    contract_end_date__lt=today
                )
            elif contract_status == 'FUTURE':
                queryset = queryset.filter(
                    is_active=True,
                    contract_start_date__gt=today
                )
            elif contract_status == 'INACTIVE':
                queryset = queryset.filter(is_active=False)

        return queryset.select_related('organization', 'created_by')

    def perform_create(self, serializer):
        """Set created_by to current user when creating a new preferred airline"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def active_contracts(self, request):
        """
        Get all currently active preferred airline contracts.
        A contract is active if:
        - is_active = True
        - current date is between contract_start_date and contract_end_date

        Query params supported:
        - organization: Filter by organization ID
        - market_type: Filter by DOMESTIC or INTERNATIONAL
        """
        from django.utils import timezone
        today = timezone.now().date()

        queryset = self.filter_queryset(self.get_queryset())

        # Filter for currently active contracts
        queryset = queryset.filter(
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """
        Get preferred airline contracts expiring within the next N days.

        Query params:
        - days: Number of days to look ahead (default: 30)
        - organization: Filter by organization ID
        """
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        days_ahead = int(request.query_params.get('days', 30))
        expiry_threshold = today + timedelta(days=days_ahead)

        queryset = self.filter_queryset(self.get_queryset())

        # Filter for contracts expiring soon
        queryset = queryset.filter(
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today,
            contract_end_date__lte=expiry_threshold
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a preferred airline contract.
        Sets is_active to False.
        """
        preferred_airline = self.get_object()
        preferred_airline.is_active = False
        preferred_airline.save()

        serializer = self.get_serializer(preferred_airline)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a preferred airline contract.
        Sets is_active to True.
        """
        preferred_airline = self.get_object()
        preferred_airline.is_active = True
        preferred_airline.save()

        serializer = self.get_serializer(preferred_airline)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def compliance_report(self, request):
        """
        Calculate preferred airline compliance metrics.

        Returns spending and booking counts broken down by:
        - Overall compliance rate
        - Compliance by cost center
        - Compliance by traveller
        - Non-compliant bookings (off-preferred airline)

        Query params:
        - organization: Filter by organization ID (required)
        - booking_date__gte: Start date for bookings (optional)
        - booking_date__lte: End date for bookings (optional)
        - travel_date__gte: Travel start date (optional)
        - travel_date__lte: Travel end date (optional)
        - market_type: Filter by DOMESTIC or INTERNATIONAL (optional)

        Returns:
        {
            "summary": {
                "total_spend": 1000000,
                "preferred_spend": 850000,
                "non_preferred_spend": 150000,
                "compliance_rate": 85.0,
                "total_bookings": 500,
                "preferred_bookings": 425,
                "non_preferred_bookings": 75
            },
            "by_cost_center": [...],
            "by_traveller": [...],
            "non_compliant_bookings": [...]
        }
        """
        from django.utils import timezone
        from collections import defaultdict

        # Get organization from query params
        organization_id = request.query_params.get('organization')
        if not organization_id:
            return Response(
                {'error': 'organization parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get date range filters
        booking_date_gte = request.query_params.get('booking_date__gte')
        booking_date_lte = request.query_params.get('booking_date__lte')
        travel_date_gte = request.query_params.get('travel_date__gte')
        travel_date_lte = request.query_params.get('travel_date__lte')
        market_type_filter = request.query_params.get('market_type')

        # Get active preferred airline contracts for this organization
        today = timezone.now().date()
        preferred_airlines = PreferredAirline.objects.filter(
            organization_id=organization_id,
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today
        )

        # Build a lookup for preferred airlines by market type
        preferred_by_market = {
            'DOMESTIC': [],
            'INTERNATIONAL': []
        }
        for pa in preferred_airlines:
            preferred_by_market[pa.market_type].append({
                'iata_code': pa.airline_iata_code,
                'markets_served': pa.markets_served,
                'routes_covered': pa.routes_covered
            })

        # Get all bookings for the organization with filters
        bookings_qs = Booking.objects.filter(organization_id=organization_id)

        if booking_date_gte:
            bookings_qs = bookings_qs.filter(booking_date__gte=booking_date_gte)
        if booking_date_lte:
            bookings_qs = bookings_qs.filter(booking_date__lte=booking_date_lte)
        if travel_date_gte:
            bookings_qs = bookings_qs.filter(travel_date__gte=travel_date_gte)
        if travel_date_lte:
            bookings_qs = bookings_qs.filter(travel_date__lte=travel_date_lte)

        bookings = bookings_qs.select_related('traveller', 'organization').prefetch_related(
            'air_bookings__segments'
        )

        # Initialize aggregations
        summary = {
            'total_spend': 0,
            'preferred_spend': 0,
            'non_preferred_spend': 0,
            'total_bookings': 0,
            'preferred_bookings': 0,
            'non_preferred_bookings': 0
        }

        cost_center_data = defaultdict(lambda: {
            'cost_center': '',
            'cost_center_name': '',
            'total_spend': 0,
            'preferred_spend': 0,
            'non_preferred_spend': 0,
            'total_bookings': 0,
            'preferred_bookings': 0,
            'non_preferred_bookings': 0,
            'compliance_rate': 0
        })

        traveller_data = defaultdict(lambda: {
            'traveller_id': '',
            'traveller_name': '',
            'cost_center': '',
            'total_spend': 0,
            'preferred_spend': 0,
            'non_preferred_spend': 0,
            'total_bookings': 0,
            'preferred_bookings': 0,
            'non_preferred_bookings': 0,
            'compliance_rate': 0
        })

        non_compliant_bookings = []

        # Helper function to determine if booking is domestic or international
        def get_booking_market_type(air_booking):
            """Determine if air booking is DOMESTIC or INTERNATIONAL"""
            home_country = air_booking.booking.organization.home_country or 'AUS'

            # Get home country airports
            home_country_obj = Country.objects.filter(alpha_3=home_country).first()
            if not home_country_obj:
                return 'INTERNATIONAL'  # Default to international if can't determine

            domestic_airports = list(Airport.objects.filter(
                country=home_country_obj.name
            ).values_list('iata_code', flat=True))

            # Check if all segments are domestic
            for segment in air_booking.segments.all():
                origin_domestic = segment.origin_airport_iata_code in domestic_airports
                dest_domestic = segment.destination_airport_iata_code in domestic_airports

                if not (origin_domestic and dest_domestic):
                    return 'INTERNATIONAL'

            return 'DOMESTIC'

        # Helper function to check if booking is on preferred airline
        def is_preferred_airline(air_booking, market_type):
            """Check if air booking is on a preferred airline for this market type"""
            primary_airline = air_booking.primary_airline_iata_code

            if not primary_airline:
                return False

            # Check if airline is in preferred list for this market type
            preferred_list = preferred_by_market.get(market_type, [])

            for preferred in preferred_list:
                if preferred['iata_code'] == primary_airline:
                    # Found matching airline - could add more sophisticated route/market matching here
                    return True

            return False

        # Process each booking
        for booking in bookings:
            if not booking.air_bookings.exists():
                continue  # Skip non-air bookings

            cost_center = booking.traveller.cost_center if booking.traveller and booking.traveller.cost_center else 'Unassigned'
            traveller_id = str(booking.traveller.id) if booking.traveller else 'Unknown'
            traveller_name = str(booking.traveller) if booking.traveller else 'Unknown'

            # Process air bookings
            for air_booking in booking.air_bookings.all():
                # Determine market type
                market_type = get_booking_market_type(air_booking)

                # Skip if filtered by market type
                if market_type_filter and market_type != market_type_filter:
                    continue

                # Calculate spend for this air booking (base fare only, excluding taxes/GST)
                air_spend = float(air_booking.base_fare or 0)

                # Add transactions
                air_content_type = ContentType.objects.get_for_model(AirBooking)
                air_transactions = BookingTransaction.objects.filter(
                    content_type=air_content_type,
                    object_id=air_booking.id,
                    status__in=['CONFIRMED', 'PENDING']
                )
                transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in air_transactions)
                air_spend += transaction_total

                # Check if on preferred airline
                is_preferred = is_preferred_airline(air_booking, market_type)

                # Update summary
                summary['total_spend'] += air_spend
                summary['total_bookings'] += 1

                if is_preferred:
                    summary['preferred_spend'] += air_spend
                    summary['preferred_bookings'] += 1
                else:
                    summary['non_preferred_spend'] += air_spend
                    summary['non_preferred_bookings'] += 1

                    # Add to non-compliant list
                    non_compliant_bookings.append({
                        'booking_id': str(booking.id),
                        'booking_reference': booking.agent_booking_reference,
                        'traveller_name': traveller_name,
                        'cost_center': cost_center,
                        'airline_code': air_booking.primary_airline_iata_code,
                        'airline_name': air_booking.primary_airline_name,
                        'market_type': market_type,
                        'travel_date': booking.travel_date.isoformat() if booking.travel_date else None,
                        'total_fare': air_spend,
                        'origin': air_booking.origin_airport_iata_code,
                        'destination': air_booking.destination_airport_iata_code
                    })

                # Update cost center aggregation
                if cost_center not in cost_center_data:
                    cost_center_data[cost_center]['cost_center'] = cost_center

                cost_center_data[cost_center]['total_spend'] += air_spend
                cost_center_data[cost_center]['total_bookings'] += 1

                if is_preferred:
                    cost_center_data[cost_center]['preferred_spend'] += air_spend
                    cost_center_data[cost_center]['preferred_bookings'] += 1
                else:
                    cost_center_data[cost_center]['non_preferred_spend'] += air_spend
                    cost_center_data[cost_center]['non_preferred_bookings'] += 1

                # Update traveller aggregation
                if traveller_id not in traveller_data:
                    traveller_data[traveller_id]['traveller_id'] = traveller_id
                    traveller_data[traveller_id]['traveller_name'] = traveller_name
                    traveller_data[traveller_id]['cost_center'] = cost_center

                traveller_data[traveller_id]['total_spend'] += air_spend
                traveller_data[traveller_id]['total_bookings'] += 1

                if is_preferred:
                    traveller_data[traveller_id]['preferred_spend'] += air_spend
                    traveller_data[traveller_id]['preferred_bookings'] += 1
                else:
                    traveller_data[traveller_id]['non_preferred_spend'] += air_spend
                    traveller_data[traveller_id]['non_preferred_bookings'] += 1

        # Calculate compliance rates
        if summary['total_spend'] > 0:
            summary['compliance_rate'] = round((summary['preferred_spend'] / summary['total_spend']) * 100, 1)
        else:
            summary['compliance_rate'] = 0

        # Format cost center data
        cost_centers = []
        for cc_data in cost_center_data.values():
            if cc_data['total_spend'] > 0:
                cc_data['compliance_rate'] = round((cc_data['preferred_spend'] / cc_data['total_spend']) * 100, 1)
            cost_centers.append(cc_data)

        # Sort by non-preferred spend (worst offenders first)
        cost_centers.sort(key=lambda x: x['non_preferred_spend'], reverse=True)

        # Format traveller data
        travellers = []
        for t_data in traveller_data.values():
            if t_data['traveller_id'] == 'Unknown':
                continue
            if t_data['total_spend'] > 0:
                t_data['compliance_rate'] = round((t_data['preferred_spend'] / t_data['total_spend']) * 100, 1)
            travellers.append(t_data)

        # Sort by non-preferred spend (worst offenders first)
        travellers.sort(key=lambda x: x['non_preferred_spend'], reverse=True)

        # Sort non-compliant bookings by fare (highest first)
        non_compliant_bookings.sort(key=lambda x: x['total_fare'], reverse=True)

        return Response({
            'summary': summary,
            'by_cost_center': cost_centers,
            'by_traveller': travellers,
            'non_compliant_bookings': non_compliant_bookings[:100]  # Limit to top 100
        })

    @action(detail=False, methods=['get'])
    def market_share_performance(self, request):
        """
        Calculate actual vs target market share for each preferred airline.

        Returns performance metrics for each preferred airline showing:
        - Target market share % and revenue
        - Actual market share % and revenue
        - Variance from target
        - Performance status (EXCEEDING, MEETING, BELOW_TARGET)

        Query params:
        - organization: Filter by organization ID (required)
        - booking_date__gte: Start date for bookings (optional)
        - booking_date__lte: End date for bookings (optional)
        - travel_date__gte: Travel start date (optional)
        - travel_date__lte: Travel end date (optional)
        - market_type: Filter by DOMESTIC or INTERNATIONAL (optional)

        Returns:
        {
            "preferred_airlines": [
                {
                    "airline_code": "QF",
                    "airline_name": "Qantas Airways",
                    "market_type": "DOMESTIC",
                    "target_market_share": 85.0,
                    "target_revenue": 850000.00,
                    "actual_market_share": 78.5,
                    "actual_revenue": 785000.00,
                    "market_share_variance": -6.5,
                    "revenue_variance": -65000.00,
                    "booking_count": 425,
                    "performance_status": "BELOW_TARGET"
                },
                ...
            ],
            "totals": {
                "total_market_revenue": 1000000.00,
                "preferred_airlines_revenue": 850000.00,
                "other_airlines_revenue": 150000.00
            }
        }
        """
        from django.utils import timezone
        from collections import defaultdict

        # Get organization from query params
        organization_id = request.query_params.get('organization')
        if not organization_id:
            return Response(
                {'error': 'organization parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get date range filters
        booking_date_gte = request.query_params.get('booking_date__gte')
        booking_date_lte = request.query_params.get('booking_date__lte')
        travel_date_gte = request.query_params.get('travel_date__gte')
        travel_date_lte = request.query_params.get('travel_date__lte')
        market_type_filter = request.query_params.get('market_type')

        # Get active preferred airline contracts for this organization
        today = timezone.now().date()
        preferred_airlines = PreferredAirline.objects.filter(
            organization_id=organization_id,
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today
        )

        if market_type_filter:
            preferred_airlines = preferred_airlines.filter(market_type=market_type_filter)

        # Initialize performance tracking for each preferred airline
        airline_performance = {}
        for pa in preferred_airlines:
            airline_performance[pa.airline_iata_code] = {
                'airline_code': pa.airline_iata_code,
                'airline_name': pa.airline_name,
                'market_type': pa.market_type,
                'target_market_share': float(pa.target_market_share),
                'target_revenue': float(pa.target_revenue) if pa.target_revenue else None,
                'actual_revenue': 0,
                'booking_count': 0,
                'contract_id': str(pa.id),
                'contract_start_date': pa.contract_start_date.isoformat(),
                'contract_end_date': pa.contract_end_date.isoformat()
            }

        # Track total market revenue by market type
        market_revenue = {
            'DOMESTIC': 0,
            'INTERNATIONAL': 0
        }

        # Get all bookings for the organization with filters
        bookings_qs = Booking.objects.filter(organization_id=organization_id)

        if booking_date_gte:
            bookings_qs = bookings_qs.filter(booking_date__gte=booking_date_gte)
        if booking_date_lte:
            bookings_qs = bookings_qs.filter(booking_date__lte=booking_date_lte)
        if travel_date_gte:
            bookings_qs = bookings_qs.filter(travel_date__gte=travel_date_gte)
        if travel_date_lte:
            bookings_qs = bookings_qs.filter(travel_date__lte=travel_date_lte)

        bookings = bookings_qs.select_related('traveller', 'organization').prefetch_related(
            'air_bookings__segments'
        )

        # Helper function to determine if booking is domestic or international
        def get_booking_market_type(air_booking):
            """Determine if air booking is DOMESTIC or INTERNATIONAL"""
            home_country = air_booking.booking.organization.home_country or 'AUS'

            # Get home country airports
            home_country_obj = Country.objects.filter(alpha_3=home_country).first()
            if not home_country_obj:
                return 'INTERNATIONAL'

            domestic_airports = list(Airport.objects.filter(
                country=home_country_obj.name
            ).values_list('iata_code', flat=True))

            # Check if all segments are domestic
            for segment in air_booking.segments.all():
                origin_domestic = segment.origin_airport_iata_code in domestic_airports
                dest_domestic = segment.destination_airport_iata_code in domestic_airports

                if not (origin_domestic and dest_domestic):
                    return 'INTERNATIONAL'

            return 'DOMESTIC'

        # Process each booking
        for booking in bookings:
            if not booking.air_bookings.exists():
                continue

            for air_booking in booking.air_bookings.all():
                # Determine market type
                market_type = get_booking_market_type(air_booking)

                # Skip if filtered by market type
                if market_type_filter and market_type != market_type_filter:
                    continue

                # Calculate spend for this air booking (base fare only, excluding taxes/GST)
                air_spend = float(air_booking.base_fare or 0)

                # Add transactions
                air_content_type = ContentType.objects.get_for_model(AirBooking)
                air_transactions = BookingTransaction.objects.filter(
                    content_type=air_content_type,
                    object_id=air_booking.id,
                    status__in=['CONFIRMED', 'PENDING']
                )
                transaction_total = sum(float(t.total_amount_base or t.total_amount or 0) for t in air_transactions)
                air_spend += transaction_total

                # Add to total market revenue for this market type
                market_revenue[market_type] += air_spend

                # Check if this booking is on a preferred airline
                airline_code = air_booking.primary_airline_iata_code
                if airline_code and airline_code in airline_performance:
                    # Check if market type matches
                    if airline_performance[airline_code]['market_type'] == market_type:
                        airline_performance[airline_code]['actual_revenue'] += air_spend
                        airline_performance[airline_code]['booking_count'] += 1

        # Calculate market share and variance for each preferred airline
        results = []
        for perf in airline_performance.values():
            market_type = perf['market_type']
            total_market = market_revenue[market_type]

            # Calculate actual market share
            if total_market > 0:
                perf['actual_market_share'] = round((perf['actual_revenue'] / total_market) * 100, 1)
            else:
                perf['actual_market_share'] = 0

            # Calculate variances
            perf['market_share_variance'] = round(
                perf['actual_market_share'] - perf['target_market_share'], 1
            )

            if perf['target_revenue']:
                perf['revenue_variance'] = round(perf['actual_revenue'] - perf['target_revenue'], 2)
                perf['revenue_variance_percent'] = round(
                    (perf['revenue_variance'] / perf['target_revenue']) * 100, 1
                ) if perf['target_revenue'] > 0 else 0
            else:
                perf['revenue_variance'] = None
                perf['revenue_variance_percent'] = None

            # Determine performance status
            if perf['market_share_variance'] >= 0:
                perf['performance_status'] = 'EXCEEDING' if perf['market_share_variance'] > 2 else 'MEETING'
            else:
                perf['performance_status'] = 'BELOW_TARGET'

            results.append(perf)

        # Sort by market share variance (worst performers first for visibility)
        results.sort(key=lambda x: x['market_share_variance'])

        # Calculate totals
        total_revenue = sum(market_revenue.values())
        preferred_revenue = sum(p['actual_revenue'] for p in results)
        other_revenue = total_revenue - preferred_revenue

        return Response({
            'preferred_airlines': results,
            'totals': {
                'total_market_revenue': round(total_revenue, 2),
                'preferred_airlines_revenue': round(preferred_revenue, 2),
                'other_airlines_revenue': round(other_revenue, 2),
                'preferred_market_share': round((preferred_revenue / total_revenue * 100), 1) if total_revenue > 0 else 0
            },
            'by_market_type': {
                'domestic': {
                    'total_revenue': round(market_revenue['DOMESTIC'], 2),
                    'preferred_count': len([p for p in results if p['market_type'] == 'DOMESTIC'])
                },
                'international': {
                    'total_revenue': round(market_revenue['INTERNATIONAL'], 2),
                    'preferred_count': len([p for p in results if p['market_type'] == 'INTERNATIONAL'])
                }
            }
        })

    @action(detail=False, methods=['get'])
    def performance_dashboard(self, request):
        """
        Calculate performance metrics for preferred airline contracts.

        Query params:
        - organization: Filter by organization ID (required)
        - booking_date__gte: Start date (optional)
        - booking_date__lte: End date (optional)

        Returns performance data showing actual vs target metrics.
        """
        from django.utils import timezone
        from collections import defaultdict

        # Get organization from query params
        organization_id = request.query_params.get('organization')
        if not organization_id:
            return Response(
                {'error': 'organization parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get active preferred airline contracts for this organization
        today = timezone.now().date()
        preferred_airlines = PreferredAirline.objects.filter(
            organization_id=organization_id,
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today
        )

        results = []
        total_target_revenue = 0
        total_actual_preferred_revenue = 0
        total_market_revenue = 0

        # Get date filters
        booking_date_gte = request.query_params.get('booking_date__gte')
        booking_date_lte = request.query_params.get('booking_date__lte')

        # Determine home country for domestic/international classification
        from apps.reference_data.models import Country
        home_country = request.user.organization.home_country if request.user.organization else 'AUS'
        home_country_obj = Country.objects.filter(alpha_3=home_country).first()

        if home_country_obj:
            domestic_airports = list(Airport.objects.filter(
                country=home_country_obj.name
            ).values_list('iata_code', flat=True))
        else:
            domestic_airports = []

        # Calculate market totals by market type (DOMESTIC/INTERNATIONAL)
        market_totals = {'DOMESTIC': 0, 'INTERNATIONAL': 0}

        # Get all air bookings for the organization in the date range
        all_air_bookings_qs = AirBooking.objects.filter(
            booking__organization_id=organization_id
        )

        if booking_date_gte:
            all_air_bookings_qs = all_air_bookings_qs.filter(booking__booking_date__gte=booking_date_gte)
        if booking_date_lte:
            all_air_bookings_qs = all_air_bookings_qs.filter(booking__booking_date__lte=booking_date_lte)

        # Calculate total revenue by market type
        for ab in all_air_bookings_qs.prefetch_related('segments'):
            # Determine if domestic or international
            is_domestic = True
            if domestic_airports:
                for segment in ab.segments.all():
                    if segment.origin_airport_iata_code not in domestic_airports or \
                       segment.destination_airport_iata_code not in domestic_airports:
                        is_domestic = False
                        break

            market_type = 'DOMESTIC' if is_domestic else 'INTERNATIONAL'
            market_totals[market_type] += float(ab.total_fare or 0)

        # Process each preferred airline
        for pa in preferred_airlines:
            # Get actual bookings for this preferred airline
            air_bookings_qs = AirBooking.objects.filter(
                booking__organization_id=organization_id,
                primary_airline_iata_code=pa.airline_iata_code
            )

            if booking_date_gte:
                air_bookings_qs = air_bookings_qs.filter(booking__booking_date__gte=booking_date_gte)
            if booking_date_lte:
                air_bookings_qs = air_bookings_qs.filter(booking__booking_date__lte=booking_date_lte)

            # Filter by market type
            matching_bookings = []
            if domestic_airports:
                for ab in air_bookings_qs.prefetch_related('segments'):
                    # Determine if domestic or international
                    is_domestic = True
                    for segment in ab.segments.all():
                        if segment.origin_airport_iata_code not in domestic_airports or \
                           segment.destination_airport_iata_code not in domestic_airports:
                            is_domestic = False
                            break

                    market_type = 'DOMESTIC' if is_domestic else 'INTERNATIONAL'
                    if market_type == pa.market_type:
                        matching_bookings.append(ab)
            else:
                matching_bookings = list(air_bookings_qs)

            # Calculate actual metrics
            actual_revenue = sum(float(ab.total_fare or 0) for ab in matching_bookings)

            # Calculate actual market share
            market_total = market_totals.get(pa.market_type, 0)
            actual_market_share = (actual_revenue / market_total * 100) if market_total > 0 else 0

            # Add to totals
            if pa.target_revenue:
                total_target_revenue += float(pa.target_revenue)
            total_actual_preferred_revenue += actual_revenue
            total_market_revenue += market_total

            # Calculate variances
            market_share_variance = actual_market_share - float(pa.target_market_share)
            revenue_variance = None
            performance_status = 'MEETING'

            # Determine performance status based on market share
            if actual_market_share >= float(pa.target_market_share):
                performance_status = 'EXCEEDING'
            elif actual_market_share >= float(pa.target_market_share) * 0.9:
                performance_status = 'MEETING'
            else:
                performance_status = 'BELOW_TARGET'

            # Also check revenue target if specified
            if pa.target_revenue:
                revenue_variance = actual_revenue - float(pa.target_revenue)
                if actual_revenue < float(pa.target_revenue) * 0.9:
                    performance_status = 'BELOW_TARGET'

            results.append({
                'airline': pa.airline_name,
                'airline_code': pa.airline_iata_code,
                'market_type': pa.market_type,
                'market_type_display': pa.get_market_type_display(),
                'target_market_share': float(pa.target_market_share),
                'actual_market_share': round(actual_market_share, 2),
                'market_share_variance': round(market_share_variance, 2),
                'target_revenue': float(pa.target_revenue) if pa.target_revenue else None,
                'actual_revenue': round(actual_revenue, 2),
                'revenue_variance': round(revenue_variance, 2) if revenue_variance is not None else None,
                'performance_status': performance_status
            })

        # Calculate overall market share
        overall_actual_market_share = (total_actual_preferred_revenue / sum(market_totals.values()) * 100) if sum(market_totals.values()) > 0 else 0

        return Response({
            'contracts': sorted(results, key=lambda x: x.get('actual_revenue', 0), reverse=True),
            'totals': {
                'target_revenue': round(total_target_revenue, 2),
                'actual_revenue': round(total_actual_preferred_revenue, 2),
                'revenue_variance': round(total_actual_preferred_revenue - total_target_revenue, 2),
                'actual_market_share': round(overall_actual_market_share, 2),
                'total_market_revenue': round(sum(market_totals.values()), 2)
            }
        })


# ============================================================================
# PREFERRED HOTEL VIEWSET
# ============================================================================

class PreferredHotelViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing preferred hotel contracts.

    Supports:
    - List all preferred hotels for accessible organizations
    - Retrieve specific preferred hotel details
    - Create new preferred hotel contracts
    - Update existing contracts
    - Delete contracts
    - Filter by organization, market_type, hotel_chain, contract status

    Query parameters:
    - organization: Filter by organization ID
    - market_type: Filter by DOMESTIC or INTERNATIONAL
    - hotel_chain: Filter by hotel chain name
    - location_city: Filter by city
    - is_active: Filter by active status (true/false)
    - contract_status: Filter by ACTIVE, EXPIRED, FUTURE, INACTIVE
    """
    serializer_class = PreferredHotelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'market_type', 'hotel_chain', 'location_city', 'location_country', 'is_active']
    search_fields = ['hotel_chain', 'location_city', 'location_country', 'notes']
    ordering_fields = ['hotel_chain', 'priority', 'contract_start_date', 'contract_end_date', 'target_room_nights', 'target_revenue', 'created_at']
    ordering = ['organization', 'market_type', 'priority', 'hotel_chain']

    def get_queryset(self):
        """
        Filter preferred hotels based on user's organization access.
        Only show hotels for organizations the user has access to.
        """
        user = self.request.user

        if user.user_type == 'ADMIN':
            queryset = PreferredHotel.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            # Travel agents see preferred hotels for their customer organizations
            if user.organization:
                queryset = PreferredHotel.objects.filter(
                    Q(organization=user.organization) |
                    Q(organization__travel_agent=user.organization)
                )
            else:
                queryset = PreferredHotel.objects.all()
        else:
            # Customer users see only their organization's preferred hotels
            if user.organization:
                queryset = PreferredHotel.objects.filter(organization=user.organization)
            else:
                queryset = PreferredHotel.objects.none()

        # Filter by contract_status if provided (custom filter)
        contract_status = self.request.query_params.get('contract_status', None)
        if contract_status:
            from django.utils import timezone
            today = timezone.now().date()

            if contract_status == 'ACTIVE':
                queryset = queryset.filter(
                    is_active=True,
                    contract_start_date__lte=today,
                    contract_end_date__gte=today
                )
            elif contract_status == 'EXPIRED':
                queryset = queryset.filter(
                    is_active=True,
                    contract_end_date__lt=today
                )
            elif contract_status == 'FUTURE':
                queryset = queryset.filter(
                    is_active=True,
                    contract_start_date__gt=today
                )
            elif contract_status == 'INACTIVE':
                queryset = queryset.filter(is_active=False)

        return queryset.select_related('organization', 'hotel', 'created_by')

    def perform_create(self, serializer):
        """Set created_by to current user when creating a new preferred hotel"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def active_contracts(self, request):
        """
        Get all currently active preferred hotel contracts.
        A contract is active if:
        - is_active = True
        - current date is between contract_start_date and contract_end_date

        Query params supported:
        - organization: Filter by organization ID
        - market_type: Filter by DOMESTIC or INTERNATIONAL
        """
        from django.utils import timezone
        today = timezone.now().date()

        queryset = self.filter_queryset(self.get_queryset())

        # Filter for currently active contracts
        queryset = queryset.filter(
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """
        Get preferred hotel contracts expiring within the next N days.

        Query params:
        - days: Number of days to look ahead (default: 30)
        - organization: Filter by organization ID
        """
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        days_ahead = int(request.query_params.get('days', 30))
        expiry_threshold = today + timedelta(days=days_ahead)

        queryset = self.filter_queryset(self.get_queryset())

        # Filter for contracts expiring soon
        queryset = queryset.filter(
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today,
            contract_end_date__lte=expiry_threshold
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a preferred hotel contract.
        Sets is_active to False.
        """
        preferred_hotel = self.get_object()
        preferred_hotel.is_active = False
        preferred_hotel.save()

        serializer = self.get_serializer(preferred_hotel)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a preferred hotel contract.
        Sets is_active to True.
        """
        preferred_hotel = self.get_object()
        preferred_hotel.is_active = True
        preferred_hotel.save()

        serializer = self.get_serializer(preferred_hotel)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def compliance_report(self, request):
        """
        Calculate preferred hotel compliance metrics.

        Returns room nights and spending broken down by:
        - Overall compliance rate
        - Compliance by cost center
        - Non-compliant bookings (off-preferred hotels)

        Query params:
        - organization: Filter by organization ID (required)
        - booking_date__gte: Start date for bookings (optional)
        - booking_date__lte: End date for bookings (optional)
        - market_type: Filter by DOMESTIC or INTERNATIONAL (optional)

        Returns:
        {
            "summary": {
                "total_spend": 500000,
                "preferred_spend": 425000,
                "non_preferred_spend": 75000,
                "compliance_rate": 85.0,
                "total_room_nights": 1000,
                "preferred_room_nights": 850,
                "non_preferred_room_nights": 150
            },
            "by_cost_center": [...],
            "non_compliant_bookings": [...]
        }
        """
        from django.utils import timezone
        from collections import defaultdict

        # Get organization from query params
        organization_id = request.query_params.get('organization')
        if not organization_id:
            return Response(
                {'error': 'organization parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get date range filters
        booking_date_gte = request.query_params.get('booking_date__gte')
        booking_date_lte = request.query_params.get('booking_date__lte')
        market_type_filter = request.query_params.get('market_type')

        # Get active preferred hotel contracts for this organization
        today = timezone.now().date()
        preferred_hotels = PreferredHotel.objects.filter(
            organization_id=organization_id,
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today
        )

        # Build a lookup for preferred hotels
        preferred_chains = set()
        preferred_by_location = {}  # {chain: {city: True}}
        preferred_locations = set()  # Track all cities/countries with preferred hotels
        has_chain_wide_contracts = False  # Track if there are any chain-wide contracts

        for ph in preferred_hotels:
            preferred_chains.add(ph.hotel_chain.lower())
            if ph.location_city:
                if ph.hotel_chain.lower() not in preferred_by_location:
                    preferred_by_location[ph.hotel_chain.lower()] = set()
                preferred_by_location[ph.hotel_chain.lower()].add(ph.location_city.lower())
                preferred_locations.add(ph.location_city.lower())
            elif ph.location_country:
                preferred_locations.add(ph.location_country.lower())
            else:
                # Chain-wide contract (no location restriction)
                has_chain_wide_contracts = True

        # Get all bookings for the organization with filters
        bookings_qs = Booking.objects.filter(organization_id=organization_id)

        if booking_date_gte:
            bookings_qs = bookings_qs.filter(booking_date__gte=booking_date_gte)
        if booking_date_lte:
            bookings_qs = bookings_qs.filter(booking_date__lte=booking_date_lte)

        bookings = bookings_qs.select_related('traveller', 'organization').prefetch_related(
            'accommodation_bookings__hotel'
        )

        # Initialize aggregations
        summary = {
            'total_spend': 0,
            'preferred_spend': 0,
            'non_preferred_spend': 0,
            'total_room_nights': 0,
            'preferred_room_nights': 0,
            'non_preferred_room_nights': 0
        }

        cost_center_data = defaultdict(lambda: {
            'cost_center': '',
            'cost_center_name': '',
            'total_spend': 0,
            'preferred_spend': 0,
            'non_preferred_spend': 0,
            'total_room_nights': 0,
            'preferred_room_nights': 0,
            'non_preferred_room_nights': 0,
            'compliance_rate': 0
        })

        traveller_data = defaultdict(lambda: {
            'traveller_id': '',
            'traveller_name': '',
            'cost_center': '',
            'total_spend': 0,
            'preferred_spend': 0,
            'non_preferred_spend': 0,
            'total_room_nights': 0,
            'preferred_room_nights': 0,
            'non_preferred_room_nights': 0,
            'compliance_rate': 0
        })

        non_compliant_bookings = []

        # Helper function to determine market type
        def get_accommodation_market_type(accom_booking):
            """Determine if accommodation is DOMESTIC or INTERNATIONAL"""
            home_country = accom_booking.booking.organization.home_country or 'AUS'

            # Get country from hotel or fall back to booking country
            if accom_booking.hotel and accom_booking.hotel.country:
                hotel_country_name = accom_booking.hotel.country
            else:
                hotel_country_name = accom_booking.country

            if not hotel_country_name:
                return 'INTERNATIONAL'

            # Get home country object
            home_country_obj = Country.objects.filter(alpha_3=home_country).first()
            if not home_country_obj:
                return 'INTERNATIONAL'

            return 'DOMESTIC' if hotel_country_name.lower() == home_country_obj.name.lower() else 'INTERNATIONAL'

        # Helper function to check if we have preferred hotels in this location
        def has_preferred_hotel_in_location(accom_booking):
            """Check if there's any preferred hotel contract for this location"""
            city = accom_booking.city or ''
            country = accom_booking.country or ''

            # If we have chain-wide contracts, all locations are covered
            if has_chain_wide_contracts:
                return True

            # Check if this specific city or country has a preferred hotel
            city_lower = city.lower()
            country_lower = country.lower()

            return city_lower in preferred_locations or country_lower in preferred_locations

        # Helper function to check if booking is on preferred hotel
        def is_preferred_hotel(accom_booking):
            """Check if accommodation booking is on a preferred hotel"""
            hotel_chain = accom_booking.hotel_chain or ''
            city = accom_booking.city or ''

            if not hotel_chain:
                return False

            # Check if chain is preferred
            chain_lower = hotel_chain.lower()
            if chain_lower not in preferred_chains:
                return False

            # If location-specific contract exists, check location match
            if chain_lower in preferred_by_location:
                city_lower = city.lower()
                return city_lower in preferred_by_location[chain_lower]

            # Chain-wide contract (no location restriction)
            return True

        # Process each booking
        for booking in bookings:
            if not booking.accommodation_bookings.exists():
                continue  # Skip non-accommodation bookings

            cost_center = booking.traveller.cost_center if booking.traveller and booking.traveller.cost_center else 'Unassigned'

            # Process accommodation bookings
            for accom_booking in booking.accommodation_bookings.all():
                # Determine market type
                market_type = get_accommodation_market_type(accom_booking)

                # Skip if filtered by market type
                if market_type_filter and market_type != market_type_filter:
                    continue

                # ONLY track compliance if we have a preferred hotel contract for this location
                if not has_preferred_hotel_in_location(accom_booking):
                    continue  # Skip - no preferred hotel available in this location

                # Calculate spend including transactions
                spend = float(accom_booking.total_amount_base or 0)

                # Add transaction amounts
                from django.contrib.contenttypes.models import ContentType
                accom_ct = ContentType.objects.get_for_model(AccommodationBooking)
                transactions = BookingTransaction.objects.filter(
                    content_type=accom_ct,
                    object_id=accom_booking.id,
                    status__in=['CONFIRMED', 'PENDING']
                )
                for trans in transactions:
                    spend += float(trans.total_amount_base or trans.total_amount or 0)

                room_nights = accom_booking.number_of_nights or 0

                # Update summary
                summary['total_spend'] += spend
                summary['total_room_nights'] += room_nights

                # Update cost center data
                cc_key = cost_center
                cost_center_data[cc_key]['cost_center'] = cost_center
                cost_center_data[cc_key]['cost_center_name'] = cost_center
                cost_center_data[cc_key]['total_spend'] += spend
                cost_center_data[cc_key]['total_room_nights'] += room_nights

                # Update traveller data
                traveller_id = str(booking.traveller.id) if booking.traveller else 'Unknown'
                traveller_name = str(booking.traveller) if booking.traveller else 'Unknown'
                traveller_key = traveller_id
                traveller_data[traveller_key]['traveller_id'] = traveller_id
                traveller_data[traveller_key]['traveller_name'] = traveller_name
                traveller_data[traveller_key]['cost_center'] = cost_center
                traveller_data[traveller_key]['total_spend'] += spend
                traveller_data[traveller_key]['total_room_nights'] += room_nights

                # Check if preferred
                if is_preferred_hotel(accom_booking):
                    summary['preferred_spend'] += spend
                    summary['preferred_room_nights'] += room_nights
                    cost_center_data[cc_key]['preferred_spend'] += spend
                    cost_center_data[cc_key]['preferred_room_nights'] += room_nights
                    traveller_data[traveller_key]['preferred_spend'] += spend
                    traveller_data[traveller_key]['preferred_room_nights'] += room_nights
                else:
                    summary['non_preferred_spend'] += spend
                    summary['non_preferred_room_nights'] += room_nights
                    cost_center_data[cc_key]['non_preferred_spend'] += spend
                    cost_center_data[cc_key]['non_preferred_room_nights'] += room_nights
                    traveller_data[traveller_key]['non_preferred_spend'] += spend
                    traveller_data[traveller_key]['non_preferred_room_nights'] += room_nights

                    # Track non-compliant booking
                    non_compliant_bookings.append({
                        'booking_reference': booking.agent_booking_reference,
                        'traveller_name': str(booking.traveller) if booking.traveller else 'Unknown',
                        'cost_center': cost_center,
                        'hotel_chain': accom_booking.hotel_chain or 'Unknown',
                        'hotel_name': accom_booking.hotel_name or 'Unknown',
                        'city': accom_booking.city or 'Unknown',
                        'checkin_date': str(accom_booking.check_in_date),
                        'room_nights': room_nights,
                        'spend': round(spend, 2),
                        'market_type': market_type
                    })

        # Calculate compliance rates
        if summary['total_spend'] > 0:
            summary['compliance_rate'] = round((summary['preferred_spend'] / summary['total_spend']) * 100, 2)
        else:
            summary['compliance_rate'] = 0

        # Calculate cost center compliance rates
        for cc_data in cost_center_data.values():
            if cc_data['total_spend'] > 0:
                cc_data['compliance_rate'] = round((cc_data['preferred_spend'] / cc_data['total_spend']) * 100, 2)
            else:
                cc_data['compliance_rate'] = 0

        # Calculate traveller compliance rates
        for t_data in traveller_data.values():
            if t_data['total_spend'] > 0:
                t_data['compliance_rate'] = round((t_data['preferred_spend'] / t_data['total_spend']) * 100, 2)
            else:
                t_data['compliance_rate'] = 0

        # Format response
        return Response({
            'summary': {
                'total_spend': round(summary['total_spend'], 2),
                'preferred_spend': round(summary['preferred_spend'], 2),
                'non_preferred_spend': round(summary['non_preferred_spend'], 2),
                'compliance_rate': summary['compliance_rate'],
                'total_room_nights': summary['total_room_nights'],
                'preferred_room_nights': summary['preferred_room_nights'],
                'non_preferred_room_nights': summary['non_preferred_room_nights']
            },
            'by_cost_center': sorted(
                [dict(cc_data) for cc_data in cost_center_data.values()],
                key=lambda x: x['total_spend'],
                reverse=True
            ),
            'by_traveller': sorted(
                [dict(t_data) for t_data in traveller_data.values()],
                key=lambda x: x['total_spend'],
                reverse=True
            ),
            'non_compliant_bookings': sorted(
                non_compliant_bookings,
                key=lambda x: x['spend'],
                reverse=True
            )[:50]  # Limit to top 50
        })

    @action(detail=False, methods=['get'])
    def performance_dashboard(self, request):
        """
        Calculate performance metrics for preferred hotels.

        Query params:
        - organization: Filter by organization ID (required)
        - booking_date__gte: Start date (optional)
        - booking_date__lte: End date (optional)

        Returns performance data showing actual vs target metrics.
        """
        from django.utils import timezone
        from collections import defaultdict

        # Get organization from query params
        organization_id = request.query_params.get('organization')
        if not organization_id:
            return Response(
                {'error': 'organization parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get active preferred hotels for this organization
        today = timezone.now().date()
        preferred_hotels = PreferredHotel.objects.filter(
            organization_id=organization_id,
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today
        )

        results = []
        total_target_revenue = 0
        total_actual_revenue = 0
        total_target_room_nights = 0
        total_actual_room_nights = 0

        for ph in preferred_hotels:
            # Get actual bookings for this hotel
            booking_date_gte = request.query_params.get('booking_date__gte')
            booking_date_lte = request.query_params.get('booking_date__lte')

            accom_qs = AccommodationBooking.objects.filter(
                booking__organization_id=organization_id,
                hotel_chain=ph.hotel_chain
            )

            # Apply location filters if contract is location-specific
            if ph.location_city:
                accom_qs = accom_qs.filter(city=ph.location_city)

            if booking_date_gte:
                accom_qs = accom_qs.filter(booking__booking_date__gte=booking_date_gte)
            if booking_date_lte:
                accom_qs = accom_qs.filter(booking__booking_date__lte=booking_date_lte)

            # Calculate actual metrics
            actual_room_nights = sum(a.number_of_nights or 0 for a in accom_qs)
            actual_revenue = sum(float(a.total_amount_base or 0) for a in accom_qs)

            # Add to totals
            if ph.target_revenue:
                total_target_revenue += float(ph.target_revenue)
            total_actual_revenue += actual_revenue

            if ph.target_room_nights:
                total_target_room_nights += ph.target_room_nights
            total_actual_room_nights += actual_room_nights

            # Calculate variances
            room_nights_variance = None
            revenue_variance = None
            performance_status = 'ON_TARGET'

            if ph.target_room_nights:
                room_nights_variance = actual_room_nights - ph.target_room_nights
                if actual_room_nights < ph.target_room_nights * 0.9:
                    performance_status = 'BELOW_TARGET'
                elif actual_room_nights >= ph.target_room_nights:
                    performance_status = 'ABOVE_TARGET'

            if ph.target_revenue:
                revenue_variance = actual_revenue - float(ph.target_revenue)
                if actual_revenue < float(ph.target_revenue) * 0.9:
                    performance_status = 'BELOW_TARGET'
                elif actual_revenue >= float(ph.target_revenue):
                    performance_status = 'ABOVE_TARGET'

            results.append({
                'hotel_chain': ph.hotel_chain,
                'location': ph.location_city or ph.location_country or 'All Locations',
                'market_type': ph.market_type,
                'priority': ph.priority,
                'target_room_nights': ph.target_room_nights,
                'actual_room_nights': actual_room_nights,
                'room_nights_variance': room_nights_variance,
                'target_revenue': float(ph.target_revenue) if ph.target_revenue else None,
                'actual_revenue': round(actual_revenue, 2),
                'revenue_variance': round(revenue_variance, 2) if revenue_variance is not None else None,
                'performance_status': performance_status
            })

        return Response({
            'contracts': sorted(results, key=lambda x: x.get('actual_revenue', 0), reverse=True),
            'totals': {
                'target_revenue': round(total_target_revenue, 2),
                'actual_revenue': round(total_actual_revenue, 2),
                'revenue_variance': round(total_actual_revenue - total_target_revenue, 2),
                'target_room_nights': total_target_room_nights,
                'actual_room_nights': total_actual_room_nights,
                'room_nights_variance': total_actual_room_nights - total_target_room_nights
            }
        })


# ============================================================================
# PREFERRED CAR HIRE VIEWSET
# ============================================================================

class PreferredCarHireViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing preferred car hire contracts.

    Supports:
    - List all preferred car hire contracts for accessible organizations
    - Retrieve specific preferred car hire details
    - Create new preferred car hire contracts
    - Update existing contracts
    - Delete contracts
    - Filter by organization, market, supplier, contract status

    Query parameters:
    - organization: Filter by organization ID
    - market: Filter by market (AUSTRALIA, NEW_ZEALAND, USA, UK, CANADA, OTHER)
    - supplier: Filter by supplier name
    - car_category: Filter by car category
    - is_active: Filter by active status (true/false)
    - contract_status: Filter by ACTIVE, EXPIRED, FUTURE, INACTIVE
    """
    serializer_class = PreferredCarHireSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'market', 'supplier', 'car_category', 'is_active']
    search_fields = ['supplier', 'notes']
    ordering_fields = ['supplier', 'market', 'priority', 'contract_start_date', 'contract_end_date', 'target_rental_days', 'target_revenue', 'created_at']
    ordering = ['organization', 'market', 'priority', 'supplier']

    def get_queryset(self):
        """
        Filter preferred car hire contracts based on user's organization access.
        Only show contracts for organizations the user has access to.
        """
        user = self.request.user

        if user.user_type == 'ADMIN':
            queryset = PreferredCarHire.objects.all()
        elif user.user_type in ['AGENT_ADMIN', 'AGENT_USER']:
            # Travel agents see preferred car hire contracts for their customer organizations
            if user.organization:
                queryset = PreferredCarHire.objects.filter(
                    Q(organization=user.organization) |
                    Q(organization__travel_agent=user.organization)
                )
            else:
                queryset = PreferredCarHire.objects.all()
        else:
            # Customer users see only their organization's preferred car hire contracts
            if user.organization:
                queryset = PreferredCarHire.objects.filter(organization=user.organization)
            else:
                queryset = PreferredCarHire.objects.none()

        # Filter by contract_status if provided (custom filter)
        contract_status = self.request.query_params.get('contract_status', None)
        if contract_status:
            from django.utils import timezone
            today = timezone.now().date()

            if contract_status == 'ACTIVE':
                queryset = queryset.filter(
                    is_active=True,
                    contract_start_date__lte=today,
                    contract_end_date__gte=today
                )
            elif contract_status == 'EXPIRED':
                queryset = queryset.filter(
                    is_active=True,
                    contract_end_date__lt=today
                )
            elif contract_status == 'FUTURE':
                queryset = queryset.filter(
                    is_active=True,
                    contract_start_date__gt=today
                )
            elif contract_status == 'INACTIVE':
                queryset = queryset.filter(is_active=False)

        return queryset.select_related('organization', 'created_by')

    def perform_create(self, serializer):
        """Set created_by to current user when creating a new preferred car hire contract"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def active_contracts(self, request):
        """
        Get all currently active preferred car hire contracts.
        A contract is active if:
        - is_active = True
        - current date is between contract_start_date and contract_end_date

        Query params supported:
        - organization: Filter by organization ID
        - market: Filter by market
        """
        from django.utils import timezone
        today = timezone.now().date()

        queryset = self.filter_queryset(self.get_queryset())

        # Filter for currently active contracts
        queryset = queryset.filter(
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """
        Get preferred car hire contracts expiring within the next N days.

        Query params:
        - days: Number of days to look ahead (default: 30)
        - organization: Filter by organization ID
        """
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        days_ahead = int(request.query_params.get('days', 30))
        expiry_threshold = today + timedelta(days=days_ahead)

        queryset = self.filter_queryset(self.get_queryset())

        # Filter for contracts expiring soon
        queryset = queryset.filter(
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today,
            contract_end_date__lte=expiry_threshold
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a preferred car hire contract.
        Sets is_active to False.
        """
        preferred_car_hire = self.get_object()
        preferred_car_hire.is_active = False
        preferred_car_hire.save()

        serializer = self.get_serializer(preferred_car_hire)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a preferred car hire contract.
        Sets is_active to True.
        """
        preferred_car_hire = self.get_object()
        preferred_car_hire.is_active = True
        preferred_car_hire.save()

        serializer = self.get_serializer(preferred_car_hire)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def compliance_report(self, request):
        """
        Calculate preferred car hire compliance metrics.

        Returns rental days and spending broken down by:
        - Overall compliance rate
        - Compliance by cost center
        - Compliance by traveller
        - Non-compliant bookings (off-preferred suppliers)

        Query params:
        - organization: Filter by organization ID (required)
        - booking_date__gte: Start date for bookings (optional)
        - booking_date__lte: End date for bookings (optional)
        - market: Filter by market (optional)

        Returns:
        {
            "summary": {
                "total_spend": 500000,
                "preferred_spend": 425000,
                "non_preferred_spend": 75000,
                "compliance_rate": 85.0,
                "total_rental_days": 1000,
                "preferred_rental_days": 850,
                "non_preferred_rental_days": 150
            },
            "by_cost_center": [...],
            "by_traveller": [...],
            "non_compliant_bookings": [...]
        }
        """
        from django.utils import timezone
        from collections import defaultdict

        # Get organization from query params
        organization_id = request.query_params.get('organization')
        if not organization_id:
            return Response(
                {'error': 'organization parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get date range filters
        booking_date_gte = request.query_params.get('booking_date__gte')
        booking_date_lte = request.query_params.get('booking_date__lte')
        market_filter = request.query_params.get('market')

        # Get active preferred car hire contracts for this organization
        today = timezone.now().date()
        preferred_car_hires = PreferredCarHire.objects.filter(
            organization_id=organization_id,
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today
        )

        # Build a lookup for preferred suppliers by market
        preferred_by_market = defaultdict(set)  # {market: {supplier1, supplier2}}
        markets_with_contracts = set()  # Track which markets have preferred contracts

        for pch in preferred_car_hires:
            # Add main supplier
            preferred_by_market[pch.market].add(pch.supplier.lower())
            markets_with_contracts.add(pch.market)

            # Add related brands if specified
            if pch.related_brands:
                related = [brand.strip().lower() for brand in pch.related_brands.split(',') if brand.strip()]
                for brand in related:
                    preferred_by_market[pch.market].add(brand)

        # Get all bookings for the organization with filters
        bookings_qs = Booking.objects.filter(organization_id=organization_id)

        if booking_date_gte:
            bookings_qs = bookings_qs.filter(booking_date__gte=booking_date_gte)
        if booking_date_lte:
            bookings_qs = bookings_qs.filter(booking_date__lte=booking_date_lte)

        bookings = bookings_qs.select_related('traveller', 'organization').prefetch_related(
            'car_hire_bookings'
        )

        # Initialize aggregations
        summary = {
            'total_spend': 0,
            'preferred_spend': 0,
            'non_preferred_spend': 0,
            'total_rental_days': 0,
            'preferred_rental_days': 0,
            'non_preferred_rental_days': 0
        }

        cost_center_data = defaultdict(lambda: {
            'cost_center': '',
            'cost_center_name': '',
            'total_spend': 0,
            'preferred_spend': 0,
            'non_preferred_spend': 0,
            'total_rental_days': 0,
            'preferred_rental_days': 0,
            'non_preferred_rental_days': 0,
            'compliance_rate': 0
        })

        traveller_data = defaultdict(lambda: {
            'traveller_id': '',
            'traveller_name': '',
            'cost_center': '',
            'total_spend': 0,
            'preferred_spend': 0,
            'non_preferred_spend': 0,
            'total_rental_days': 0,
            'preferred_rental_days': 0,
            'non_preferred_rental_days': 0,
            'compliance_rate': 0
        })

        non_compliant_bookings = []

        # Helper function to determine market from car hire booking
        def get_car_hire_market(car_hire_booking):
            """Determine market from car hire location"""
            # Get country from the booking
            country = car_hire_booking.country or ''

            # Map countries to markets
            if not country:
                return 'OTHER'

            country_upper = country.upper()

            # Try to match by country name or code
            if 'AUSTRALIA' in country_upper or country_upper in ['AU', 'AUS']:
                return 'AUSTRALIA'
            elif 'NEW ZEALAND' in country_upper or country_upper in ['NZ', 'NZL']:
                return 'NEW_ZEALAND'
            elif 'UNITED STATES' in country_upper or 'USA' in country_upper or country_upper in ['US', 'USA']:
                return 'USA'
            elif 'UNITED KINGDOM' in country_upper or country_upper in ['GB', 'GBR', 'UK']:
                return 'UK'
            elif 'CANADA' in country_upper or country_upper in ['CA', 'CAN']:
                return 'CANADA'
            else:
                return 'OTHER'

        # Helper function to check if we have preferred suppliers in this market
        def has_preferred_in_market(market):
            """Check if there's any preferred supplier contract for this market"""
            return market in markets_with_contracts

        # Helper function to check if booking is on preferred supplier
        def is_preferred_supplier(car_hire_booking, market):
            """Check if car hire booking is on a preferred supplier"""
            rental_company = car_hire_booking.rental_company or ''

            if not rental_company or market not in preferred_by_market:
                return False

            rental_company_lower = rental_company.lower()
            return rental_company_lower in preferred_by_market[market]

        # Process each booking
        for booking in bookings:
            if not booking.car_hire_bookings.exists():
                continue  # Skip non-car-hire bookings

            cost_center = booking.traveller.cost_center if booking.traveller and booking.traveller.cost_center else 'Unassigned'

            # Process car hire bookings
            for car_hire_booking in booking.car_hire_bookings.all():
                # Determine market
                market = get_car_hire_market(car_hire_booking)

                # Skip if filtered by market
                if market_filter and market != market_filter:
                    continue

                # ONLY track compliance if we have a preferred supplier contract for this market
                if not has_preferred_in_market(market):
                    continue  # Skip - no preferred supplier available in this market

                # Calculate spend including transactions
                spend = float(car_hire_booking.total_amount_base or 0)

                # Add transaction amounts
                from django.contrib.contenttypes.models import ContentType
                car_hire_ct = ContentType.objects.get_for_model(CarHireBooking)
                transactions = BookingTransaction.objects.filter(
                    content_type=car_hire_ct,
                    object_id=car_hire_booking.id,
                    status__in=['CONFIRMED', 'PENDING']
                )
                for trans in transactions:
                    spend += float(trans.total_amount_base or trans.total_amount or 0)

                rental_days = car_hire_booking.number_of_days or 0

                # Update summary
                summary['total_spend'] += spend
                summary['total_rental_days'] += rental_days

                # Update cost center data
                cc_key = cost_center
                cost_center_data[cc_key]['cost_center'] = cost_center
                cost_center_data[cc_key]['cost_center_name'] = cost_center
                cost_center_data[cc_key]['total_spend'] += spend
                cost_center_data[cc_key]['total_rental_days'] += rental_days

                # Update traveller data
                traveller_id = str(booking.traveller.id) if booking.traveller else 'Unknown'
                traveller_name = str(booking.traveller) if booking.traveller else 'Unknown'
                traveller_key = traveller_id
                traveller_data[traveller_key]['traveller_id'] = traveller_id
                traveller_data[traveller_key]['traveller_name'] = traveller_name
                traveller_data[traveller_key]['cost_center'] = cost_center
                traveller_data[traveller_key]['total_spend'] += spend
                traveller_data[traveller_key]['total_rental_days'] += rental_days

                # Check if preferred
                if is_preferred_supplier(car_hire_booking, market):
                    summary['preferred_spend'] += spend
                    summary['preferred_rental_days'] += rental_days
                    cost_center_data[cc_key]['preferred_spend'] += spend
                    cost_center_data[cc_key]['preferred_rental_days'] += rental_days
                    traveller_data[traveller_key]['preferred_spend'] += spend
                    traveller_data[traveller_key]['preferred_rental_days'] += rental_days
                else:
                    summary['non_preferred_spend'] += spend
                    summary['non_preferred_rental_days'] += rental_days
                    cost_center_data[cc_key]['non_preferred_spend'] += spend
                    cost_center_data[cc_key]['non_preferred_rental_days'] += rental_days
                    traveller_data[traveller_key]['non_preferred_spend'] += spend
                    traveller_data[traveller_key]['non_preferred_rental_days'] += rental_days

                    # Track non-compliant booking
                    non_compliant_bookings.append({
                        'booking_reference': booking.agent_booking_reference,
                        'traveller_name': str(booking.traveller) if booking.traveller else 'Unknown',
                        'cost_center': cost_center,
                        'supplier': car_hire_booking.rental_company or 'Unknown',
                        'car_category': car_hire_booking.vehicle_category or 'Unknown',
                        'pickup_location': car_hire_booking.pickup_location or 'Unknown',
                        'pickup_date': str(car_hire_booking.pickup_date) if car_hire_booking.pickup_date else 'Unknown',
                        'rental_days': rental_days,
                        'spend': round(spend, 2),
                        'market': market
                    })

        # Calculate compliance rates
        if summary['total_spend'] > 0:
            summary['compliance_rate'] = round((summary['preferred_spend'] / summary['total_spend']) * 100, 2)
        else:
            summary['compliance_rate'] = 0

        # Calculate cost center compliance rates
        for cc_data in cost_center_data.values():
            if cc_data['total_spend'] > 0:
                cc_data['compliance_rate'] = round((cc_data['preferred_spend'] / cc_data['total_spend']) * 100, 2)
            else:
                cc_data['compliance_rate'] = 0

        # Calculate traveller compliance rates
        for t_data in traveller_data.values():
            if t_data['total_spend'] > 0:
                t_data['compliance_rate'] = round((t_data['preferred_spend'] / t_data['total_spend']) * 100, 2)
            else:
                t_data['compliance_rate'] = 0

        # Format response
        return Response({
            'summary': {
                'total_spend': round(summary['total_spend'], 2),
                'preferred_spend': round(summary['preferred_spend'], 2),
                'non_preferred_spend': round(summary['non_preferred_spend'], 2),
                'compliance_rate': summary['compliance_rate'],
                'total_rental_days': summary['total_rental_days'],
                'preferred_rental_days': summary['preferred_rental_days'],
                'non_preferred_rental_days': summary['non_preferred_rental_days']
            },
            'by_cost_center': sorted(
                [dict(cc_data) for cc_data in cost_center_data.values()],
                key=lambda x: x['total_spend'],
                reverse=True
            ),
            'by_traveller': sorted(
                [dict(t_data) for t_data in traveller_data.values()],
                key=lambda x: x['total_spend'],
                reverse=True
            ),
            'non_compliant_bookings': sorted(
                non_compliant_bookings,
                key=lambda x: x['spend'],
                reverse=True
            )[:50]  # Limit to top 50
        })

    @action(detail=False, methods=['get'])
    def performance_dashboard(self, request):
        """
        Calculate performance metrics for preferred car hire contracts.

        Query params:
        - organization: Filter by organization ID (required)
        - booking_date__gte: Start date (optional)
        - booking_date__lte: End date (optional)

        Returns performance data showing actual vs target metrics.
        """
        from django.utils import timezone
        from collections import defaultdict

        # Get organization from query params
        organization_id = request.query_params.get('organization')
        if not organization_id:
            return Response(
                {'error': 'organization parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get active preferred car hire contracts for this organization
        today = timezone.now().date()
        preferred_car_hires = PreferredCarHire.objects.filter(
            organization_id=organization_id,
            is_active=True,
            contract_start_date__lte=today,
            contract_end_date__gte=today
        )

        results = []
        total_target_revenue = 0
        total_actual_revenue = 0
        total_target_rental_days = 0
        total_actual_rental_days = 0

        # Helper function to determine market from car hire booking
        def get_car_hire_market(car_hire_booking):
            """Determine market from car hire location"""
            country = car_hire_booking.country or ''

            if not country:
                return 'OTHER'

            country_upper = country.upper()

            if 'AUSTRALIA' in country_upper or country_upper in ['AU', 'AUS']:
                return 'AUSTRALIA'
            elif 'NEW ZEALAND' in country_upper or country_upper in ['NZ', 'NZL']:
                return 'NEW_ZEALAND'
            elif 'UNITED STATES' in country_upper or 'USA' in country_upper or country_upper in ['US', 'USA']:
                return 'USA'
            elif 'UNITED KINGDOM' in country_upper or country_upper in ['GB', 'GBR', 'UK']:
                return 'UK'
            elif 'CANADA' in country_upper or country_upper in ['CA', 'CAN']:
                return 'CANADA'
            else:
                return 'OTHER'

        for pch in preferred_car_hires:
            # Get actual bookings for this supplier in this market
            booking_date_gte = request.query_params.get('booking_date__gte')
            booking_date_lte = request.query_params.get('booking_date__lte')

            car_hire_qs = CarHireBooking.objects.filter(
                booking__organization_id=organization_id,
                rental_company=pch.supplier
            )

            if booking_date_gte:
                car_hire_qs = car_hire_qs.filter(booking__booking_date__gte=booking_date_gte)
            if booking_date_lte:
                car_hire_qs = car_hire_qs.filter(booking__booking_date__lte=booking_date_lte)

            # Filter by market - need to check country
            market_bookings = []
            for ch in car_hire_qs:
                if get_car_hire_market(ch) == pch.market:
                    market_bookings.append(ch)

            # Calculate actual metrics
            actual_rental_days = sum(ch.number_of_days or 0 for ch in market_bookings)
            actual_revenue = sum(float(ch.total_amount_base or 0) for ch in market_bookings)

            # Add to totals
            if pch.target_revenue:
                total_target_revenue += float(pch.target_revenue)
            total_actual_revenue += actual_revenue

            if pch.target_rental_days:
                total_target_rental_days += pch.target_rental_days
            total_actual_rental_days += actual_rental_days

            # Calculate variances
            rental_days_variance = None
            revenue_variance = None
            performance_status = 'ON_TARGET'

            if pch.target_rental_days:
                rental_days_variance = actual_rental_days - pch.target_rental_days
                if actual_rental_days < pch.target_rental_days * 0.9:
                    performance_status = 'BELOW_TARGET'
                elif actual_rental_days >= pch.target_rental_days:
                    performance_status = 'ABOVE_TARGET'

            if pch.target_revenue:
                revenue_variance = actual_revenue - float(pch.target_revenue)
                if actual_revenue < float(pch.target_revenue) * 0.9:
                    performance_status = 'BELOW_TARGET'
                elif actual_revenue >= float(pch.target_revenue):
                    performance_status = 'ABOVE_TARGET'

            results.append({
                'supplier': pch.supplier,
                'market': pch.market,
                'market_display': pch.get_market_display(),
                'car_category': pch.car_category,
                'car_category_display': pch.get_car_category_display(),
                'priority': pch.priority,
                'target_rental_days': pch.target_rental_days,
                'actual_rental_days': actual_rental_days,
                'rental_days_variance': rental_days_variance,
                'target_revenue': float(pch.target_revenue) if pch.target_revenue else None,
                'actual_revenue': round(actual_revenue, 2),
                'revenue_variance': round(revenue_variance, 2) if revenue_variance is not None else None,
                'performance_status': performance_status
            })

        return Response({
            'contracts': sorted(results, key=lambda x: x.get('actual_revenue', 0), reverse=True),
            'totals': {
                'target_revenue': round(total_target_revenue, 2),
                'actual_revenue': round(total_actual_revenue, 2),
                'revenue_variance': round(total_actual_revenue - total_target_revenue, 2),
                'target_rental_days': total_target_rental_days,
                'actual_rental_days': total_actual_rental_days,
                'rental_days_variance': total_actual_rental_days - total_target_rental_days
            }
        })