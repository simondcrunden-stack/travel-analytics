# Travel Analytics - Current Project State
**Generated:** October 29, 2025 (Session 35)  
**Status:** Accurate snapshot from actual code files  
**Purpose:** Upload this at the start of EVERY Claude session

---

## 🎯 Critical Information

### Database: PostgreSQL
- **Name:** travel_analytics_db
- **User:** travel_analytics_user
- **Location:** localhost:5432

### Backend Stack
- Django 5.2.7
- Python 3.11
- Django REST Framework
- JWT Authentication

### Frontend Stack
- Vue.js 3 (Composition API)
- Pinia (state management)
- Vue Router (with auth guards)
- Tailwind CSS
- Chart.js + vue-chartjs

---

## 📊 Complete Database Schema

### 1. USERS APP

#### User Model
**Table:** `users`  
**Type:** Extended AbstractUser

```python
Fields:
- id: UUIDField (PK)
- username: CharField (inherited)
- email: EmailField (inherited, indexed)
- password: CharField (inherited)
- user_type: CharField(20) - ADMIN, AGENT_ADMIN, AGENT_USER, CUSTOMER_ADMIN, CUSTOMER_RISK, CUSTOMER
- phone: CharField(20)
- organization: FK → organizations.Organization
- is_active: BooleanField (inherited)
- date_joined: DateTimeField (inherited)

Indexes:
- email
- user_type
```

#### UserProfile Model
**Table:** `user_profiles`

```python
Fields:
- id: AutoField (PK)
- user: OneToOne → User
- home_country: CharField(2) - ISO 2-letter code
- default_filters: JSONField - saved dashboard preferences
- created_at: DateTimeField
- updated_at: DateTimeField

Auto-created via signal when User is created
```

---

### 2. ORGANIZATIONS APP

#### Organization Model
**Table:** `organizations`

```python
Fields:
- id: UUIDField (PK)
- name: CharField(200)
- org_type: CharField(20) - AGENT or CUSTOMER
- code: CharField(50, unique=True)
- contact_name: CharField(200)
- contact_position: CharField(100)
- contact_email: EmailField
- contact_phone: CharField(20)
- address: TextField
- business_number: CharField(50) - ABN/ACN
- ap_contact_name: CharField(200)
- ap_contact_email: EmailField
- ap_contact_phone: CharField(20)
- base_currency: CharField(3) - default 'AUD'
- home_country: CharField(3) - ISO alpha-3, default 'AUS' ✨ SESSION 29/35
- is_active: BooleanField
- subscription_status: CharField(20) - ACTIVE, TRIAL, SUSPENDED, CANCELLED
- subscription_start: DateField
- subscription_end: DateField
- travel_agent: FK → self (for customer orgs)
- created_at: DateTimeField
- updated_at: DateTimeField

Indexes:
- code
- org_type + is_active
- home_country ✨ NEW

Methods:
- is_domestic_travel(country_code) → bool
- get_home_country_display() → str
```

---

### 3. REFERENCE_DATA APP

#### Airport Model
**Table:** `airports`

```python
Fields:
- iata_code: CharField(3, PK)
- name: CharField(200)
- city: CharField(100)
- country: CharField(100)
- latitude: DecimalField(9,6)
- longitude: DecimalField(9,6)
- timezone: CharField(50)

Ordering: iata_code
```

#### Airline Model
**Table:** `airlines`

```python
Fields:
- iata_code: CharField(3, PK)
- name: CharField(200)
- country: CharField(100)
- alliance: CharField(50) - Star Alliance, OneWorld, etc.

Ordering: iata_code
```

#### CurrencyExchangeRate Model ✨ SESSION 34 ENHANCED
**Table:** `currency_exchange_rates`

```python
Fields:
- id: UUIDField (PK)
- from_currency: CharField(3) - e.g., USD, GBP, EUR
- to_currency: CharField(3) - e.g., AUD
- exchange_rate: DecimalField(12,6) - min 0.000001
- rate_date: DateField
- rate_source: CharField(100) - e.g., "Reserve Bank of Australia"
- created_at: DateTimeField
- updated_at: DateTimeField

Indexes:
- from_currency + to_currency + rate_date
- rate_date

Unique: from_currency + to_currency + rate_date
Ordering: -rate_date (newest first)

✨ ENHANCED METHODS (Session 34):
- get_rate(from_currency, to_currency, date) → Decimal
  * Returns 1.0 if same currency
  * Looks for exact date match
  * Falls back to most recent before date
  * Falls back to reverse rate (inverted)
  * Returns None if no rate found
  
- convert_amount(amount, from_currency, to_currency, date) → Decimal
  * Uses get_rate() to convert amount
  * Returns None if no rate available
```

#### Country Model ✨ SESSION 35 RESTORED
**Table:** `countries`

```python
Fields:
- alpha_3: CharField(3, PK) - ISO 3166-1 alpha-3 (AUS, NZL, USA)
- alpha_2: CharField(2, unique) - ISO 3166-1 alpha-2 (AU, NZ, US)
- numeric_code: CharField(3) - ISO 3166-1 numeric
- name: CharField(200) - Official name
- common_name: CharField(200) - Common name
- region: CharField(100) - Asia, Europe, Oceania, etc.
- subregion: CharField(100) - South-Eastern Asia, etc.
- currency_code: CharField(3) - ISO 4217 (AUD, USD, EUR)
- phone_prefix: CharField(10) - +61, +64, etc.
- is_active: BooleanField - default True
- created_at: DateTimeField
- updated_at: DateTimeField

Indexes:
- region
- subregion
- is_active

Ordering: name
Current Count: 24 countries

Methods:
- is_domestic_for_organization(organization) → bool
  * Returns True if country matches org's home_country
  * Multi-tenant design - no static is_domestic field

NOTE: This model was accidentally removed and restored in Session 35
```

