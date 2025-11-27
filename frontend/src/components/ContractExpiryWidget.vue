<template>
  <div class="bg-white rounded-xl shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200 bg-gray-50">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-gray-900">Contract Expiry Alerts</h3>
          <p class="text-sm text-gray-500 mt-1">Preferred supplier contracts expiring soon</p>
        </div>
        <button
          @click="showSection = !showSection"
          class="text-gray-400 hover:text-gray-600"
        >
          <span class="mdi" :class="showSection ? 'mdi-chevron-up' : 'mdi-chevron-down'" style="font-size: 24px;"></span>
        </button>
      </div>
    </div>

    <!-- Content -->
    <div v-if="showSection">
      <!-- Loading State -->
      <div v-if="loading" class="px-6 py-8 text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p class="text-sm text-gray-500 mt-2">Loading contract expiry data...</p>
      </div>

      <!-- No Organization Selected -->
      <div v-else-if="!organization" class="px-6 py-8 text-center">
        <span class="mdi mdi-information-outline text-4xl text-gray-300"></span>
        <p class="text-sm text-gray-500 mt-2">Select an organization to view contract expiry alerts</p>
      </div>

      <!-- No Expiring Contracts -->
      <div v-else-if="!loading && Array.isArray(expiringContracts) && expiringContracts.length === 0" class="px-6 py-8 text-center">
        <span class="mdi mdi-check-circle text-4xl text-green-500"></span>
        <p class="text-sm text-gray-600 mt-2 font-medium">No contracts expiring in the next 90 days</p>
        <p class="text-xs text-gray-500 mt-1">All supplier contracts are in good standing</p>
      </div>

      <!-- Expiring Contracts -->
      <div v-else-if="!loading && Array.isArray(expiringContracts) && expiringContracts.length > 0" class="p-6 space-y-6">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-red-600 font-medium uppercase">Critical (< 30 days)</p>
                <p class="text-2xl font-bold text-red-700 mt-1">{{ criticalCount }}</p>
              </div>
              <span class="mdi mdi-alert-circle text-3xl text-red-500"></span>
            </div>
          </div>

          <div class="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-amber-600 font-medium uppercase">Warning (30-60 days)</p>
                <p class="text-2xl font-bold text-amber-700 mt-1">{{ warningCount }}</p>
              </div>
              <span class="mdi mdi-alert text-3xl text-amber-500"></span>
            </div>
          </div>

          <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-yellow-600 font-medium uppercase">Upcoming (60-90 days)</p>
                <p class="text-2xl font-bold text-yellow-700 mt-1">{{ upcomingCount }}</p>
              </div>
              <span class="mdi mdi-information text-3xl text-yellow-500"></span>
            </div>
          </div>
        </div>

        <!-- Contracts Table -->
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Supplier</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Market</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Date</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Days Left</th>
                <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Urgency</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="contract in sortedContracts" :key="`${contract.type}-${contract.id}`" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap">
                  <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium" :class="getTypeClass(contract.type)">
                    <span class="mdi" :class="getTypeIcon(contract.type)" style="font-size: 14px; margin-right: 4px;"></span>
                    {{ contract.type }}
                  </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ contract.name }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                  {{ contract.market }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                  {{ formatDate(contract.contract_end_date) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right font-medium">
                  {{ contract.daysRemaining }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-center">
                  <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium" :class="getUrgencyClass(contract.daysRemaining)">
                    {{ getUrgencyText(contract.daysRemaining) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import preferredAirlineService from '@/services/preferredAirlineService'
import preferredHotelService from '@/services/preferredHotelService'
import preferredCarHireService from '@/services/preferredCarHireService'

const props = defineProps({
  organization: {
    type: String,
    default: null
  }
})

const loading = ref(false)
const showSection = ref(true)
const expiringContracts = ref([])

// Computed counts
const criticalCount = computed(() => {
  if (!Array.isArray(expiringContracts.value)) return 0
  return expiringContracts.value.filter(c => c.daysRemaining < 30).length
})
const warningCount = computed(() => {
  if (!Array.isArray(expiringContracts.value)) return 0
  return expiringContracts.value.filter(c => c.daysRemaining >= 30 && c.daysRemaining < 60).length
})
const upcomingCount = computed(() => {
  if (!Array.isArray(expiringContracts.value)) return 0
  return expiringContracts.value.filter(c => c.daysRemaining >= 60).length
})

// Sorted contracts (most urgent first)
const sortedContracts = computed(() => {
  if (!Array.isArray(expiringContracts.value)) return []
  return [...expiringContracts.value].sort((a, b) => a.daysRemaining - b.daysRemaining)
})

// Watch for organization changes
watch(() => props.organization, () => {
  loadExpiringContracts()
}, { immediate: true })

// Load expiring contracts from all three supplier types
const loadExpiringContracts = async () => {
  if (!props.organization) {
    expiringContracts.value = []
    return
  }

  try {
    loading.value = true
    const params = { organization: props.organization }

    // Load from all three supplier types in parallel (90 days)
    const [airlines, hotels, carHire] = await Promise.all([
      preferredAirlineService.getExpiringSoon(90, params).catch(() => []),
      preferredHotelService.getExpiringSoon(90, params).catch(() => []),
      preferredCarHireService.getExpiringSoon(90, params).catch(() => [])
    ])

    // Transform and combine all contracts
    const allContracts = [
      ...transformAirlineContracts(airlines),
      ...transformHotelContracts(hotels),
      ...transformCarHireContracts(carHire)
    ]

    expiringContracts.value = allContracts

    console.log('✅ [ContractExpiryWidget] Loaded expiring contracts:', {
      airlines: airlines.length,
      hotels: hotels.length,
      carHire: carHire.length,
      total: allContracts.length
    })

  } catch (error) {
    console.error('❌ [ContractExpiryWidget] Error loading expiring contracts:', error)
    expiringContracts.value = []
  } finally {
    loading.value = false
  }
}

// Transform airline contracts
const transformAirlineContracts = (contracts) => {
  return contracts.map(c => ({
    ...c,
    type: 'AIR',
    name: c.airline_name,
    market: c.market_type_display || c.market_type,
    daysRemaining: calculateDaysRemaining(c.contract_end_date)
  }))
}

// Transform hotel contracts
const transformHotelContracts = (contracts) => {
  return contracts.map(c => ({
    ...c,
    type: 'HOTEL',
    name: c.hotel_chain_name || c.hotel_name,
    market: c.location_display || `${c.city}, ${c.country}`,
    daysRemaining: calculateDaysRemaining(c.contract_end_date)
  }))
}

// Transform car hire contracts
const transformCarHireContracts = (contracts) => {
  return contracts.map(c => ({
    ...c,
    type: 'CAR',
    name: c.supplier_name,
    market: c.market_display || c.market,
    daysRemaining: calculateDaysRemaining(c.contract_end_date)
  }))
}

// Calculate days remaining until contract end
const calculateDaysRemaining = (endDate) => {
  const today = new Date()
  const end = new Date(endDate)
  const diffTime = end - today
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return Math.max(0, diffDays)
}

// Helper functions
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getTypeClass = (type) => {
  const classes = {
    'AIR': 'bg-blue-100 text-blue-800',
    'HOTEL': 'bg-purple-100 text-purple-800',
    'CAR': 'bg-green-100 text-green-800'
  }
  return classes[type] || 'bg-gray-100 text-gray-800'
}

const getTypeIcon = (type) => {
  const icons = {
    'AIR': 'mdi-airplane',
    'HOTEL': 'mdi-bed',
    'CAR': 'mdi-car'
  }
  return icons[type] || 'mdi-file-document'
}

const getUrgencyClass = (days) => {
  if (days < 30) return 'bg-red-100 text-red-800'
  if (days < 60) return 'bg-amber-100 text-amber-800'
  return 'bg-yellow-100 text-yellow-800'
}

const getUrgencyText = (days) => {
  if (days < 30) return 'Critical'
  if (days < 60) return 'Warning'
  return 'Upcoming'
}
</script>
