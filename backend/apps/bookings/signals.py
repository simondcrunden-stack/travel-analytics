# apps/bookings/signals.py
"""
Django signals for automatic calculations and updates.
Session 38-39: Transaction tracking + Audit logging
"""

from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.db.models import Sum
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Import models
from .models import (
    Booking,
    AirSegment,
    AirBooking,
    AccommodationBooking,
    CarHireBooking,
    ServiceFee,
    BookingTransaction,
    BookingAuditLog
)

# =================================================================
# SIGNAL 1 & 2: CARBON EMISSIONS RECALCULATION
# =================================================================

@receiver(post_save, sender=AirSegment)
def recalculate_carbon_on_segment_save(sender, instance, **kwargs):
    """
    Signal 1: When an AirSegment is saved, recalculate the total carbon
    emissions for its parent AirBooking.
    """
    try:
        air_booking = instance.air_booking
        if air_booking:
            total_carbon = air_booking.air_segments.aggregate(
                total=Sum('carbon_emissions_kg')
            )['total'] or Decimal('0.00')
            
            # Update using queryset to avoid triggering another save signal
            AirBooking.objects.filter(pk=air_booking.pk).update(
                total_carbon_emissions_kg=total_carbon
            )
            
            logger.info(
                f"Carbon emissions updated for AirBooking {air_booking.id}: "
                f"{total_carbon} kg CO2"
            )
    except Exception as e:
        logger.error(f"Error in recalculate_carbon_on_segment_save: {e}")


@receiver(post_delete, sender=AirSegment)
def recalculate_carbon_on_segment_delete(sender, instance, **kwargs):
    """
    Signal 2: When an AirSegment is deleted, recalculate the total carbon
    emissions for its parent AirBooking.
    """
    try:
        air_booking = instance.air_booking
        if air_booking:
            total_carbon = air_booking.air_segments.aggregate(
                total=Sum('carbon_emissions_kg')
            )['total'] or Decimal('0.00')
            
            AirBooking.objects.filter(pk=air_booking.pk).update(
                total_carbon_emissions_kg=total_carbon
            )
            
            logger.info(
                f"Carbon emissions updated after segment deletion for "
                f"AirBooking {air_booking.id}: {total_carbon} kg CO2"
            )
    except Exception as e:
        logger.error(f"Error in recalculate_carbon_on_segment_delete: {e}")


# =================================================================
# SIGNAL 3: POTENTIAL SAVINGS CALCULATION
# =================================================================

@receiver(post_save, sender=AirBooking)
def calculate_potential_savings(sender, instance, created, **kwargs):
    """
    Signal 3: When an AirBooking is created or updated, calculate potential
    savings if lowest_fare_available is provided.
    """
    try:
        if not instance.lowest_fare_available:
            return
            
        # Get the parent booking to access base_fare
        booking = instance.booking
        if not booking:
            return
            
        base_fare = booking.base_fare or Decimal('0.00')
        lowest_fare = instance.lowest_fare_available
        
        if lowest_fare < base_fare:
            savings = base_fare - lowest_fare
            AirBooking.objects.filter(pk=instance.pk).update(
                potential_savings=savings
            )
            logger.info(
                f"Potential savings calculated for AirBooking {instance.id}: "
                f"${savings}"
            )
    except Exception as e:
        logger.error(f"Error in calculate_potential_savings: {e}")


# =================================================================
# SIGNAL 5: BOOKING TOTAL RECALCULATION
# =================================================================

@receiver(post_save, sender=AirBooking)
@receiver(post_save, sender=AccommodationBooking)
@receiver(post_save, sender=CarHireBooking)
@receiver(post_save, sender=ServiceFee)
@receiver(post_delete, sender=AirBooking)
@receiver(post_delete, sender=AccommodationBooking)
@receiver(post_delete, sender=CarHireBooking)
@receiver(post_delete, sender=ServiceFee)
def recalculate_booking_total(sender, instance, **kwargs):
    """
    Signal 5: When any booking component changes, recalculate the parent
    Booking's total_amount field.
    """
    try:
        booking = instance.booking
        if not booking:
            return
        
        # Calculate totals from all related bookings
        air_total = booking.air_bookings.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        accommodation_total = booking.accommodation_bookings.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        car_total = booking.car_hire_bookings.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        fees_total = booking.service_fees.aggregate(
            total=Sum('fee_amount')
        )['total'] or Decimal('0.00')
        
        new_total = air_total + accommodation_total + car_total + fees_total
        
        # Update using queryset to avoid infinite loop
        Booking.objects.filter(pk=booking.pk).update(
            total_amount=new_total
        )
        
        # Create audit log for total recalculation
        BookingAuditLog.objects.create(
            booking=booking,
            action='TOTAL_RECALCULATED',
            changed_by=None,  # System action
            description=f'Total recalculated: ${new_total}',
            before_value={'total_amount': str(booking.total_amount)},
            after_value={'total_amount': str(new_total)}
        )
        
        logger.info(
            f"Booking {booking.id} total updated to ${new_total} "
            f"(Air: ${air_total}, Acc: ${accommodation_total}, "
            f"Car: ${car_total}, Fees: ${fees_total})"
        )
    except Exception as e:
        logger.error(f"Error in recalculate_booking_total: {e}")


