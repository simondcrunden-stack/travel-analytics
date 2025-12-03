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
