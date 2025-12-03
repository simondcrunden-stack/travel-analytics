from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import date

from .models import FiscalYear, Budget, BudgetAlert
from apps.organizations.models import Organization, OrganizationalNode
from apps.api.permissions import IsAdminUser


class FiscalYearViewSet(viewsets.ModelViewSet):
    """
    API endpoints for fiscal year management.

    List, create, update, and delete fiscal years for organizations.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter fiscal years by organization based on user permissions"""
        queryset = FiscalYear.objects.all()

        # Filter by organization if specified
        org_id = self.request.query_params.get('organization_id')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        elif self.request.user.user_type != 'ADMIN':
            # Non-admins only see their organization's fiscal years
            if hasattr(self.request.user, 'organization'):
                queryset = queryset.filter(organization=self.request.user.organization)

        return queryset.order_by('-start_date')

    def list(self, request):
        """List all fiscal years"""
        queryset = self.get_queryset()

        results = []
        for fy in queryset:
            results.append({
                'id': str(fy.id),
                'organization': {
                    'id': str(fy.organization.id),
                    'name': fy.organization.name
                },
                'fiscal_year_type': fy.fiscal_year_type,
                'year_label': fy.year_label,
                'start_date': fy.start_date.isoformat(),
                'end_date': fy.end_date.isoformat(),
                'is_current': fy.is_current,
                'is_active': fy.is_active,
                'created_at': fy.created_at.isoformat(),
            })

        return Response({'fiscal_years': results})

    def create(self, request):
        """Create a new fiscal year"""
        org_id = request.data.get('organization_id')
        fiscal_year_type = request.data.get('fiscal_year_type')
        year_label = request.data.get('year_label')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        is_current = request.data.get('is_current', False)

        if not all([org_id, fiscal_year_type, year_label, start_date, end_date]):
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            organization = Organization.objects.get(id=org_id)

            # If setting as current, unset any existing current FY
            if is_current:
                FiscalYear.objects.filter(
                    organization=organization,
                    is_current=True
                ).update(is_current=False)

            fiscal_year = FiscalYear.objects.create(
                organization=organization,
                fiscal_year_type=fiscal_year_type,
                year_label=year_label,
                start_date=start_date,
                end_date=end_date,
                is_current=is_current,
                is_active=True
            )

            return Response({
                'id': str(fiscal_year.id),
                'message': f'Fiscal year {year_label} created successfully'
            }, status=status.HTTP_201_CREATED)

        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BudgetViewSet(viewsets.ModelViewSet):
    """
    API endpoints for budget management.

    List, create, update, and delete budgets for organizational nodes.
    Includes endpoints for budget tracking and status.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter budgets based on user permissions and query parameters"""
        queryset = Budget.objects.select_related(
            'organization', 'fiscal_year', 'organizational_node'
        ).all()

        # Filter by organization
        org_id = self.request.query_params.get('organization_id')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        elif self.request.user.user_type != 'ADMIN':
            if hasattr(self.request.user, 'organization'):
                queryset = queryset.filter(organization=self.request.user.organization)

        # Filter by fiscal year
        fiscal_year_id = self.request.query_params.get('fiscal_year_id')
        if fiscal_year_id:
            queryset = queryset.filter(fiscal_year_id=fiscal_year_id)

        # Filter by organizational node
        node_id = self.request.query_params.get('organizational_node_id')
        if node_id:
            queryset = queryset.filter(organizational_node_id=node_id)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.order_by('-fiscal_year__start_date', 'organizational_node__code')

    def list(self, request):
        """List all budgets with current status"""
        queryset = self.get_queryset()

        results = []
        for budget in queryset:
            # Get current budget status
            try:
                budget_status = budget.get_budget_status()
            except:
                budget_status = {
                    'percentage': 0,
                    'status': 'OK',
                    'spent': Decimal('0.00'),
                    'remaining': budget.total_budget
                }

            results.append({
                'id': str(budget.id),
                'organization': {
                    'id': str(budget.organization.id),
                    'name': budget.organization.name
                },
                'fiscal_year': {
                    'id': str(budget.fiscal_year.id),
                    'year_label': budget.fiscal_year.year_label,
                    'start_date': budget.fiscal_year.start_date.isoformat(),
                    'end_date': budget.fiscal_year.end_date.isoformat(),
                },
                'organizational_node': {
                    'id': str(budget.organizational_node.id),
                    'name': budget.organizational_node.name,
                    'code': budget.organizational_node.code,
                    'node_type': budget.organizational_node.node_type,
                } if budget.organizational_node else None,
                'node_name': budget.node_name,
                'node_code': budget.node_code,
                'total_budget': str(budget.total_budget),
                'air_budget': str(budget.air_budget),
                'accommodation_budget': str(budget.accommodation_budget),
                'car_hire_budget': str(budget.car_hire_budget),
                'other_budget': str(budget.other_budget),
                'currency': budget.currency,
                'carbon_budget': str(budget.carbon_budget),
                'warning_threshold': budget.warning_threshold,
                'critical_threshold': budget.critical_threshold,
                'is_active': budget.is_active,
                'status': budget_status,
                'created_at': budget.created_at.isoformat(),
            })

        return Response({'budgets': results})

    def create(self, request):
        """Create a new budget"""
        org_id = request.data.get('organization_id')
        fiscal_year_id = request.data.get('fiscal_year_id')
        node_id = request.data.get('organizational_node_id')
        total_budget = request.data.get('total_budget')

        if not all([org_id, fiscal_year_id, total_budget]):
            return Response(
                {'error': 'Missing required fields: organization_id, fiscal_year_id, total_budget'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            organization = Organization.objects.get(id=org_id)
            fiscal_year = FiscalYear.objects.get(id=fiscal_year_id)

            budget_data = {
                'organization': organization,
                'fiscal_year': fiscal_year,
                'total_budget': Decimal(str(total_budget)),
                'currency': request.data.get('currency', organization.base_currency),
                'air_budget': Decimal(str(request.data.get('air_budget', 0))),
                'accommodation_budget': Decimal(str(request.data.get('accommodation_budget', 0))),
                'car_hire_budget': Decimal(str(request.data.get('car_hire_budget', 0))),
                'other_budget': Decimal(str(request.data.get('other_budget', 0))),
                'carbon_budget': Decimal(str(request.data.get('carbon_budget', 0))),
                'warning_threshold': request.data.get('warning_threshold', 80),
                'critical_threshold': request.data.get('critical_threshold', 95),
                'notes': request.data.get('notes', ''),
                'is_active': request.data.get('is_active', True),
                'created_by': request.user
            }

            if node_id:
                organizational_node = OrganizationalNode.objects.get(id=node_id)
                budget_data['organizational_node'] = organizational_node

            budget = Budget.objects.create(**budget_data)

            return Response({
                'id': str(budget.id),
                'message': f'Budget created successfully for {budget.node_name}'
            }, status=status.HTTP_201_CREATED)

        except (Organization.DoesNotExist, FiscalYear.DoesNotExist, OrganizationalNode.DoesNotExist) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get detailed budget status including spending breakdown"""
        try:
            budget = self.get_queryset().get(pk=pk)

            # Get overall status
            budget_status = budget.get_budget_status()

            # Get spending by category
            spent_by_category = budget.get_spent_by_category()

            return Response({
                'budget_id': str(budget.id),
                'node_name': budget.node_name,
                'fiscal_year': budget.fiscal_year.year_label,
                'total_budget': str(budget.total_budget),
                'total_spent': str(budget_status['spent']),
                'remaining': str(budget_status['remaining']),
                'percentage_used': budget_status['percentage'],
                'status': budget_status['status'],
                'breakdown': {
                    'air': {
                        'budget': str(budget.air_budget),
                        'spent': str(spent_by_category['air']),
                        'remaining': str(budget.air_budget - spent_by_category['air'])
                    },
                    'accommodation': {
                        'budget': str(budget.accommodation_budget),
                        'spent': str(spent_by_category['accommodation']),
                        'remaining': str(budget.accommodation_budget - spent_by_category['accommodation'])
                    },
                    'car_hire': {
                        'budget': str(budget.car_hire_budget),
                        'spent': str(spent_by_category['car_hire']),
                        'remaining': str(budget.car_hire_budget - spent_by_category['car_hire'])
                    },
                    'other': {
                        'budget': str(budget.other_budget),
                        'spent': str(spent_by_category['other']),
                        'remaining': str(budget.other_budget - spent_by_category['other'])
                    }
                },
                'carbon': {
                    'budget': str(budget.carbon_budget),
                    # Carbon emissions tracking would be calculated here
                    'used': '0',  # Placeholder - implement carbon tracking
                    'remaining': str(budget.carbon_budget)
                },
                'thresholds': {
                    'warning': budget.warning_threshold,
                    'critical': budget.critical_threshold
                }
            })

        except Budget.DoesNotExist:
            return Response(
                {'error': 'Budget not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get budget summary for an organization or fiscal year"""
        org_id = request.query_params.get('organization_id')
        fiscal_year_id = request.query_params.get('fiscal_year_id')

        if not org_id:
            return Response(
                {'error': 'organization_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = Budget.objects.filter(organization_id=org_id, is_active=True)

        if fiscal_year_id:
            queryset = queryset.filter(fiscal_year_id=fiscal_year_id)

        # Calculate totals
        totals = queryset.aggregate(
            total_budgeted=Sum('total_budget'),
            total_carbon=Sum('carbon_budget')
        )

        # Count budgets by status
        status_counts = {'OK': 0, 'WARNING': 0, 'CRITICAL': 0, 'EXCEEDED': 0}
        total_spent = Decimal('0.00')

        for budget in queryset:
            try:
                budget_status = budget.get_budget_status()
                status_counts[budget_status['status']] += 1
                total_spent += budget_status['spent']
            except:
                pass

        return Response({
            'organization_id': org_id,
            'fiscal_year_id': fiscal_year_id,
            'total_budgets': queryset.count(),
            'total_budgeted': str(totals['total_budgeted'] or 0),
            'total_spent': str(total_spent),
            'total_carbon_budget': str(totals['total_carbon'] or 0),
            'status_breakdown': status_counts
        })
