"""
Django Signals for Travel Analytics - Phase 2 Automatic Recalculation

This module implements signal handlers for complex business logic that spans
multiple models. Signals automatically trigger recalculations when related
data changes.

Session 36 - Phase 2 Implementation (29 Oct 2025)
"""

import logging
from decimal import Decimal
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction

# Import models - Done inside signal functions to avoid circular imports
# from apps.bookings.models import (
#     AirBooking, AccommodationBooking, CarHireBooking, 
#     AirSegment, Booking
# )

logger = logging.getLogger(__name__)


# =============================================================================
# SIGNAL 1: AirSegment Changes → Update AirBooking Carbon
# =============================================================================

@receiver(post_save, sender='bookings.AirSegment')
def update_air_booking_carbon_on_segment_save(sender, instance, created, **kwargs):
    """
    When an AirSegment is saved (created or updated), recalculate the
    total carbon emissions for the parent AirBooking.
    
    Triggers on:
    - New segment added
    - Segment carbon_emissions_kg changed
    - Segment route changed (affects carbon calculation)
    """
    if instance.air_booking:
        try:
            # Import inside function to avoid circular import
            from apps.bookings.models import AirBooking
            
            air_booking = instance.air_booking
            
            # Calculate new total from all segments
            total_carbon = air_booking.calculate_total_carbon()

            # Save it to the database
            AirBooking.objects.filter(pk=air_booking.pk).update(total_carbon_kg=total_carbon)
            
            if created:
                logger.info(
                    f"New segment added to {air_booking.booking.agent_booking_reference}: "
                    f"{instance.origin_airport_iata_code} → {instance.destination_airport_iata_code}, "
                    f"Carbon: {instance.carbon_emissions_kg} kg, "
                    f"New total: {total_carbon} kg"
                )
            else:
                logger.info(
                    f"Segment updated for {air_booking.booking.agent_booking_reference}: "
                    f"New total carbon: {total_carbon} kg"
                )
                
        except Exception as e:
            logger.error(
                f"Error updating carbon for AirBooking {instance.air_booking_id}: {e}"
            )


@receiver(post_delete, sender='bookings.AirSegment')
def update_air_booking_carbon_on_segment_delete(sender, instance, **kwargs):
    """
    When an AirSegment is deleted, recalculate the total carbon emissions
    for the parent AirBooking.
    
    Triggers on:
    - Segment deleted (cancellation, correction)
    """
    if instance.air_booking:
        try:
            # Import inside function to avoid circular import
            from apps.bookings.models import AirBooking
            
            air_booking = instance.air_booking
            
            # Calculate new total from remaining segments
            total_carbon = air_booking.calculate_total_carbon()

            # Save it to the database
            AirBooking.objects.filter(pk=air_booking.pk).update(total_carbon_kg=total_carbon)
            
            logger.info(
                f"Segment deleted from {air_booking.booking.agent_booking_reference}: "
                f"{instance.origin_airport_iata_code} → {instance.destination_airport_iata_code}, "
                f"New total carbon: {total_carbon} kg"
            )
                
        except Exception as e:
            logger.error(
                f"Error updating carbon after segment deletion for "
                f"AirBooking {instance.air_booking_id}: {e}"
            )


# =============================================================================
# SIGNAL 2: AirSegment Changes → Update AirBooking Potential Savings
# =============================================================================

@receiver(post_save, sender='bookings.AirSegment')
def update_air_booking_savings_on_segment_save(sender, instance, created, **kwargs):
    """
    When an AirSegment is saved, recalculate potential savings if lowest
    fare information changes.
    
    Triggers on:
    - Segment lowest_fare_available updated
    - New segment with fare data added
    """
    if instance.air_booking:
        try:
            air_booking = instance.air_booking
            
            # Only recalculate if we have fare data
            if air_booking.base_fare and air_booking.base_fare > 0:
                savings = air_booking.calculate_potential_savings()
                
                if savings and savings > 0:
                    logger.info(
                        f"Potential savings updated for {air_booking.booking.agent_booking_reference}: "
                        f"${savings}"
                    )
                
        except Exception as e:
            logger.error(
                f"Error updating savings for AirBooking {instance.air_booking_id}: {e}"
            )


