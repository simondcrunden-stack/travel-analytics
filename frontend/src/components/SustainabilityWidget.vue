<template>
  <div class="bg-white rounded-xl shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-green-50 to-emerald-50">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <span class="mdi mdi-leaf text-green-600" style="font-size: 24px;"></span>
            Sustainability Dashboard
          </h3>
          <p class="text-sm text-gray-500 mt-1">Carbon footprint and environmental impact tracking</p>
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
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
        <p class="text-sm text-gray-500 mt-2">Loading sustainability data...</p>
      </div>

      <!-- No Data -->
      <div v-else-if="!loading && !sustainabilityData" class="px-6 py-8 text-center">
        <span class="mdi mdi-leaf-off text-4xl text-gray-300"></span>
        <p class="text-sm text-gray-500 mt-2">No sustainability data available</p>
      </div>

      <!-- Data Display -->
      <div v-else class="p-6 space-y-6">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- Total Emissions -->
          <div class="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-green-700 font-medium uppercase">Total Emissions</p>
                <p class="text-2xl font-bold text-green-900 mt-1">{{ sustainabilityData.summary.total_emissions_tonnes }}</p>
                <p class="text-xs text-green-600 mt-0.5">tonnes CO₂</p>
              </div>
              <span class="mdi mdi-cloud text-3xl text-green-600"></span>
            </div>
          </div>

          <!-- Domestic Emissions -->
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-blue-700 font-medium uppercase">Domestic</p>
                <p class="text-2xl font-bold text-blue-900 mt-1">{{ formatWeight(sustainabilityData.summary.domestic_emissions_kg) }}</p>
                <p class="text-xs text-blue-600 mt-0.5">kg CO₂</p>
              </div>
              <span class="mdi mdi-home-map-marker text-3xl text-blue-600"></span>
            </div>
          </div>

          <!-- International Emissions -->
          <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-purple-700 font-medium uppercase">International</p>
                <p class="text-2xl font-bold text-purple-900 mt-1">{{ formatWeight(sustainabilityData.summary.international_emissions_kg) }}</p>
                <p class="text-xs text-purple-600 mt-0.5">kg CO₂</p>
              </div>
              <span class="mdi mdi-earth text-3xl text-purple-600"></span>
            </div>
          </div>

          <!-- Carbon Efficiency -->
          <div class="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-amber-700 font-medium uppercase">Efficiency</p>
                <p class="text-2xl font-bold text-amber-900 mt-1">{{ sustainabilityData.summary.carbon_efficiency.toFixed(2) }}</p>
                <p class="text-xs text-amber-600 mt-0.5">kg CO₂ per $</p>
              </div>
              <span class="mdi mdi-speedometer text-3xl text-amber-600"></span>
            </div>
          </div>
        </div>

        <!-- Emissions Breakdown Chart -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <h4 class="text-sm font-semibold text-gray-900 mb-4">Emissions Breakdown</h4>
          <div class="h-64">
            <canvas ref="emissionsBreakdownChart"></canvas>
          </div>
        </div>

        <!-- Monthly Trend Chart -->
        <div v-if="sustainabilityData.monthly_trend && sustainabilityData.monthly_trend.length > 0" class="bg-white rounded-lg border border-gray-200 p-6">
          <h4 class="text-sm font-semibold text-gray-900 mb-4">Monthly Emissions Trend</h4>
          <div class="h-64">
            <canvas ref="monthlyTrendChart"></canvas>
          </div>
        </div>

        <!-- Top Carbon Emitters -->
        <div v-if="sustainabilityData.top_emitters && sustainabilityData.top_emitters.length > 0" class="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h4 class="text-sm font-semibold text-gray-900">Top Carbon Emitters</h4>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Traveller</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total CO₂ (kg)</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Trips</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg per Trip</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="(emitter, index) in sustainabilityData.top_emitters" :key="emitter.traveller_id" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span
                      class="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold"
                      :class="getRankClass(index)"
                    >
                      {{ index + 1 }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ emitter.traveller_name }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 font-medium">
                    {{ formatWeight(emitter.carbon_kg) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-600">
                    {{ emitter.trips }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-600">
                    {{ formatWeight(emitter.avg_carbon_per_trip) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Top Routes by Emissions -->
        <div v-if="sustainabilityData.top_routes_by_emissions && sustainabilityData.top_routes_by_emissions.length > 0" class="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h4 class="text-sm font-semibold text-gray-900">Highest Emission Routes</h4>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Route</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total CO₂ (kg)</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Trips</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg per Trip</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="(route, index) in sustainabilityData.top_routes_by_emissions" :key="route.route" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span
                      class="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold"
                      :class="getRankClass(index)"
                    >
                      {{ index + 1 }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ route.route }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 font-medium">
                    {{ formatWeight(route.carbon_kg) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-600">
                    {{ route.trips }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-600">
                    {{ formatWeight(route.avg_carbon_per_trip) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'
import bookingService from '@/services/bookingService'

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({})
  }
})

const loading = ref(false)
const showSection = ref(true)
const sustainabilityData = ref(null)

// Chart refs
const emissionsBreakdownChart = ref(null)
const monthlyTrendChart = ref(null)
let emissionsBreakdownChartInstance = null
let monthlyTrendChartInstance = null

// Load sustainability data
const loadSustainabilityData = async () => {
  loading.value = true

  try {
    const data = await bookingService.getSustainabilityAnalytics(props.filters)
    sustainabilityData.value = data

    console.log('✅ [SustainabilityWidget] Loaded sustainability data:', data)

    // Render charts after data loads - use setTimeout to ensure DOM is ready
    await nextTick()
    await nextTick() // Double nextTick for Chart.js
    setTimeout(() => {
      renderCharts()
    }, 100)
  } catch (error) {
    console.error('❌ [SustainabilityWidget] Error loading sustainability data:', error)
    sustainabilityData.value = null
  } finally {
    loading.value = false
  }
}

// Render charts
const renderCharts = () => {
  if (!sustainabilityData.value) {
    console.log('⚠️ [SustainabilityWidget] No data available for charts')
    return
  }

  console.log('🎨 [SustainabilityWidget] Rendering charts with data:', {
    domestic: sustainabilityData.value.summary.domestic_emissions_kg,
    international: sustainabilityData.value.summary.international_emissions_kg,
    monthlyTrendPoints: sustainabilityData.value.monthly_trend?.length || 0
  })

  // Emissions Breakdown Chart
  if (emissionsBreakdownChartInstance) {
    emissionsBreakdownChartInstance.destroy()
  }

  if (emissionsBreakdownChart.value) {
    const ctx = emissionsBreakdownChart.value.getContext('2d')
    console.log('📊 [SustainabilityWidget] Creating emissions breakdown chart')
    emissionsBreakdownChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Domestic', 'International'],
        datasets: [{
          data: [
            sustainabilityData.value.summary.domestic_emissions_kg,
            sustainabilityData.value.summary.international_emissions_kg
          ],
          backgroundColor: ['#3b82f6', '#a855f7']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || ''
                const value = context.parsed || 0
                return `${label}: ${formatWeight(value)} kg CO₂`
              }
            }
          }
        }
      }
    })
  }

  // Monthly Trend Chart
  if (monthlyTrendChartInstance) {
    monthlyTrendChartInstance.destroy()
  }

  if (monthlyTrendChart.value && sustainabilityData.value.monthly_trend && sustainabilityData.value.monthly_trend.length > 0) {
    const ctx = monthlyTrendChart.value.getContext('2d')
    monthlyTrendChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: sustainabilityData.value.monthly_trend.map(d => {
          const [year, month] = d.month.split('-')
          return new Date(year, month - 1).toLocaleDateString('en-AU', {
            month: 'short',
            year: 'numeric'
          })
        }),
        datasets: [{
          label: 'Carbon Emissions (kg CO₂)',
          data: sustainabilityData.value.monthly_trend.map(d => d.carbon_kg),
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `Emissions: ${formatWeight(context.parsed.y)} kg CO₂`
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => `${formatWeight(value)} kg`
            }
          }
        }
      }
    })
  }
}

// Watch for filter changes
watch(() => props.filters, () => {
  loadSustainabilityData()
}, { immediate: true, deep: true })

// Helper functions
const formatWeight = (kg) => {
  return new Intl.NumberFormat('en-AU', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(kg || 0)
}

const getRankClass = (index) => {
  if (index === 0) return 'bg-red-400 text-red-900'
  if (index === 1) return 'bg-orange-400 text-orange-900'
  if (index === 2) return 'bg-yellow-400 text-yellow-900'
  return 'bg-gray-200 text-gray-700'
}
</script>
