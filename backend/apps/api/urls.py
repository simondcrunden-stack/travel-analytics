from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

# Create router and register viewsets
router = DefaultRouter()

# Core endpoints
router.register(r'organizations', views.OrganizationViewSet, basename='organization')
router.register(r'organizational-nodes', views.OrganizationalNodeViewSet, basename='organizational-node')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'travellers', views.TravellerViewSet, basename='traveller')
router.register(r'bookings', views.BookingViewSet, basename='booking')

# Budget endpoints
router.register(r'fiscal-years', views.FiscalYearViewSet, basename='fiscal-year')
router.register(r'budgets', views.BudgetViewSet, basename='budget')

# Reference data endpoints
router.register(r'airports', views.AirportViewSet, basename='airport')
router.register(r'airlines', views.AirlineViewSet, basename='airline')
router.register(r'countries', views.CountryViewSet, basename='country')

# Commission endpoints
router.register(r'commissions', views.CommissionViewSet, basename='commission')

# Service Fee endpoint
router.register(r'service-fees', views.ServiceFeeViewSet, basename='service-fee')

# Compliance endpoints
router.register(r'compliance-violations', views.ComplianceViolationViewSet, basename='compliance-violation')

urlpatterns = [
    # JWT Authentication endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    path('', include(router.urls)),
]