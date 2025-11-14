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
                    'label': hotel.canonical_name,
                    'subtitle': hotel.hotel_chain if hotel.hotel_chain else None
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