#### HotelChain Model
**Table:** `hotel_chains`

```python
Fields:
- id: UUIDField (PK)
- name: CharField(200)
- alternative_names: TextField - comma-separated
- website: URLField
- is_preferred: BooleanField
- tier: CharField(20) - PREFERRED, APPROVED, STANDARD
- is_active: BooleanField
- has_corporate_rate: BooleanField
- corporate_discount_percentage: DecimalField(5,2) - % off BAR
- account_manager_name: CharField(200)
- account_manager_email: EmailField
- account_manager_phone: CharField(50)
- contract_start_date: DateField
- contract_end_date: DateField
- notes: TextField
- created_at: DateTimeField
- updated_at: DateTimeField

Ordering: name
```

#### CarRentalCompany Model
**Table:** `car_rental_companies`

```python
Fields:
- id: UUIDField (PK)
- name: CharField(200)
- alternative_names: TextField - comma-separated
- website: URLField
- is_preferred: BooleanField
- tier: CharField(20) - PREFERRED, APPROVED, STANDARD
- is_active: BooleanField
- has_corporate_rate: BooleanField
- corporate_discount_percentage: DecimalField(5,2) - average %
- account_manager_name: CharField(200)
- account_manager_email: EmailField
- account_manager_phone: CharField(50)
- contract_start_date: DateField
- contract_end_date: DateField
- notes: TextField
- created_at: DateTimeField
- updated_at: DateTimeField

Ordering: name
```

---

## 🔗 Key Relationships

```
Organization (1) ←→ (Many) User
Organization (1) ←→ (Many) Organization (customers)
Organization (1) ←→ (Many) Traveller
Organization (1) ←→ (Many) Booking

User (1) ←→ (1) UserProfile (auto-created)
User (1) ←→ (0..1) Traveller

Booking (1) ←→ (Many) AirBooking
Booking (1) ←→ (Many) AccommodationBooking
Booking (1) ←→ (Many) CarHireBooking

AirBooking (1) ←→ (Many) AirSegment

Airport (referenced by) → AirSegment.origin, AirSegment.destination
Airline (referenced by) → AirSegment.airline_iata_code
Country (referenced by) → Organization.home_country
CurrencyExchangeRate (used by) → Booking conversions
```

---

## ✅ Current Data State

**Organizations:** 3
- 1 Travel Agent (Global Travel Partners)
- 2 Customer Organizations (TechCorp Australia, Retail Solutions Group)

**Users:** 6+
- Platform admins
- Agent admins
- Customer admins and users

**Travellers:** 8
- Across multiple organizations
- Some linked to User accounts

**Bookings:** 15
- 7 Air bookings
- 3 Accommodation bookings
- 1 Car hire booking

**Reference Data:**
- 24 Countries (Session 35)
- 10 Airports
- 8 Airlines
- Multiple exchange rates
- Hotel chains and car rental companies

---

## 🚨 Critical Fields & Fixes

### Session 33 Fix - DO NOT REVERT
```python
# AccommodationBooking.country
country = models.CharField(max_length=100, blank=True, null=True)

# CarHireBooking.country  
country = models.CharField(max_length=100, blank=True, null=True)

# These MUST remain optional (blank=True, null=True)
```

### Session 34 Phase 1 - Applied
```python
# AirBooking - New fields added
base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
currency = models.CharField(max_length=3, default='AUD')
fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
total_carbon_kg = DecimalField(10,2, null=True, blank=True)

# CurrencyExchangeRate - Enhanced get_rate() method with fallbacks
```

### Session 35 Fix - Country Model Restored
```python
# Country model was accidentally removed from models.py
# It has been restored with all fields and methods
# Do NOT remove this model again
```

---

## 📁 File Structure

```
backend/
├── apps/
│   ├── users/
│   │   ├── models.py ✅ (User, UserProfile)
│   │   └── admin.py
│   ├── organizations/
│   │   ├── models.py ✅ (Organization with home_country)
│   │   └── admin.py
│   ├── reference_data/
│   │   ├── models.py ✅ (Airport, Airline, Currency, Country, Hotels, Cars)
│   │   └── admin.py
│   ├── bookings/
│   │   ├── models.py (Traveller, Booking, Air/Hotel/Car bookings)
│   │   └── admin.py
│   └── api/
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
└── backend/
    └── settings.py
```

---

## 🎯 What This Document Is For

**At the start of EVERY Claude session:**
1. Upload this file FIRST
2. Upload SESSION_35_CRITICAL_FIXES_DO_NOT_REVERT.md SECOND
3. Upload the latest session handover document THIRD

**This ensures Claude knows:**
- ✅ Exact structure of all models
- ✅ Current field names and types
- ✅ What's optional vs required
- ✅ All relationships
- ✅ Recent changes and fixes
- ✅ What NOT to change

---

## 🔄 Updating This Document

When you make model changes:
1. Update the relevant section in this document
2. Note the session number
3. Mark with ✨ for new features
4. Mark with 🚨 for critical fixes
5. Upload the updated version at next session start

---

**Last Updated:** Session 35 (October 29, 2025)  
**Next Update:** When models change  
**Status:** ✅ Accurate and complete
