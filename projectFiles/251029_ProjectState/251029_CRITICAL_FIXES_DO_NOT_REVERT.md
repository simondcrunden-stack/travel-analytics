# CRITICAL FIXES - DO NOT REVERT
## Travel Analytics Platform - Session 35

**Purpose:** This document tracks all critical fixes that must be preserved across sessions.  
**Rule:** Any code changes must check this document first to avoid reverting important fixes.

---

## Session 33: Country Field Fix

### Problem
Country fields were required but not all bookings have country data, causing validation errors.

### Solution - APPLIED
Made country fields optional in both AccommodationBooking and CarHireBooking models.

### Files Modified
**File:** `backend/apps/bookings/models.py`

**CarHireBooking** (around line 742):
```python
# Country (Session 33: Made optional - DO NOT REVERT)
country = models.CharField(max_length=100, blank=True, null=True)
```

**AccommodationBooking** (around line 575):
```python
# Country (Session 33: Made optional - DO NOT REVERT)  
country = models.CharField(max_length=100, blank=True, null=True)
```

### Migration Created
```bash
python manage.py makemigrations bookings
python manage.py migrate
```

**Status:** ✅ CRITICAL - Must remain optional

---

## Session 34: Automatic Recalculation (Phase 1)

### Enhancement
Added automatic calculations when models are saved:
- AirBooking: Calculate total carbon and potential savings
- AccommodationBooking: Convert currency to base currency
- CarHireBooking: Convert currency to base currency
- CurrencyExchangeRate: Helper method for rate lookups

### Files Modified

#### 1. CurrencyExchangeRate Model
**File:** `backend/apps/reference_data/models.py`

**Added method** (around line 60):
```python
@classmethod
def get_rate(cls, from_currency, to_currency, date):
    """Get exchange rate with intelligent fallback logic"""
    # Implementation includes:
    # - Same currency returns 1.0
    # - Looks for direct rate
    # - Falls back to reverse rate (inverted)
    # - Returns None if not found
```

#### 2. AirBooking Model
**File:** `backend/apps/bookings/models.py`

**Added methods** (around line 240):
```python
def calculate_total_carbon(self):
    """Sum carbon emissions from all segments"""

def calculate_potential_savings(self):
    """Calculate savings if lowest fare was used"""

def save(self, *args, **kwargs):
    """Auto-calculate carbon and savings on save"""
    # Uses .update() to avoid infinite recursion
```

#### 3. AccommodationBooking Model
**File:** `backend/apps/bookings/models.py`

**Added methods** (around line 620):
```python
def convert_to_base_currency(self):
    """Convert nightly rate to organization's base currency"""

def save(self, *args, **kwargs):
    """Auto-convert currency on save"""
```

#### 4. CarHireBooking Model
**File:** `backend/apps/bookings/models.py`

**Added methods** (around line 765):
```python
def convert_to_base_currency(self):
    """Convert daily rate to organization's base currency"""

def save(self, *args, **kwargs):
    """Auto-convert currency on save"""
```

**Status:** ✅ IMPLEMENTED - Phase 1 complete

---

## Common Issues Resolved

### Issue 1: Circular Imports
**Problem:** Importing CurrencyExchangeRate at module level causes circular import errors.

**Solution:** Import inside methods instead:
```python
def convert_to_base_currency(self):
    from apps.reference_data.models import CurrencyExchangeRate
    rate = CurrencyExchangeRate.get_rate(...)
```

### Issue 2: Infinite Save Loops
**Problem:** Calling `self.save()` inside a `save()` method causes infinite recursion.

**Solution:** Use `.update()` instead:
```python
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    # Calculate something
    ModelName.objects.filter(pk=self.pk).update(field=calculated_value)
```

### Issue 3: Missing Exchange Rates
**Problem:** No exchange rate data returns None, causing conversion errors.

**Solution:** Check for None and use fallback:
```python
rate = CurrencyExchangeRate.get_rate(from_curr, to_curr, date)
if rate is None:
    logger.warning("No rate found, using 1:1 fallback")
    rate = Decimal('1.0')
```

---

## Testing Checklist

After any model changes, verify:

- [ ] Country fields are optional (`blank=True, null=True`)
- [ ] Can save bookings without country data
- [ ] AirBooking calculates carbon from segments
- [ ] AirBooking calculates potential savings
- [ ] AccommodationBooking converts currency
- [ ] CarHireBooking converts currency
- [ ] CurrencyExchangeRate.get_rate() works
- [ ] No circular import errors
- [ ] No infinite save loops
- [ ] Django admin saves work correctly

---

## Quick Test Commands

### Test Country Fields (Session 33 fix)
```python
from apps.bookings.models import CarHireBooking, AccommodationBooking

# Should work without country
car = CarHireBooking(
    rental_company="Test",
    pickup_city="Sydney",
    # country not provided - should still work!
)
```

### Test Currency Conversion (Session 34)
```python
from apps.bookings.models import AccommodationBooking
from apps.reference_data.models import CurrencyExchangeRate

# Test exchange rate lookup
rate = CurrencyExchangeRate.get_rate('USD', 'AUD', date.today())
print(f"Rate: {rate}")

# Test auto-conversion on save
acc = AccommodationBooking.objects.first()
acc.save()  # Should auto-convert
print(f"Base: {acc.nightly_rate_base}")
```

---

## Future Session Protocol

### At Start of Session
1. **Review this document** before making any model changes
2. **Check git diff** to see what changed since last session
3. **Ask about critical fixes** if uncertain

### During Session
1. **Mark new fixes** with session number in comments
2. **Update this document** with new critical fixes
3. **Test immediately** after each change

### At End of Session
1. **Update this document** with new fixes
2. **Create handover** with specific files/lines changed
3. **List what NOT to change** in next session

---

## File Version Markers

Add these markers to code to indicate critical sections:

```python
# =============================================================================
# SESSION 33 FIX: Country Fields - DO NOT REVERT TO REQUIRED
# =============================================================================
country = models.CharField(max_length=100, blank=True, null=True)

# =============================================================================
# SESSION 34 ENHANCEMENT: Automatic Currency Conversion
# =============================================================================
def convert_to_base_currency(self):
    ...
```

---

## Emergency Recovery

If critical fixes are accidentally reverted:

### Step 1: Check Git History
```bash
cd ~/Desktop/travel-analytics/backend
git log --oneline -10
git diff HEAD~1 apps/bookings/models.py
```

### Step 2: Restore from Git
```bash
git checkout HEAD~1 -- apps/bookings/models.py
```

### Step 3: Verify Fixes
- Check country fields are optional
- Check Phase 1 methods are present
- Run migrations if needed
- Restart server

---

## Contact & Support

If you encounter issues:
1. Share the specific error message
2. Note which model/operation is failing
3. Check this document for known fixes
4. Test in Django shell to isolate problem

---

**Last Updated:** Session 35  
**Status:** Active Reference Document  
**Importance:** 🔥 CRITICAL - Check before ANY model changes
