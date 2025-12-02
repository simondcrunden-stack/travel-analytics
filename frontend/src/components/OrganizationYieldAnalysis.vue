<template>
  <div class="bg-white rounded-xl shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-blue-50">
      <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <span class="mdi mdi-office-building text-indigo-600"></span>
        Organization Yield Analysis
      </h3>
      <p class="text-sm text-gray-600 mt-1">Revenue and booking metrics by customer organization</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="p-8 text-center">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      <p class="mt-2 text-gray-600">Loading organization data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-6">
      <div class="bg-red-50 border border-red-200 rounded-lg p-4">
        <p class="text-red-800">{{ error }}</p>
      </div>
    </div>

    <!-- Data Display -->
    <div v-else-if="data" class="p-6">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <div class="bg-indigo-50 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-indigo-600 font-medium">Total Organizations</p>
              <p class="text-2xl font-bold text-indigo-900">{{ data.organization_count }}</p>
            </div>
            <span class="mdi mdi-domain text-3xl text-indigo-400"></span>
          </div>
        </div>

        <div class="bg-blue-50 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-blue-600 font-medium">Total Bookings</p>
              <p class="text-2xl font-bold text-blue-900">{{ data.totals?.total_bookings || 0 }}</p>
            </div>
            <span class="mdi mdi-briefcase text-3xl text-blue-400"></span>
          </div>
        </div>

        <div class="bg-purple-50 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-purple-600 font-medium">Booking Value</p>
              <p class="text-2xl font-bold text-purple-900">{{ formatCurrency(data.totals?.total_booking_value || 0) }}</p>
            </div>
            <span class="mdi mdi-cash-multiple text-3xl text-purple-400"></span>
          </div>
        </div>

        <div class="bg-green-50 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-green-600 font-medium">Total Revenue</p>
              <p class="text-2xl font-bold text-green-900">{{ formatCurrency(data.totals?.total_revenue || 0) }}</p>
            </div>
            <span class="mdi mdi-currency-usd text-3xl text-green-400"></span>
          </div>
        </div>

        <div class="bg-cyan-50 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-cyan-600 font-medium">Avg Yield</p>
              <p class="text-2xl font-bold text-cyan-900">{{ ((data.totals?.total_revenue || 0) / (data.totals?.total_booking_value || 1) * 100).toFixed(1) }}%</p>
            </div>
            <span class="mdi mdi-percent text-3xl text-cyan-400"></span>
          </div>
        </div>

        <div class="bg-orange-50 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-orange-600 font-medium">Online Bookings</p>
              <p class="text-2xl font-bold text-orange-900">{{ data.totals?.overall_online_percentage?.toFixed(1) || 0 }}%</p>
            </div>
            <span class="mdi mdi-laptop text-3xl text-orange-400"></span>
          </div>
        </div>
      </div>

      <!-- Organization Table -->
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" @click="sortBy('organization_name')">
                Organization
                <span v-if="sortField === 'organization_name'" class="mdi" :class="sortAscending ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th scope="col" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" @click="sortBy('booking_count')">
                Bookings
                <span v-if="sortField === 'booking_count'" class="mdi" :class="sortAscending ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th scope="col" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" @click="sortBy('unique_travellers')">
                Travellers
                <span v-if="sortField === 'unique_travellers'" class="mdi" :class="sortAscending ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th scope="col" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" @click="sortBy('total_booking_value')">
                Booking Value
                <span v-if="sortField === 'total_booking_value'" class="mdi" :class="sortAscending ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th scope="col" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" @click="sortBy('total_revenue')">
                Total Revenue
                <span v-if="sortField === 'total_revenue'" class="mdi" :class="sortAscending ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th scope="col" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" @click="sortBy('yield_percentage')">
                Yield %
                <span v-if="sortField === 'yield_percentage'" class="mdi" :class="sortAscending ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th scope="col" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" @click="sortBy('revenue_per_booking')">
                Rev/Booking
                <span v-if="sortField === 'revenue_per_booking'" class="mdi" :class="sortAscending ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th scope="col" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" @click="sortBy('hotel_booking_count')">
                Hotel Bookings
                <span v-if="sortField === 'hotel_booking_count'" class="mdi" :class="sortAscending ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th scope="col" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" @click="sortBy('online_percentage')">
                Online %
                <span v-if="sortField === 'online_percentage'" class="mdi" :class="sortAscending ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
              <th scope="col" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" @click="sortBy('modification_percentage')">
                Changes
                <span v-if="sortField === 'modification_percentage'" class="mdi" :class="sortAscending ? 'mdi-arrow-up' : 'mdi-arrow-down'"></span>
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="org in sortedOrganizations" :key="org.organization_id" class="hover:bg-gray-50">
              <td class="px-4 py-3 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="flex-shrink-0 h-8 w-8 bg-indigo-100 rounded-full flex items-center justify-center">
                    <span class="mdi mdi-domain text-indigo-600 text-lg"></span>
                  </div>
                  <div class="ml-3">
                    <div class="text-sm font-medium text-gray-900">{{ org.organization_name }}</div>
                    <div class="text-xs text-gray-500">{{ org.organization_type }}</div>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                {{ org.booking_count }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                {{ org.unique_travellers }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                {{ formatCurrency(org.total_booking_value) }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-right text-sm font-semibold text-green-600">
                {{ formatCurrency(org.total_revenue) }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-right text-sm font-semibold text-blue-600">
                {{ org.yield_percentage?.toFixed(1) || 0 }}%
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                {{ formatCurrency(org.revenue_per_booking) }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                {{ org.hotel_booking_count }}
                <span class="text-xs text-gray-500">({{ org.total_nights }}n)</span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-right text-sm">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium" :class="getOnlinePercentageClass(org.online_percentage)">
                  {{ org.online_percentage }}%
                </span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                {{ org.modification_percentage }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- No Data -->
      <div v-if="!data.organizations || data.organizations.length === 0" class="text-center py-12">
        <span class="mdi mdi-office-building-outline text-6xl text-gray-300"></span>
        <p class="mt-2 text-gray-500">No organization data available for the selected period</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import bookingService from '@/services/bookingService'

const props = defineProps({
  organization: {
    type: String,
    default: null
  },
  startDate: {
    type: String,
    default: null
  },
  endDate: {
    type: String,
    default: null
  }
})

const data = ref(null)
const loading = ref(false)
const error = ref(null)
const sortField = ref('total_revenue')
const sortAscending = ref(false)

const loadData = async () => {
  loading.value = true
  error.value = null

  try {
    const params = {}
    if (props.organization) params.organization = props.organization
    if (props.startDate) params.travel_date_after = props.startDate
    if (props.endDate) params.travel_date_before = props.endDate

    data.value = await bookingService.getOrganizationYieldAnalysis(params)
  } catch (err) {
    console.error('Error loading organization yield data:', err)
    error.value = 'Failed to load organization yield analysis data'
  } finally {
    loading.value = false
  }
}

const sortBy = (field) => {
  if (sortField.value === field) {
    sortAscending.value = !sortAscending.value
  } else {
    sortField.value = field
    sortAscending.value = false
  }
}

const sortedOrganizations = computed(() => {
  if (!data.value?.organizations) return []

  const organizations = [...data.value.organizations]
  organizations.sort((a, b) => {
    let aVal = a[sortField.value]
    let bVal = b[sortField.value]

    // Handle string comparisons
    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase()
      bVal = bVal.toLowerCase()
    }

    if (sortAscending.value) {
      return aVal > bVal ? 1 : -1
    } else {
      return aVal < bVal ? 1 : -1
    }
  })

  return organizations
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value || 0)
}

const getOnlinePercentageClass = (percentage) => {
  if (percentage >= 70) return 'bg-green-100 text-green-800'
  if (percentage >= 40) return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

// Watch for prop changes
watch([() => props.organization, () => props.startDate, () => props.endDate], loadData, { immediate: true })
</script>