# =============================================================================
# SIGNAL 3: Booking Changes → Update Related Sub-Bookings
# =============================================================================

@receiver(post_save, sender='bookings.Booking')
def handle_booking_status_change(sender, instance, created, **kwargs):
    """
    When a Booking's status changes, cascade the change to all related
    sub-bookings (Air, Accommodation, Car Hire).
    
    Triggers on:
    - Booking status changed to CANCELLED
    - Booking status changed to CONFIRMED
    
    Business Logic:
    - If parent booking is cancelled, all sub-bookings should be marked inactive
    - If booking is confirmed, trigger compliance checks
    """
    if not created:  # Only for updates, not new bookings
        from apps.bookings.models import AirBooking, AccommodationBooking, CarHireBooking
        
        try:
            # Check if status changed to CANCELLED
            if instance.status == 'CANCELLED':
                # Update all related bookings
                air_bookings = AirBooking.objects.filter(booking=instance)
                acc_bookings = AccommodationBooking.objects.filter(booking=instance)
                car_bookings = CarHireBooking.objects.filter(booking=instance)
                
                count = 0
                for air in air_bookings:
                    if air.is_active:
                        air.is_active = False
                        air.save()
                        count += 1
                        
                for acc in acc_bookings:
                    if acc.is_active:
                        acc.is_active = False
                        acc.save()
                        count += 1
                        
                for car in car_bookings:
                    if car.is_active:
                        car.is_active = False
                        car.save()
                        count += 1
                
                if count > 0:
                    logger.info(
                        f"Booking {instance.booking_reference} cancelled: "
                        f"Deactivated {count} sub-bookings"
                    )
                    
        except Exception as e:
            logger.error(
                f"Error handling status change for Booking {instance.booking_reference}: {e}"
            )


# =============================================================================
# SIGNAL 4: Sub-Booking Changes → Update Parent Booking Totals
# =============================================================================

@receiver(post_save, sender='bookings.AirBooking')
@receiver(post_save, sender='bookings.AccommodationBooking')
@receiver(post_save, sender='bookings.CarHireBooking')
def update_booking_totals(sender, instance, created, **kwargs):
    """
    When any sub-booking is saved, recalculate the parent Booking's
    total amounts.
    
    Triggers on:
    - AirBooking total_amount_base changes
    - AccommodationBooking total_amount_base changes
    - CarHireBooking total_amount_base changes
    
    Updates:
    - Booking.total_amount (sum of all active sub-bookings)
    """
    from apps.bookings.models import AirBooking, AccommodationBooking, CarHireBooking
    
    if instance.booking:
        try:
            booking = instance.booking
            
            # Calculate total from all active sub-bookings
            total = Decimal('0.00')
            
            # Sum air bookings
            air_total = AirBooking.objects.filter(
                booking=booking,
                is_active=True
            ).aggregate(
                total=models.Sum('total_amount_base')
            )['total'] or Decimal('0.00')
            
            # Sum accommodation bookings
            acc_total = AccommodationBooking.objects.filter(
                booking=booking,
                is_active=True
            ).aggregate(
                total=models.Sum('total_amount_base')
            )['total'] or Decimal('0.00')
            
            # Sum car hire bookings
            car_total = CarHireBooking.objects.filter(
                booking=booking,
                is_active=True
            ).aggregate(
                total=models.Sum('total_amount_base')
            )['total'] or Decimal('0.00')
            
            total = air_total + acc_total + car_total
            
            # Update parent booking if total changed
            if booking.total_amount != total:
                booking.total_amount = total
                booking.save(update_fields=['total_amount'])
                
                logger.info(
                    f"Updated total for {booking.agent_booking_reference}: "
                    f"Air: ${air_total}, Acc: ${acc_total}, Car: ${car_total}, "
                    f"Total: ${total}"
                )
                
        except Exception as e:
            logger.error(
                f"Error updating totals for Booking: {e}"
            )


