<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Service Fees Analytics</h1>
      <p class="mt-1 text-sm text-gray-500">Analyze booking fees, channels, and trends</p>
    </div>

    <!-- Universal Filters -->
    <UniversalFilters
      :show-traveller="false"
      :show-date-range="true"
      :show-destinations="false"
      :show-organization="true"
      :show-status="false"
      :show-supplier="false"
      @filters-changed="handleFiltersChanged"
    />

    <!-- View-Specific Filters -->
    <div class="bg-white rounded-xl shadow-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">Service Fee Filters</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Fee Type Filter -->
        <div>
          <label for="feeType" class="block text-sm font-medium text-gray-700 mb-2">Fee Type</label>
          <select
            id="feeType"
            v-model="viewFilters.feeType"
            class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="">All Fee Types</option>
            <option v-for="feeType in feeTypes" :key="feeType.value" :value="feeType.value">
              {{ feeType.label }}
            </option>
          </select>
        </div>

        <!-- Channel Filter -->
        <div>
          <label for="channel" class="block text-sm font-medium text-gray-700 mb-2">Channel</label>
          <select
            id="channel"
            v-model="viewFilters.channel"
            class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="">All Channels</option>
            <option value="Online">Online</option>
            <option value="Offline">Offline</option>
            <option value="Mobile">Mobile</option>
          </select>
        </div>

        <!-- Service Fee Description Search -->
        <div>
          <label for="description" class="block text-sm font-medium text-gray-700 mb-2">Description</label>
          <input
            id="description"
            v-model="viewFilters.description"
            type="text"
            placeholder="Search fee description..."
            class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
        </div>
      </div>
    </div>

      <!-- Stats Cards - Note the mb-6 class added -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <!-- Total Fees -->
        <div class="bg-white rounded-xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Total Fees</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                ${{ formatNumber(stats.totalFees) }}
              </p>
            </div>
            <div class="bg-blue-100 p-3 rounded-full">
              <svg class="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Total Transactions -->
        <div class="bg-white rounded-xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Total Transactions</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                {{ stats.totalTransactions }}
              </p>
            </div>
            <div class="bg-purple-100 p-3 rounded-full">
              <svg class="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Average Fee -->
        <div class="bg-white rounded-xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Average Fee</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                ${{ formatNumber(stats.avgFee) }}
              </p>
            </div>
            <div class="bg-green-100 p-3 rounded-full">
              <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Online Percentage -->
        <div class="bg-white rounded-xl shadow-sm p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Online %</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                {{ stats.onlinePercentage }}%
              </p>
            </div>
            <div class="bg-amber-100 p-3 rounded-full">
              <svg class="h-6 w-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Chart Components Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FeeTypeChart :filters="allFilters" />
        <FeeChannelChart :filters="allFilters" />
      </div>

      <FeeTrendChart :filters="allFilters" />

      <!-- Service Fees Table -->
      <div class="bg-white rounded-xl shadow-sm">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">Service Fee Records</h3>
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Booking Reference
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Traveller
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fee Type
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Channel
                </th>
                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="fee in paginatedFees" :key="fee.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ fee.booking?.booking_reference || 'N/A' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ fee.booking?.traveller_name || 'N/A' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ formatFeeType(fee.fee_type) }}
                </td>
                <td class="px-6 py-4 text-sm text-gray-900">
                  {{ fee.description || 'N/A' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <span v-if="fee.booking_channel === 'Online' || (fee.fee_type && fee.fee_type.includes('ONLINE'))" class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                    Online
                  </span>
                  <span v-else-if="fee.booking_channel === 'Mobile'" class="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">
                    Mobile
                  </span>
                  <span v-else class="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                    Offline
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                  {{ fee.currency || 'AUD' }} ${{ formatNumber(fee.fee_amount) }}
                </td>
              </tr>
              <tr v-if="paginatedFees.length === 0">
                <td colspan="6" class="px-6 py-8 text-center text-sm text-gray-500">
                  No service fees found
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-700">Rows per page:</span>
            <select v-model="itemsPerPage" class="border border-gray-300 rounded-md px-2 py-1 text-sm">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="30">30</option>
              <option :value="40">40</option>
              <option :value="50">50</option>
            </select>
          </div>

          <div class="flex items-center gap-4">
            <span class="text-sm text-gray-700">
              {{ startIndex + 1 }}-{{ endIndex }} of {{ serviceFees.length }}
            </span>
            <div class="flex gap-1">
              <button
                @click="currentPage--"
                :disabled="currentPage === 1"
                class="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                @click="currentPage++"
                :disabled="currentPage >= totalPages"
                class="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import UniversalFilters from '@/components/common/UniversalFilters.vue'
import FeeTypeChart from '@/components/fees/FeeTypeChart.vue'
import FeeChannelChart from '@/components/fees/FeeChannelChart.vue'
import FeeTrendChart from '@/components/fees/FeeTrendChart.vue'
import { transformFiltersForBackend } from '@/utils/filterTransformer'

// Universal filters from UniversalFilters component
const universalFilters = ref({})

// View-specific filters
const viewFilters = reactive({
  feeType: '',
  channel: '',
  description: '',
})

// Combined filters for API calls
const allFilters = computed(() => {
  return {
    ...universalFilters.value,
    ...viewFilters.value,
  }
})

// Stats
const stats = reactive({
  totalFees: 0,
  totalTransactions: 0,
  avgFee: 0,
  onlinePercentage: 0,
})

// Service fees data
const serviceFees = ref([])

// Fee types (loaded dynamically)
const feeTypes = ref([])

// Pagination
const currentPage = ref(1)
const itemsPerPage = ref(20)

// Computed pagination values
const totalPages = computed(() => {
  return Math.ceil(serviceFees.value.length / itemsPerPage.value)
})

const startIndex = computed(() => {
  return (currentPage.value - 1) * itemsPerPage.value
})

const endIndex = computed(() => {
  return Math.min(startIndex.value + itemsPerPage.value, serviceFees.value.length)
})

const paginatedFees = computed(() => {
  return serviceFees.value.slice(startIndex.value, endIndex.value)
})

// Watch pagination changes
watch(itemsPerPage, () => {
  currentPage.value = 1
})

// Handle UniversalFilters changes
const handleFiltersChanged = async (filters) => {
  console.log('📊 [ServiceFeesView] Universal filters changed:', filters)
  universalFilters.value = filters
  await loadStats()
}

// Format number helper
const formatNumber = (num) => {
  return new Intl.NumberFormat('en-AU').format(Math.round(num || 0))
}

// Load fee types from API
const loadFeeTypes = async () => {
  try {
    const response = await api.get('/service-fees/fee_type_choices/')
    feeTypes.value = response.data
    console.log('✅ Loaded fee types:', feeTypes.value)
  } catch (error) {
    console.error('Error loading fee types:', error)
    // Fallback to hardcoded values if API fails
    feeTypes.value = [
      { value: 'BOOKING_ONLINE_DOM', label: 'Online Booking - Domestic' },
      { value: 'BOOKING_ONLINE_INTL', label: 'Online Booking - International' },
      { value: 'BOOKING_OFFLINE_DOM', label: 'Offline Booking - Domestic' },
      { value: 'BOOKING_OFFLINE_INTL', label: 'Offline Booking - International' },
      { value: 'CHANGE_FEE', label: 'Change Fee' },
      { value: 'REFUND_FEE', label: 'Refund Fee' },
      { value: 'AFTER_HOURS', label: 'After Hours Fee' },
      { value: 'CONSULTATION', label: 'Consultation Fee' },
      { value: 'OTHER', label: 'Other Fee' }
    ]
  }
}

// Format fee type helper
const formatFeeType = (feeType) => {
  if (!feeType) return 'N/A'

  // Try to find the label from loaded fee types
  const feeTypeObj = feeTypes.value.find(ft => ft.value === feeType)
  if (feeTypeObj) return feeTypeObj.label

  // Fallback to hardcoded mapping
  const typeMap = {
    'BOOKING_ONLINE_DOM': 'Online Booking - Domestic',
    'BOOKING_ONLINE_INTL': 'Online Booking - International',
    'BOOKING_OFFLINE_DOM': 'Offline Booking - Domestic',
    'BOOKING_OFFLINE_INTL': 'Offline Booking - International',
    'CHANGE_FEE': 'Change Fee',
    'REFUND_FEE': 'Refund Fee',
    'AFTER_HOURS': 'After Hours Fee',
    'CONSULTATION': 'Consultation Fee',
    'OTHER': 'Other Fee'
  }

  return typeMap[feeType] || feeType
}

// Load stats
const loadStats = async () => {
  try {
    const params = transformFiltersForBackend(allFilters.value)

    // Add view-specific params
    if (viewFilters.feeType) params.fee_type = viewFilters.feeType
    if (viewFilters.channel) params.booking_channel = viewFilters.channel
    if (viewFilters.description) params.description = viewFilters.description

    console.log('🔍 [ServiceFeesView] Loading with params:', params)

    const response = await api.get('/service-fees/', { params })

    const fees = response.data.results || []

    // Store fees for table
    serviceFees.value = fees

    // Reset to first page when data changes
    currentPage.value = 1

    stats.totalTransactions = fees.length
    stats.totalFees = fees.reduce((sum, f) => sum + parseFloat(f.fee_amount || 0), 0)
    stats.avgFee = stats.totalTransactions > 0 ? Math.round(stats.totalFees / stats.totalTransactions) : 0

    // Calculate online percentage
    const onlineFees = fees.filter(f =>
      f.booking_channel === 'Online' || (f.fee_type && f.fee_type.includes('ONLINE'))
    ).length
    stats.onlinePercentage = stats.totalTransactions > 0
      ? Math.round((onlineFees / stats.totalTransactions) * 100)
      : 0
  } catch (error) {
    console.error('Error loading service fees stats:', error)
  }
}

// Watch view-specific filters
watch(viewFilters, () => {
  loadStats()
}, { deep: true })

// Load data on mount
onMounted(() => {
  loadFeeTypes()
  loadStats()
})
</script>