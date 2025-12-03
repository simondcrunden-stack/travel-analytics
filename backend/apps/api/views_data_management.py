# apps/api/views_data_management.py
# API endpoints for data merging and management

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Count
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from difflib import SequenceMatcher
import logging

from apps.bookings.models import Traveller, Booking, MergeAudit
from .permissions import IsAdminUser

logger = logging.getLogger(__name__)


def calculate_name_similarity(name1, name2):
    """
    Calculate similarity score between two names (0.0 to 1.0)
    Uses SequenceMatcher for fuzzy matching
    """
    if not name1 or not name2:
        return 0.0

    name1_clean = name1.lower().strip()
    name2_clean = name2.lower().strip()

    if name1_clean == name2_clean:
        return 1.0

    return SequenceMatcher(None, name1_clean, name2_clean).ratio()


class TravellerMergeViewSet(viewsets.ViewSet):
    """
    API endpoints for finding and merging duplicate travellers
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['get'])
    def find_duplicates(self, request):
        """
        Find potential duplicate travellers within an organization

        Query params:
        - organization_id or organization: Organization ID (required for org admins, optional for system admins)
        - min_similarity: Minimum name similarity score (0.0-1.0, default 0.7)
        """
        org_id = request.query_params.get('organization_id') or request.query_params.get('organization')
        min_similarity = float(request.query_params.get('min_similarity', 0.7))

        # Get organization context
        if not org_id and request.user.user_type != 'ADMIN':
            # Organization admins must specify their org
            if hasattr(request.user, 'organization'):
                org_id = request.user.organization.id
            else:
                return Response(
                    {'error': 'Organization parameter required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Base queryset
        travellers = Traveller.objects.filter(is_active=True)

        if org_id:
            travellers = travellers.filter(organization_id=org_id)

        # Annotate with booking count for context
        travellers = travellers.annotate(
            booking_count=Count('bookings')
        ).order_by('organization', 'last_name', 'first_name')

        # Find duplicates
        duplicate_groups = []
        processed_ids = set()

        for traveller in travellers:
            if str(traveller.id) in processed_ids:
                continue

            traveller_full_name = f"{traveller.first_name} {traveller.last_name}"

            # Find potential matches in same organization
            potential_matches = travellers.filter(
                organization=traveller.organization
            ).exclude(id=traveller.id)

            matches = []
            for candidate in potential_matches:
                if str(candidate.id) in processed_ids:
                    continue

                candidate_full_name = f"{candidate.first_name} {candidate.last_name}"
                similarity = calculate_name_similarity(
                    traveller_full_name,
                    candidate_full_name
                )

                # Also check employee ID match
                employee_id_match = False
                if traveller.employee_id and candidate.employee_id:
                    employee_id_match = traveller.employee_id == candidate.employee_id

                # Include if similarity meets threshold or employee IDs match
                if similarity >= min_similarity or employee_id_match:
                    matches.append({
                        'id': str(candidate.id),
                        'first_name': candidate.first_name,
                        'last_name': candidate.last_name,
                        'email': candidate.email,
                        'employee_id': candidate.employee_id,
                        'department': candidate.department,
                        'booking_count': candidate.booking_count,
                        'similarity_score': round(similarity, 2),
                        'employee_id_match': employee_id_match,
                        'created_at': candidate.created_at.isoformat()
                    })

            if matches:
                # Add the primary traveller
                group = {
                    'primary': {
                        'id': str(traveller.id),
                        'first_name': traveller.first_name,
                        'last_name': traveller.last_name,
                        'email': traveller.email,
                        'employee_id': traveller.employee_id,
                        'department': traveller.department,
                        'booking_count': traveller.booking_count,
                        'created_at': traveller.created_at.isoformat()
                    },
                    'matches': sorted(matches, key=lambda x: x['similarity_score'], reverse=True),
                    'organization_id': str(traveller.organization.id),
                    'organization_name': traveller.organization.name
                }
                duplicate_groups.append(group)

                # Mark all as processed
                processed_ids.add(str(traveller.id))
                for match in matches:
                    processed_ids.add(match['id'])

        return Response({
            'duplicate_groups': duplicate_groups,
            'total_groups': len(duplicate_groups),
            'min_similarity': min_similarity
        })

    @action(detail=False, methods=['post'])
    def merge(self, request):
        """
        Merge multiple travellers into one

        Request body:
        {
            "primary_id": "uuid",  // The traveller to keep
            "merge_ids": ["uuid1", "uuid2"],  // Travellers to merge in
            "chosen_name": "Full Name",  // Optional: custom name
            "chosen_employee_id": "EMP123"  // Optional: which employee ID to keep
        }
        """
        primary_id = request.data.get('primary_id')
        merge_ids = request.data.get('merge_ids', [])
        chosen_name = request.data.get('chosen_name', '')
        chosen_employee_id = request.data.get('chosen_employee_id', '')

        if not primary_id or not merge_ids:
            return Response(
                {'error': 'primary_id and merge_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Get the primary traveller
                primary_traveller = Traveller.objects.get(id=primary_id)

                # Verify permission
                if request.user.user_type != 'ADMIN':
                    if not hasattr(request.user, 'organization') or \
                       request.user.organization != primary_traveller.organization:
                        return Response(
                            {'error': 'Permission denied'},
                            status=status.HTTP_403_FORBIDDEN
                        )

                # Get travellers to merge
                merge_travellers = Traveller.objects.filter(id__in=merge_ids)

                # Verify all in same organization
                for traveller in merge_travellers:
                    if traveller.organization != primary_traveller.organization:
                        return Response(
                            {'error': 'All travellers must be in the same organization'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                # Create snapshots for undo
                merged_records_snapshot = {}
                relationship_updates = {
                    'bookings': []
                }

                for traveller in merge_travellers:
                    # Snapshot the record
                    merged_records_snapshot[str(traveller.id)] = {
                        'id': str(traveller.id),
                        'first_name': traveller.first_name,
                        'last_name': traveller.last_name,
                        'email': traveller.email,
                        'employee_id': traveller.employee_id,
                        'department': traveller.department,
                        'organization_id': str(traveller.organization.id),
                        'created_at': traveller.created_at.isoformat()
                    }

                    # Reassign all bookings to primary traveller
                    bookings = Booking.objects.filter(traveller=traveller)
                    booking_ids = list(bookings.values_list('id', flat=True))
                    relationship_updates['bookings'].extend([str(bid) for bid in booking_ids])

                    bookings.update(traveller=primary_traveller)

                # Update primary traveller if custom name/employee_id provided
                if chosen_name:
                    name_parts = chosen_name.strip().split(' ', 1)
                    primary_traveller.first_name = name_parts[0]
                    primary_traveller.last_name = name_parts[1] if len(name_parts) > 1 else ''

                if chosen_employee_id:
                    primary_traveller.employee_id = chosen_employee_id

                primary_traveller.save()

                # Create merge audit record
                merge_audit = MergeAudit.objects.create(
                    merge_type='TRAVELLER',
                    performed_by=request.user,
                    organization=primary_traveller.organization,
                    primary_content_type=ContentType.objects.get_for_model(Traveller),
                    primary_object_id=str(primary_traveller.id),
                    merged_record_ids=[str(t.id) for t in merge_travellers],
                    merged_records_snapshot=merged_records_snapshot,
                    relationship_updates=relationship_updates,
                    chosen_name=chosen_name,
                    chosen_employee_id=chosen_employee_id,
                    summary=f"Merged {len(merge_travellers)} travellers into {primary_traveller.first_name} {primary_traveller.last_name}",
                    status='COMPLETED'
                )

                # Delete merged travellers
                merge_travellers.delete()

                logger.info(f"Successfully merged {len(merge_ids)} travellers into {primary_id}")

                return Response({
                    'success': True,
                    'merge_audit_id': str(merge_audit.id),
                    'primary_traveller': {
                        'id': str(primary_traveller.id),
                        'name': f"{primary_traveller.first_name} {primary_traveller.last_name}",
                        'employee_id': primary_traveller.employee_id
                    },
                    'merged_count': len(merge_ids),
                    'reassigned_bookings': len(relationship_updates['bookings'])
                })

        except Traveller.DoesNotExist:
            return Response(
                {'error': 'Traveller not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error merging travellers: {str(e)}")
            return Response(
                {'error': f'Merge failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def undo(self, request, pk=None):
        """
        Undo a merge operation

        URL: /api/traveller-merge/<merge_audit_id>/undo/
        """
        try:
            with transaction.atomic():
                # Get the merge audit record
                merge_audit = MergeAudit.objects.get(id=pk, merge_type='TRAVELLER')

                if merge_audit.status == 'UNDONE':
                    return Response(
                        {'error': 'This merge has already been undone'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Verify permission
                if request.user.user_type != 'ADMIN':
                    if not hasattr(request.user, 'organization') or \
                       request.user.organization != merge_audit.organization:
                        return Response(
                            {'error': 'Permission denied'},
                            status=status.HTTP_403_FORBIDDEN
                        )

                # Restore merged travellers from snapshot
                restored_count = 0
                for traveller_id, snapshot in merge_audit.merged_records_snapshot.items():
                    Traveller.objects.create(
                        id=traveller_id,
                        organization_id=snapshot['organization_id'],
                        first_name=snapshot['first_name'],
                        last_name=snapshot['last_name'],
                        email=snapshot['email'],
                        employee_id=snapshot['employee_id'],
                        department=snapshot['department']
                    )
                    restored_count += 1

                # TODO: Reassign bookings back to their original travellers
                # This would require storing which booking belonged to which traveller
                # For now, bookings stay with the primary traveller

                # Mark audit as undone
                merge_audit.status = 'UNDONE'
                merge_audit.undone_by = request.user
                merge_audit.undone_at = timezone.now()
                merge_audit.save()

                logger.info(f"Successfully undid merge {pk}, restored {restored_count} travellers")

                return Response({
                    'success': True,
                    'restored_count': restored_count,
                    'message': f'Merge undone successfully. {restored_count} travellers restored.'
                })

        except MergeAudit.DoesNotExist:
            return Response(
                {'error': 'Merge audit record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error undoing merge: {str(e)}")
            return Response(
                {'error': f'Undo failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MergeAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for viewing merge audit trail
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter audit records based on user permissions"""
        queryset = MergeAudit.objects.all()

        # Filter by organization if not system admin
        if self.request.user.user_type != 'ADMIN':
            if hasattr(self.request.user, 'organization'):
                queryset = queryset.filter(organization=self.request.user.organization)

        # Search by summary (names, description)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(summary__icontains=search)

        # Filter by merge type if specified
        merge_type = self.request.query_params.get('merge_type')
        if merge_type:
            queryset = queryset.filter(merge_type=merge_type)

        # Filter by status if specified
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.select_related('performed_by', 'organization', 'undone_by')

    def list(self, request):
        """List all merge audits"""
        queryset = self.get_queryset()

        results = []
        for audit in queryset:
            results.append({
                'id': str(audit.id),
                'merge_type': audit.merge_type,
                'merge_type_display': audit.get_merge_type_display(),
                'status': audit.status,
                'performed_by': audit.performed_by.username if audit.performed_by else None,
                'organization': audit.organization.name if audit.organization else None,
                'summary': audit.summary,
                'chosen_name': audit.chosen_name,
                'chosen_employee_id': audit.chosen_employee_id,
                'merged_count': len(audit.merged_record_ids),
                'created_at': audit.created_at.isoformat(),
                'undone_at': audit.undone_at.isoformat() if audit.undone_at else None,
                'undone_by': audit.undone_by.username if audit.undone_by else None
            })

        return Response({
            'results': results,
            'count': len(results)
        })

    def retrieve(self, request, pk=None):
        """Get detailed merge audit record"""
        try:
            audit = self.get_queryset().get(id=pk)

            return Response({
                'id': str(audit.id),
                'merge_type': audit.merge_type,
                'merge_type_display': audit.get_merge_type_display(),
                'status': audit.status,
                'performed_by': audit.performed_by.username if audit.performed_by else None,
                'organization': {
                    'id': str(audit.organization.id),
                    'name': audit.organization.name
                } if audit.organization else None,
                'primary_object_id': audit.primary_object_id,
                'merged_record_ids': audit.merged_record_ids,
                'merged_records_snapshot': audit.merged_records_snapshot,
                'relationship_updates': audit.relationship_updates,
                'summary': audit.summary,
                'chosen_name': audit.chosen_name,
                'chosen_employee_id': audit.chosen_employee_id,
                'created_at': audit.created_at.isoformat(),
                'undone_at': audit.undone_at.isoformat() if audit.undone_at else None,
                'undone_by': audit.undone_by.username if audit.undone_by else None
            })
        except MergeAudit.DoesNotExist:
            return Response(
                {'error': 'Merge audit record not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ConsultantMergeViewSet(viewsets.ViewSet):
    """
    API endpoints for finding and merging duplicate consultant text entries
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['get'])
    def find_duplicates(self, request):
        """
        Find similar consultant text entries in bookings

        Query params:
        - travel_agent_id: Travel Agent organization ID (searches across all their customers)
        - organization_id: Single organization ID (fallback for non-agent users)
        - min_similarity: Minimum similarity score (0.0-1.0, default 0.7)
        """
        travel_agent_id = request.query_params.get('travel_agent_id')
        org_id = request.query_params.get('organization_id') or request.query_params.get('organization')
        min_similarity = float(request.query_params.get('min_similarity', 0.7))

        # Get bookings - consultants work across all organizations for a travel agent
        bookings_query = Booking.objects.filter(
            travel_consultant_text__isnull=False
        ).exclude(travel_consultant_text='')

        if travel_agent_id:
            # Search across the travel agent's organization AND all their customer organizations
            from apps.organizations.models import Organization
            bookings_query = bookings_query.filter(
                Q(organization_id=travel_agent_id) |  # Agent's own bookings
                Q(organization__travel_agent_id=travel_agent_id)  # Customer bookings
            )
        elif org_id:
            # Fallback to single organization
            bookings_query = bookings_query.filter(organization_id=org_id)
        elif request.user.user_type != 'ADMIN':
            # For non-admins, use their organization context
            if hasattr(request.user, 'organization'):
                org_id = request.user.organization.id
                bookings_query = bookings_query.filter(organization_id=org_id)
            else:
                return Response(
                    {'error': 'Organization or travel agent parameter required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Group by consultant text and count bookings
        consultant_texts = bookings_query.values('travel_consultant_text').annotate(
            booking_count=Count('id')
        ).order_by('travel_consultant_text')

        # Find duplicates using fuzzy matching
        duplicate_groups = []
        processed_texts = set()

        for item in consultant_texts:
            consultant_text = item['travel_consultant_text']

            if consultant_text in processed_texts:
                continue

            # Find similar consultant names
            matches = []
            for candidate in consultant_texts:
                candidate_text = candidate['travel_consultant_text']

                if candidate_text in processed_texts or candidate_text == consultant_text:
                    continue

                similarity = calculate_name_similarity(consultant_text, candidate_text)

                if similarity >= min_similarity:
                    matches.append({
                        'text': candidate_text,
                        'booking_count': candidate['booking_count'],
                        'similarity_score': round(similarity, 2)
                    })
                    processed_texts.add(candidate_text)

            if matches:
                group = {
                    'primary': {
                        'text': consultant_text,
                        'booking_count': item['booking_count']
                    },
                    'matches': sorted(matches, key=lambda x: x['similarity_score'], reverse=True)
                }
                duplicate_groups.append(group)
                processed_texts.add(consultant_text)

        return Response({
            'duplicate_groups': duplicate_groups,
            'total_groups': len(duplicate_groups),
            'min_similarity': min_similarity
        })

    @action(detail=False, methods=['post'])
    def merge(self, request):
        """
        Merge consultant text entries by standardizing the text across bookings

        Request body:
        - primary_text: The text to keep as standard
        - merge_texts: List of text variations to standardize
        - chosen_text: Optional custom text to use (overrides primary_text)
        - travel_agent_id: Travel agent context (searches across all their customers)
        - organization_id: Single organization context (fallback)
        """
        primary_text = request.data.get('primary_text')
        merge_texts = request.data.get('merge_texts', [])
        chosen_text = request.data.get('chosen_text', '')
        travel_agent_id = request.data.get('travel_agent_id')
        org_id = request.data.get('organization_id')

        if not primary_text or not merge_texts:
            return Response(
                {'error': 'primary_text and merge_texts are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use chosen text if provided, otherwise use primary
        final_text = chosen_text if chosen_text else primary_text

        try:
            with transaction.atomic():
                # Find all bookings with the merge texts
                bookings_to_update = Booking.objects.filter(
                    travel_consultant_text__in=merge_texts
                )

                # Apply same filtering logic as find_duplicates
                if travel_agent_id:
                    from apps.organizations.models import Organization
                    bookings_to_update = bookings_to_update.filter(
                        Q(organization_id=travel_agent_id) |
                        Q(organization__travel_agent_id=travel_agent_id)
                    )
                elif org_id:
                    bookings_to_update = bookings_to_update.filter(organization_id=org_id)

                # Track what we're changing
                snapshot = {}
                for text in merge_texts:
                    matching_bookings = bookings_to_update.filter(travel_consultant_text=text)
                    snapshot[text] = {
                        'booking_count': matching_bookings.count(),
                        'booking_ids': [str(b.id) for b in matching_bookings[:100]]  # Sample
                    }

                # Update all bookings
                updated_count = bookings_to_update.update(travel_consultant_text=final_text)

                # Create audit record
                merge_audit = MergeAudit.objects.create(
                    merge_type='CONSULTANT',
                    performed_by=request.user,
                    organization_id=org_id if org_id else None,
                    primary_content_type=ContentType.objects.get_for_model(Booking),
                    primary_object_id=primary_text,  # Store primary text as ID
                    merged_record_ids=merge_texts,
                    merged_records_snapshot=snapshot,
                    relationship_updates={'bookings_updated': updated_count},
                    chosen_name=final_text,
                    summary=f"Standardized consultant text '{final_text}' across {updated_count} bookings (from {len(merge_texts)} variations)"
                )

                # Create standardization rules for each variation (auto-normalize future imports)
                from apps.bookings.models import StandardizationRule
                rules_created = 0
                for merge_text in merge_texts:
                    if merge_text != final_text:  # Don't create rule for text mapping to itself
                        # Use get_or_create to avoid duplicates
                        rule, created = StandardizationRule.objects.get_or_create(
                            rule_type='CONSULTANT',
                            source_text=merge_text,
                            travel_agent_id=travel_agent_id if travel_agent_id else None,
                            organization_id=org_id if (org_id and not travel_agent_id) else None,
                            defaults={
                                'target_text': final_text,
                                'created_from_merge': merge_audit,
                                'created_by': request.user,
                                'is_active': True
                            }
                        )
                        if created:
                            rules_created += 1
                        elif not created and rule.target_text != final_text:
                            # Update existing rule if target has changed
                            rule.target_text = final_text
                            rule.save()

                return Response({
                    'success': True,
                    'merged_count': len(merge_texts),
                    'bookings_updated': updated_count,
                    'final_text': final_text,
                    'audit_id': str(merge_audit.id),
                    'rules_created': rules_created
                })

        except Exception as e:
            logger.error(f"Error merging consultant texts: {str(e)}")
            return Response(
                {'error': f'Merge failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def undo(self, request, pk=None):
        """
        Undo a consultant text merge operation
        """
        try:
            with transaction.atomic():
                merge_audit = MergeAudit.objects.get(id=pk, merge_type='CONSULTANT')

                if merge_audit.status == 'UNDONE':
                    return Response(
                        {'error': 'This merge has already been undone'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Restore original consultant texts
                restored_count = 0
                for text, data in merge_audit.merged_records_snapshot.items():
                    booking_ids = data.get('booking_ids', [])
                    # Restore bookings back to their original text
                    Booking.objects.filter(id__in=booking_ids).update(travel_consultant_text=text)
                    restored_count += len(booking_ids)

                # Deactivate standardization rules created from this merge
                from apps.bookings.models import StandardizationRule
                deactivated_rules = StandardizationRule.objects.filter(
                    created_from_merge=merge_audit,
                    is_active=True
                ).update(is_active=False)

                # Mark as undone
                merge_audit.status = 'UNDONE'
                merge_audit.undone_at = timezone.now()
                merge_audit.undone_by = request.user
                merge_audit.save()

                return Response({
                    'success': True,
                    'restored_count': restored_count
                })

        except MergeAudit.DoesNotExist:
            return Response(
                {'error': 'Merge audit record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error undoing consultant merge: {str(e)}")
            return Response(
                {'error': f'Undo failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StandardizationRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing and managing standardization rules.

    These rules are auto-created during merge operations and applied during data imports
    to prevent duplicates from being created.

    Endpoints:
    - GET /data-management/standardization-rules/ - List all rules (filtered by context)
    - GET /data-management/standardization-rules/{id}/ - Get specific rule
    - PATCH /data-management/standardization-rules/{id}/ - Update rule (activate/deactivate)
    - DELETE /data-management/standardization-rules/{id}/ - Delete rule
    - POST /data-management/standardization-rules/bulk_activate/ - Activate multiple rules
    - POST /data-management/standardization-rules/bulk_deactivate/ - Deactivate multiple rules
    - POST /data-management/standardization-rules/bulk_delete/ - Delete multiple rules
    """
    from apps.bookings.models import StandardizationRule
    queryset = StandardizationRule.objects.all()
    serializer_class = None  # We'll create a simple serializer inline
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter rules by user's context"""
        queryset = super().get_queryset()

        # Filter by rule type
        rule_type = self.request.query_params.get('rule_type')
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by travel agent
        travel_agent_id = self.request.query_params.get('travel_agent_id')
        if travel_agent_id:
            queryset = queryset.filter(travel_agent_id=travel_agent_id)

        # Filter by organization
        org_id = self.request.query_params.get('organization_id')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        return queryset.select_related('travel_agent', 'organization', 'created_by', 'created_from_merge')

    def list(self, request):
        """List standardization rules with filtering"""
        queryset = self.get_queryset()

        # Serialize manually since we don't have a formal serializer
        rules_data = []
        for rule in queryset:
            rules_data.append({
                'id': str(rule.id),
                'rule_type': rule.rule_type,
                'rule_type_display': rule.get_rule_type_display(),
                'source_text': rule.source_text,
                'target_text': rule.target_text,
                'travel_agent': {
                    'id': str(rule.travel_agent.id),
                    'name': rule.travel_agent.name
                } if rule.travel_agent else None,
                'organization': {
                    'id': str(rule.organization.id),
                    'name': rule.organization.name
                } if rule.organization else None,
                'is_active': rule.is_active,
                'created_at': rule.created_at.isoformat(),
                'created_by': rule.created_by.email if rule.created_by else None,
                'application_count': rule.application_count,
                'last_applied_at': rule.last_applied_at.isoformat() if rule.last_applied_at else None,
                'created_from_merge': {
                    'id': str(rule.created_from_merge.id),
                    'summary': rule.created_from_merge.summary
                } if rule.created_from_merge else None,
            })

        return Response({'results': rules_data})

    def retrieve(self, request, pk=None):
        """Get a specific standardization rule"""
        try:
            rule = self.get_queryset().get(id=pk)

            return Response({
                'id': str(rule.id),
                'rule_type': rule.rule_type,
                'rule_type_display': rule.get_rule_type_display(),
                'source_text': rule.source_text,
                'target_text': rule.target_text,
                'travel_agent': {
                    'id': str(rule.travel_agent.id),
                    'name': rule.travel_agent.name
                } if rule.travel_agent else None,
                'organization': {
                    'id': str(rule.organization.id),
                    'name': rule.organization.name
                } if rule.organization else None,
                'is_active': rule.is_active,
                'created_at': rule.created_at.isoformat(),
                'created_by': rule.created_by.email if rule.created_by else None,
                'application_count': rule.application_count,
                'last_applied_at': rule.last_applied_at.isoformat() if rule.last_applied_at else None,
                'created_from_merge': {
                    'id': str(rule.created_from_merge.id),
                    'summary': rule.created_from_merge.summary
                } if rule.created_from_merge else None,
            })
        except self.queryset.model.DoesNotExist:
            return Response(
                {'error': 'Rule not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def partial_update(self, request, pk=None):
        """Update a standardization rule (typically to activate/deactivate)"""
        try:
            rule = self.get_queryset().get(id=pk)

            # Only allow updating is_active and target_text
            if 'is_active' in request.data:
                rule.is_active = request.data['is_active']

            if 'target_text' in request.data:
                rule.target_text = request.data['target_text']

            rule.save()

            return Response({
                'success': True,
                'rule': {
                    'id': str(rule.id),
                    'is_active': rule.is_active,
                    'target_text': rule.target_text
                }
            })
        except self.queryset.model.DoesNotExist:
            return Response(
                {'error': 'Rule not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, pk=None):
        """Delete a standardization rule"""
        try:
            rule = self.get_queryset().get(id=pk)
            rule.delete()

            return Response({'success': True})
        except self.queryset.model.DoesNotExist:
            return Response(
                {'error': 'Rule not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def bulk_activate(self, request):
        """Activate multiple rules"""
        rule_ids = request.data.get('rule_ids', [])

        if not rule_ids:
            return Response(
                {'error': 'rule_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated = self.get_queryset().filter(id__in=rule_ids).update(is_active=True)

        return Response({
            'success': True,
            'updated_count': updated
        })

    @action(detail=False, methods=['post'])
    def bulk_deactivate(self, request):
        """Deactivate multiple rules"""
        rule_ids = request.data.get('rule_ids', [])

        if not rule_ids:
            return Response(
                {'error': 'rule_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated = self.get_queryset().filter(id__in=rule_ids).update(is_active=False)

        return Response({
            'success': True,
            'updated_count': updated
        })

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Delete multiple rules"""
        rule_ids = request.data.get('rule_ids', [])

        if not rule_ids:
            return Response(
                {'error': 'rule_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count, _ = self.get_queryset().filter(id__in=rule_ids).delete()

        return Response({
            'success': True,
            'deleted_count': deleted_count
        })