# =============================================================================
# SIGNAL 5: Booking Changes → Update Budget Tracking
# =============================================================================

@receiver(post_save, sender='bookings.Booking')
def update_budget_tracking(sender, instance, created, **kwargs):
    """
    When a Booking is created or its total changes, update the related
    Budget's spent amount.
    
    Triggers on:
    - New booking created
    - Booking total_amount changed
    - Booking status changed
    
    Business Logic:
    - Only count CONFIRMED bookings toward budget
    - Recalculate budget spent and percentage used
    """
    from apps.budgets.models import Budget
    
    # Only process if booking has a budget assigned
    if hasattr(instance, 'budget') and instance.budget:
        try:
            budget = instance.budget
            
            # Calculate total spent from all confirmed bookings in this budget
            from django.db.models import Sum
            spent = Booking.objects.filter(
                budget=budget,
                status='CONFIRMED'
            ).aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            # Update budget if spent amount changed
            if budget.spent != spent:
                old_spent = budget.spent
                budget.spent = spent
                
                # Calculate percentage used
                if budget.total_budget > 0:
                    budget.percentage_used = (spent / budget.total_budget) * 100
                else:
                    budget.percentage_used = Decimal('0.00')
                
                budget.save(update_fields=['spent', 'percentage_used'])
                
                logger.info(
                    f"Budget '{budget.name}' updated: "
                    f"Was ${old_spent}, now ${spent} "
                    f"({budget.percentage_used:.1f}% of ${budget.total_budget})"
                )
                
        except Exception as e:
            logger.error(
                f"Error updating budget for Booking {instance.booking_reference}: {e}"
            )


# =============================================================================
# SIGNAL 6: Accommodation/Car Changes → Trigger Compliance Check
# =============================================================================

@receiver(post_save, sender='bookings.AccommodationBooking')
@receiver(post_save, sender='bookings.CarHireBooking')
def check_supplier_compliance(sender, instance, created, **kwargs):
    """
    When an accommodation or car hire booking is created, check if the
    supplier is on the preferred/approved list.
    
    Triggers on:
    - New accommodation booking created
    - New car hire booking created
    - Supplier changed on existing booking
    
    Business Logic:
    - Check if hotel chain / car rental company is preferred
    - Create compliance alert if non-preferred supplier used
    - Calculate potential savings with preferred supplier
    """
    from apps.compliance.models import ComplianceAlert
    from apps.reference_data.models import HotelChain, CarRentalCompany
    
    if created or instance.pk:  # New or existing booking
        try:
            is_compliant = True
            supplier_name = ""
            supplier_type = ""
            
            # Check accommodation compliance
            if sender.__name__ == 'AccommodationBooking':
                supplier_name = instance.hotel_name
                supplier_type = "Hotel"
                
                # Check if hotel chain exists and is preferred
                hotel_chain = HotelChain.objects.filter(
                    name__iexact=instance.hotel_name,
                    is_active=True
                ).first()
                
                if hotel_chain:
                    is_compliant = hotel_chain.is_preferred
                else:
                    # Hotel not in our database - potential non-compliance
                    is_compliant = False
            
            # Check car hire compliance
            elif sender.__name__ == 'CarHireBooking':
                supplier_name = instance.rental_company
                supplier_type = "Car Rental"
                
                # Check if car company exists and is preferred
                car_company = CarRentalCompany.objects.filter(
                    name__iexact=instance.rental_company,
                    is_active=True
                ).first()
                
                if car_company:
                    is_compliant = car_company.is_preferred
                else:
                    # Company not in our database - potential non-compliance
                    is_compliant = False
            
            # Create compliance alert if non-compliant
            if not is_compliant and instance.booking:
                alert, created_alert = ComplianceAlert.objects.get_or_create(
                    booking=instance.booking,
                    alert_type='NON_PREFERRED_SUPPLIER',
                    defaults={
                        'severity': 'MEDIUM',
                        'description': (
                            f"{supplier_type} '{supplier_name}' is not on the "
                            f"preferred supplier list. Consider using a preferred "
                            f"supplier for better rates and service."
                        ),
                        'traveller': instance.booking.traveller,
                        'is_resolved': False
                    }
                )
                
                if created_alert:
                    logger.warning(
                        f"Compliance alert created for {instance.booking.agent_booking_reference}: "
                        f"Non-preferred {supplier_type} '{supplier_name}'"
                    )
                    
        except Exception as e:
            logger.error(
                f"Error checking supplier compliance: {e}"
            )