# =================================================================
# SIGNAL 9A & 9B: TRANSACTION TOTAL UPDATES
# =================================================================

# Storage for pre-delete transaction data
_transaction_pre_delete_data = {}

@receiver(pre_delete, sender=BookingTransaction)
def capture_transaction_before_delete(sender, instance, **kwargs):
    """
    Helper signal: Capture transaction data before deletion so we can
    update totals after deletion.
    """
    _transaction_pre_delete_data[instance.pk] = {
        'content_type': instance.content_type,
        'object_id': instance.object_id,
        'amount': instance.amount,
        'currency': instance.currency
    }


@receiver(post_save, sender=BookingTransaction)
def update_component_total_on_transaction_save(sender, instance, **kwargs):
    """
    Signal 9A: When a BookingTransaction is saved, update the total_amount
    of its related component (Air/Accommodation/Car/ServiceFee).
    """
    try:
        # Get the related component
        component = instance.content_object
        if not component:
            logger.warning(f"Transaction {instance.pk} has no related component")
            return
        
        # Calculate new total from all transactions
        total = component.transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Update the component's total
        component.__class__.objects.filter(pk=component.pk).update(
            total_amount=total
        )
        
        # Create audit log
        BookingAuditLog.objects.create(
            booking=component.booking,
            action='TRANSACTION_CREATED' if kwargs.get('created') else 'TRANSACTION_MODIFIED',
            changed_by=instance.created_by if hasattr(instance, 'created_by') else None,
            description=f'Transaction {instance.get_transaction_type_display()}: ${instance.amount}',
            before_value={},
            after_value={
                'transaction_type': instance.transaction_type,
                'amount': str(instance.amount),
                'currency': instance.currency
            }
        )
        
        logger.info(
            f"Component {component.__class__.__name__} {component.pk} "
            f"total updated to ${total} after transaction save"
        )
    except Exception as e:
        logger.error(f"Error in update_component_total_on_transaction_save: {e}")


@receiver(post_delete, sender=BookingTransaction)
def update_component_total_on_transaction_delete(sender, instance, **kwargs):
    """
    Signal 9B: When a BookingTransaction is deleted, update the total_amount
    of its related component.
    """
    try:
        # Get transaction data captured before deletion
        data = _transaction_pre_delete_data.pop(instance.pk, None)
        if not data:
            logger.warning(f"No pre-delete data found for transaction {instance.pk}")
            return
        
        # Get the component using the captured data
        model_class = data['content_type'].model_class()
        try:
            component = model_class.objects.get(pk=data['object_id'])
        except model_class.DoesNotExist:
            logger.warning(f"Component {model_class.__name__} {data['object_id']} no longer exists")
            return
        
        # Calculate new total from remaining transactions
        total = component.transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Update the component's total
        model_class.objects.filter(pk=component.pk).update(
            total_amount=total
        )
        
        # Create audit log
        BookingAuditLog.objects.create(
            booking=component.booking,
            action='TRANSACTION_DELETED',
            changed_by=None,  # User not available in post_delete
            description=f'Transaction deleted: ${data["amount"]}',
            before_value={
                'amount': str(data['amount']),
                'currency': data['currency']
            },
            after_value={}
        )
        
        logger.info(
            f"Component {model_class.__name__} {component.pk} "
            f"total updated to ${total} after transaction deletion"
        )
    except Exception as e:
        logger.error(f"Error in update_component_total_on_transaction_delete: {e}")


# =================================================================
# DISABLED SIGNALS (Future Implementation)
# =================================================================

# Signal 4: Status Cascade - Not applicable (sub-bookings don't have status)
# Signal 6: Budget Tracking - Blocked (Budget.spent field doesn't exist yet)
# Signal 7: Compliance Checking - Disabled (ComplianceAlert model missing)
# Signal 8: Currency Rate Changes - Optional feature, not yet implemented