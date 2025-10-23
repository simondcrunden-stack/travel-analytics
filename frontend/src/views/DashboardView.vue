<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <!-- Page Header -->
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p class="mt-2 text-sm text-gray-600">
          Overview of your travel analytics and performance metrics
        </p>
      </div>

      <!-- Filters -->
      <DashboardFilters
        :date-range="filters.dateRange"
        :organization="filters.organization"
        :origin-country="filters.originCountry"
        :destination-country="filters.destinationCountry"
        :organizations="organizations"
        @update:filters="handleFilterChange"
      />

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
      </div>

      <!-- Error State -->
      <div
        v-else-if="error"
        class="rounded-lg bg-red-50 p-4 text-red-800"
      >
        {{ error }}
      </div>

      <!-- Dashboard Content -->
      <div v-else>
        <!-- Stat Cards Grid -->
        <div class="mb-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <!-- Total Spend -->
          <StatCard
            title="Total Travel Spend"
            :value="spendBreakdown.total"
            subtitle="All booking categories"
            :icon="mdiCurrencyUsd"
            type="primary"
            format="currency"
            :trend="5.2"
          />

          <!-- Air Travel -->
          <StatCard
            title="Air Travel"
            :value="spendBreakdown.air"
            :subtitle="`${airBookingsCount || 0} flights booked`"
            :icon="mdiAirplane"
            type="info"
            format="currency"
            :trend="3.8"
          />

          <!-- Accommodation -->
          <StatCard
            title="Accommodation"
            :value="spendBreakdown.accommodation"
            :subtitle="`${transactionSummary.hotel_nights || 0} hotel nights`"
            :icon="mdiBed"
            type="success"
            format="currency"
            :trend="-1.2"
          />

          <!-- Rental Cars -->
          <StatCard
            title="Rental Cars"
            :value="spendBreakdown.car"
            :subtitle="`${transactionSummary.car_hire_days || 0} rental days`"
            :icon="mdiCarSide"
            type="warning"
            format="currency"
            :trend="2.1"
          />

          <!-- Service Fees -->
          <StatCard
            title="Service Fees"
            :value="spendBreakdown.service_fees"
            :subtitle="`${transactionSummary.service_fees || 0} fees charged`"
            :icon="mdiRoomServiceOutline"
            type="default"
            format="currency"
          />

          <!-- Other Expenses -->
          <StatCard
            title="Other Expenses"
            :value="spendBreakdown.other"
            subtitle="Miscellaneous costs"
            :icon="mdiWalletTravel"
            type="default"
            format="currency"
          />
        </div>

        <!-- Transaction Summary Card -->
        <div class="mb-8 rounded-2xl bg-white p-6 shadow-sm">
          <h3 class="mb-4 text-lg font-semibold text-gray-900">Transaction Summary</h3>
          <div class="grid grid-cols-2 gap-6 sm:grid-cols-4">
            <div>
              <p class="text-sm font-medium text-gray-600">Total Bookings</p>
              <p class="mt-2 text-2xl font-bold text-gray-900">
                {{ spendBreakdown.bookings_count || 0 }}
              </p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-600">Hotel Nights</p>
              <p class="mt-2 text-2xl font-bold text-gray-900">
                {{ transactionSummary.hotel_nights || 0 }}
              </p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-600">Car Hire Days</p>
              <p class="mt-2 text-2xl font-bold text-gray-900">
                {{ transactionSummary.car_hire_days || 0 }}
              </p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-600">Service Fees</p>
              <p class="mt-2 text-2xl font-bold text-gray-900">
                {{ transactionSummary.service_fees || 0 }}
              </p>
            </div>
          </div>
        </div>

        <!-- Compliance Summary Card (NEW) -->
        <ComplianceSummary 
          ref="complianceSummaryRef"
          :filters="filters" 
          class="mb-8" 
        />

        <!-- Charts Grid (REPLACE PLACEHOLDER) -->
        <div class="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <MonthlySpendChart :filters="filters" />
          <ComplianceDonutChart :filters="filters" />
        </div>

        <!-- Top Travellers Table -->
        <TopTravellersTable :filters="filters" class="mb-8" />

        <!-- World Map Placeholder (Phase 4) -->
        <DestinationMap :filters="filters" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import ComplianceSummary from '@/components/dashboard/ComplianceSummary.vue'
import dashboardService from '@/services/dashboardService'
import bookingService from '@/services/bookingService'
import {
  mdiCurrencyUsd,
  mdiAirplane,
  mdiBed,
  mdiCarSide,
  mdiRoomServiceOutline,
  mdiWalletTravel,
  mdiEarth,
} from '@mdi/js'
import MonthlySpendChart from '@/components/dashboard/MonthlySpendChart.vue'
import ComplianceDonutChart from '@/components/dashboard/ComplianceDonutChart.vue'
import TopTravellersTable from '@/components/dashboard/TopTravellersTable.vue'
import DestinationMap from '@/components/dashboard/DestinationMap.vue'

// State
const loading = ref(false)
const error = ref(null)
const organizations = ref([])
const spendBreakdown = ref({
  total: 0,
  air: 0,
  accommodation: 0,
  car: 0,
  service_fees: 0,
  other: 0,
  bookings_count: 0,
})
const transactionSummary = ref({
  total_bookings: 0,
  hotel_nights: 0,
  car_hire_days: 0,
  service_fees: 0,
})

// Default date range: Last 3 months
const getDefaultDateRange = () => {
  const endDate = new Date()
  const startDate = new Date()
  startDate.setMonth(startDate.getMonth() - 3)
  return [startDate, endDate]
}

const filters = ref({
  dateRange: getDefaultDateRange(),
  organization: '',
  originCountry: '',
  destinationCountry: '',
})

const travelType = ref('')

// Computed
const airBookingsCount = computed(() => {
  if (!spendBreakdown.value || !spendBreakdown.value.bookings_count) {
    return 0
  }
  return Math.round(spendBreakdown.value.bookings_count * 0.5)
})

const complianceSummaryRef = ref(null)

// Methods
const handleFilterChange = (newFilters) => {
  filters.value = { ...newFilters }
  loadDashboardData()
  // Refresh compliance data
  if (complianceSummaryRef.value) {
    complianceSummaryRef.value.refresh()
  }
}

const loadDashboardData = async () => {
  try {
    loading.value = true
    error.value = null

    // Build API params
    const params = {}
    if (filters.value.dateRange && filters.value.dateRange.length === 2) {
      params.start_date = filters.value.dateRange[0].toISOString().split('T')[0]
      params.end_date = filters.value.dateRange[1].toISOString().split('T')[0]
    }
    if (filters.value.organization) {
      params.organization = filters.value.organization
    }

    // Load spend breakdown
    const breakdown = await dashboardService.getSpendBreakdown(params)
    spendBreakdown.value = breakdown

    // Load transaction summary
    const summary = await dashboardService.getTransactionSummary(params)
    transactionSummary.value = summary
  } catch (err) {
    console.error('Error loading dashboard data:', err)
    error.value = 'Failed to load dashboard data. Please try again.'
  } finally {
    loading.value = false
  }
}

const loadOrganizations = async () => {
  try {
    const orgs = await bookingService.getOrganizations()
    organizations.value = orgs
  } catch (err) {
    console.error('Error loading organizations:', err)
  }
}

// Lifecycle
onMounted(async () => {
  await loadOrganizations()
  await loadDashboardData()
})
</script>