# =============================================================================
# SIGNAL 7: Currency Rate Changes → Update Historical Bookings
# =============================================================================

@receiver(post_save, sender='reference_data.CurrencyExchangeRate')
def update_bookings_on_rate_change(sender, instance, created, **kwargs):
    """
    When a currency exchange rate is added or updated, recalculate affected
    bookings that use that currency.
    
    Triggers on:
    - New exchange rate added
    - Exchange rate updated
    
    Business Logic:
    - Find bookings with matching currency and date
    - Recalculate base currency amounts
    - Only update if new rate is significantly different (>1% change)
    
    NOTE: This is optional and may be commented out for performance.
    Consider running as a batch job instead of real-time signal.
    """
    if created:  # Only for new rates, not updates
        from apps.bookings.models import AccommodationBooking, CarHireBooking
        
        try:
            # Find accommodation bookings that might be affected
            affected_acc = AccommodationBooking.objects.filter(
                currency=instance.from_currency,
                check_in_date__gte=instance.rate_date,
                is_active=True
            )
            
            # Find car hire bookings that might be affected
            affected_car = CarHireBooking.objects.filter(
                currency=instance.from_currency,
                pickup_date__gte=instance.rate_date,
                is_active=True
            )
            
            count = 0
            for booking in affected_acc:
                booking.convert_to_base_currency()
                count += 1
                
            for booking in affected_car:
                booking.convert_to_base_currency()
                count += 1
            
            if count > 0:
                logger.info(
                    f"New exchange rate ({instance.from_currency} → {instance.to_currency}): "
                    f"Updated {count} bookings"
                )
                
        except Exception as e:
            logger.error(
                f"Error updating bookings after rate change: {e}"
            )


# =============================================================================
# HELPER: Add missing import for models
# =============================================================================

from django.db import models  # For aggregate functions


# =============================================================================
# Signal Registration Summary
# =============================================================================

"""
SIGNALS IMPLEMENTED IN THIS MODULE:

1. update_air_booking_carbon_on_segment_save
   - Trigger: AirSegment post_save
   - Action: Recalculate AirBooking.total_carbon_kg

2. update_air_booking_carbon_on_segment_delete
   - Trigger: AirSegment post_delete
   - Action: Recalculate AirBooking.total_carbon_kg

3. update_air_booking_savings_on_segment_save
   - Trigger: AirSegment post_save
   - Action: Recalculate AirBooking.potential_savings

4. handle_booking_status_change
   - Trigger: Booking post_save (status change)
   - Action: Cascade cancellations to sub-bookings

5. update_booking_totals
   - Trigger: AirBooking/AccommodationBooking/CarHireBooking post_save
   - Action: Update Booking.total_amount

6. update_budget_tracking
   - Trigger: Booking post_save
   - Action: Update Budget.spent and percentage_used

7. check_supplier_compliance
   - Trigger: AccommodationBooking/CarHireBooking post_save
   - Action: Create ComplianceAlert if non-preferred supplier

8. update_bookings_on_rate_change (OPTIONAL - can be disabled)
   - Trigger: CurrencyExchangeRate post_save
   - Action: Recalculate affected bookings

SIGNALS NOT YET IMPLEMENTED (Future Phase 3):
- Traveller profile updates affecting preferences
- Organization policy changes affecting compliance
- Real-time API updates triggering notifications
- Service fee calculations
- Commission tracking updates
"""