<template>
  <div class="bg-white rounded-xl shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200 bg-gray-50">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-gray-900">Top Routes & Destinations</h3>
          <p class="text-sm text-gray-500 mt-1">Most popular travel routes and destinations</p>
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
        <p class="text-sm text-gray-500 mt-2">Loading routes data...</p>
      </div>

      <!-- No Data -->
      <div v-else-if="!loading && (!routesData || !routesData.top_routes || routesData.top_routes.length === 0)" class="px-6 py-8 text-center">
        <span class="mdi mdi-airplane-off text-4xl text-gray-300"></span>
        <p class="text-sm text-gray-500 mt-2">No route data available</p>
      </div>

      <!-- Data Display -->
      <div v-else class="p-6">
        <!-- Tab Selection -->
        <div class="flex gap-2 mb-6 border-b border-gray-200">
          <button
            @click="activeTab = 'routes'"
            :class="activeTab === 'routes' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
            class="px-4 py-2 border-b-2 font-medium text-sm transition-colors"
          >
            Top Routes
          </button>
          <button
            @click="activeTab = 'destinations'"
            :class="activeTab === 'destinations' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
            class="px-4 py-2 border-b-2 font-medium text-sm transition-colors"
          >
            Top Destinations
          </button>
          <button
            @click="activeTab = 'airports'"
            :class="activeTab === 'airports' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
            class="px-4 py-2 border-b-2 font-medium text-sm transition-colors"
          >
            Top Destinations
          </button>
        </div>

        <!-- Top Routes Table -->
        <div v-if="activeTab === 'routes'" class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Route</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Trips</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Travellers</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Spend</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg/Trip</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="(route, index) in routesData.top_routes" :key="route.route" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap">
                  <span
                    class="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold"
                    :class="getRankClass(index)"
                  >
                    {{ index + 1 }}
                  </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap">
                  <div class="font-medium text-gray-900">{{ route.route }}</div>
                  <div class="text-xs text-gray-500 mt-1">
                    {{ route.airport1_city }} ⇄ {{ route.airport2_city }}
                  </div>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900 font-medium">
                  {{ route.trips }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                  {{ route.unique_travellers }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                  {{ formatCurrency(route.total_spend) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                  {{ formatCurrency(route.avg_spend_per_trip) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Top Destinations Table -->
        <div v-else-if="activeTab === 'destinations'" class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Country</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Trips</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Travellers</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Spend</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg/Trip</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="(dest, index) in routesData.top_destinations" :key="dest.country" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap">
                  <span
                    class="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold"
                    :class="getRankClass(index)"
                  >
                    {{ index + 1 }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <div class="font-medium text-gray-900">{{ dest.country }}</div>
                  <div class="text-xs text-gray-500 mt-1">{{ dest.cities }}</div>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900 font-medium">
                  {{ dest.trips }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                  {{ dest.unique_travellers }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                  {{ formatCurrency(dest.total_spend) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                  {{ formatCurrency(dest.avg_spend_per_trip) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Top Destination Airports Table -->
        <div v-else-if="activeTab === 'airports'" class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Destination</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Trips</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Travellers</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Spend</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg/Trip</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="(airport, index) in routesData.top_destination_airports" :key="airport.airport" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap">
                  <span
                    class="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold"
                    :class="getRankClass(index)"
                  >
                    {{ index + 1 }}
                  </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap">
                  <div class="font-medium text-gray-900">{{ airport.airport }}</div>
                  <div class="text-xs text-gray-500 mt-1">{{ airport.city }}, {{ airport.country }}</div>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900 font-medium">
                  {{ airport.trips }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                  {{ airport.unique_travellers }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-900">
                  {{ formatCurrency(airport.total_spend) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                  {{ formatCurrency(airport.avg_spend_per_trip) }}
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
import { ref, watch } from 'vue'
import bookingService from '@/services/bookingService'

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({})
  }
})

const loading = ref(false)
const showSection = ref(true)
const activeTab = ref('routes')
const routesData = ref(null)

// Load routes data
const loadRoutesData = async () => {
  loading.value = true

  try {
    const data = await bookingService.getTopRoutesDestinations({
      ...props.filters,
      limit: 10
    })
    routesData.value = data

    console.log('✅ [TopRoutesWidget] Loaded routes data:', data)
  } catch (error) {
    console.error('❌ [TopRoutesWidget] Error loading routes data:', error)
    routesData.value = null
  } finally {
    loading.value = false
  }
}

// Watch for filter changes
watch(() => props.filters, () => {
  loadRoutesData()
}, { immediate: true, deep: true })

// Helper functions
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount || 0)
}

const getRankClass = (index) => {
  if (index === 0) return 'bg-yellow-400 text-yellow-900'
  if (index === 1) return 'bg-gray-400 text-gray-900'
  if (index === 2) return 'bg-orange-400 text-orange-900'
  return 'bg-gray-200 text-gray-700'
}
</script>
