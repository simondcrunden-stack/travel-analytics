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
    PreferredAirline
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
    PreferredAirlineSerializer
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
        
        # ========================================================================
        # TRAVELLERS FILTER (Multi-select)
        # ========================================================================
        if travellers:
            traveller_ids = [t.strip() for t in travellers.split(',') if t.strip()]
            if traveller_ids:
                queryset = queryset.filter(traveller_id__in=traveller_ids)
        
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

        total_spend = queryset.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')

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

        # Get all air bookings with destination airports
        air_bookings = AirBooking.objects.filter(
            booking__in=base_queryset
        ).select_related('booking', 'booking__traveller').values(
            'destination_airport_iata_code',
            'booking__traveller__id',
            'booking__total_amount',
            'booking__id'
        )

        # Aggregate by destination
        destination_data = defaultdict(lambda: {
            'trips': 0,
            'travellers': set(),
            'total_spend': 0
        })

        for ab in air_bookings:
            dest = ab['destination_airport_iata_code']
            destination_data[dest]['trips'] += 1
            destination_data[dest]['travellers'].add(ab['booking__traveller__id'])
            destination_data[dest]['total_spend'] += float(ab['booking__total_amount'] or 0)

        # Get airport coordinates for each destination
        result = []
        for dest_code, data in destination_data.items():
            try:
                airport = Airport.objects.get(iata_code=dest_code)
                if airport.latitude and airport.longitude:
                    result.append({
                        'code': dest_code,
                        'name': airport.name,
                        'city': airport.city,
                        'country': airport.country or 'Unknown',
                        'latitude': float(airport.latitude),
                        'longitude': float(airport.longitude),
                        'trips': data['trips'],
                        'travellers': len(data['travellers']),
                        'total_spend': round(data['total_spend'], 2),
                        'avg_spend': round(data['total_spend'] / data['trips'], 2) if data['trips'] > 0 else 0
                    })
            except Airport.DoesNotExist:
                # Skip destinations without airport data
                continue

        # Sort by number of trips (descending)
        result.sort(key=lambda x: x['trips'], reverse=True)

        return Response(result)

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
            'total_carbon_kg': 0,
            'compliance_rate': 0,
            'violation_count': 0,
            'critical_violations': 0,
        }

        bookings = base_queryset.select_related('organization', 'traveller').prefetch_related(
            'air_bookings__segments',
            'accommodation_bookings',
            'car_hire_bookings',
            'violations'
        )

        summary['total_bookings'] = bookings.count()

        # Process each booking
        for booking in bookings:
            # AIR BOOKINGS
            if booking.air_bookings.exists():
                for air in booking.air_bookings.all():
                    # Calculate air spend (original booking amount)
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
                                origin_country = segment.origin_airport.country_code if hasattr(segment.origin_airport, 'country_code') else None
                                dest_country = segment.destination_airport.country_code if hasattr(segment.destination_airport, 'country_code') else None
                                if origin_country != home_country or dest_country != home_country:
                                    all_domestic = False
                                    break
                        is_domestic = all_domestic

                    if is_domestic:
                        summary['air_spend_domestic'] += air_amount
                    else:
                        summary['air_spend_international'] += air_amount

                    # Add carbon emissions
                    summary['total_carbon_kg'] += float(air.total_carbon_kg or 0)

            # ACCOMMODATION BOOKINGS
            if booking.accommodation_bookings.exists():
                for accom in booking.accommodation_bookings.all():
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

            # CAR HIRE BOOKINGS
            if booking.car_hire_bookings.exists():
                for car in booking.car_hire_bookings.all():
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

        # Calculate total spend
        summary['total_spend'] = summary['air_spend'] + summary['accommodation_spend'] + summary['car_hire_spend']
        summary['total_spend_domestic'] = summary['air_spend_domestic'] + summary['accommodation_spend_domestic'] + summary['car_hire_spend_domestic']
        summary['total_spend_international'] = summary['air_spend_international'] + summary['accommodation_spend_international'] + summary['car_hire_spend_international']

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

            # Add air spend (including exchange tickets, refunds, etc.)
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