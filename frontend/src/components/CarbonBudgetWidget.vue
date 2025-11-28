<template>
  <div class="bg-white rounded-xl shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-green-50 to-emerald-50">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <span class="mdi mdi-leaf text-green-600" style="font-size: 24px;"></span>
            Carbon Budget Tracking & Forecast
          </h3>
          <p class="text-sm text-gray-500 mt-1">Monitor emissions against carbon budget and project year-end status</p>
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
        <p class="text-sm text-gray-500 mt-2">Loading carbon budget data...</p>
      </div>

      <!-- No Data / No Budget -->
      <div v-else-if="!loading && (!carbonData || carbonData.error)" class="px-6 py-8 text-center">
        <span class="mdi mdi-alert-circle text-4xl text-gray-300"></span>
        <p class="text-sm text-gray-500 mt-2">{{ carbonData?.error || 'No carbon budget data available' }}</p>
        <p class="text-xs text-gray-400 mt-1">Ensure carbon budgets are allocated and a current fiscal year exists</p>
      </div>

      <!-- Data Display -->
      <div v-else class="p-6 space-y-6">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- Carbon Burn Rate -->
          <div class="bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-green-700 font-medium uppercase">Monthly Emission Rate</p>
                <p class="text-2xl font-bold text-green-900 mt-1">{{ carbonData.summary.burn_rate.toFixed(2) }}</p>
                <p class="text-xs text-green-600 mt-0.5">tonnes CO₂/month</p>
              </div>
              <span class="mdi mdi-fire text-3xl text-green-600"></span>
            </div>
          </div>

          <!-- Projected Emissions -->
          <div class="bg-gradient-to-br from-teal-50 to-teal-100 border border-teal-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-teal-700 font-medium uppercase">Projected Total</p>
                <p class="text-2xl font-bold text-teal-900 mt-1">{{ carbonData.summary.projected_total_emissions.toFixed(2) }}</p>
                <p class="text-xs text-teal-600 mt-0.5">tonnes CO₂ (end of FY)</p>
              </div>
              <span class="mdi mdi-chart-timeline-variant text-3xl text-teal-600"></span>
            </div>
          </div>

          <!-- Status -->
          <div :class="getStatusColorClass()" class="border rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs font-medium uppercase" :class="getStatusTextColor()">Carbon Budget Status</p>
                <p class="text-2xl font-bold mt-1" :class="getStatusTextColor()">{{ getStatusText() }}</p>
                <p class="text-xs mt-0.5" :class="getStatusTextColor()">{{ carbonData.summary.risk_level }} risk</p>
              </div>
              <span class="mdi text-3xl" :class="[getStatusIcon(), getStatusTextColor()]"></span>
            </div>
          </div>

          <!-- Overrun Amount (if any) -->
          <div v-if="carbonData.summary.projected_overrun > 0" class="bg-gradient-to-br from-red-50 to-red-100 border border-red-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-red-700 font-medium uppercase">Projected Overrun</p>
                <p class="text-2xl font-bold text-red-900 mt-1">{{ carbonData.summary.projected_overrun.toFixed(2) }}</p>
                <p class="text-xs text-red-600 mt-0.5">tonnes CO₂ over budget</p>
              </div>
              <span class="mdi mdi-alert-octagon text-3xl text-red-600"></span>
            </div>
          </div>

          <!-- Remaining Months (if no overrun) -->
          <div v-else class="bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-gray-700 font-medium uppercase">Months Remaining</p>
                <p class="text-2xl font-bold text-gray-900 mt-1">{{ carbonData.fiscal_year.months_remaining }}</p>
                <p class="text-xs text-gray-600 mt-0.5">of {{ carbonData.fiscal_year.total_months }} total</p>
              </div>
              <span class="mdi mdi-calendar-clock text-3xl text-gray-600"></span>
            </div>
          </div>
        </div>

        <!-- Carbon Emissions Chart -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <h4 class="text-sm font-semibold text-gray-900 mb-4">Carbon Budget vs Actual Emissions Trend</h4>
          <div class="h-80">
            <canvas ref="carbonChart"></canvas>
          </div>
        </div>

        <!-- Fiscal Year Info -->
        <div class="bg-green-50 rounded-lg p-4 border border-green-200">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p class="text-gray-600">Fiscal Year Period</p>
              <p class="font-semibold text-gray-900 mt-1">
                {{ formatDate(carbonData.fiscal_year.start_date) }} - {{ formatDate(carbonData.fiscal_year.end_date) }}
              </p>
            </div>
            <div>
              <p class="text-gray-600">Progress</p>
              <p class="font-semibold text-gray-900 mt-1">
                {{ carbonData.fiscal_year.months_elapsed }} of {{ carbonData.fiscal_year.total_months }} months
                ({{ Math.round((carbonData.fiscal_year.months_elapsed / carbonData.fiscal_year.total_months) * 100) }}%)
              </p>
            </div>
            <div>
              <p class="text-gray-600">Carbon Budget Utilization</p>
              <p class="font-semibold text-gray-900 mt-1">
                {{ carbonData.summary.total_emissions.toFixed(2) }} / {{ carbonData.summary.total_carbon_budget.toFixed(2) }} tonnes CO₂
                ({{ carbonData.summary.current_utilization.toFixed(1) }}%)
              </p>
            </div>
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
  organization: {
    type: String,
    default: null
  }
})

const loading = ref(false)
const showSection = ref(true)
const carbonData = ref(null)

// Chart ref
const carbonChart = ref(null)
let carbonChartInstance = null

// Load carbon budget data
const loadCarbonData = async () => {
  if (!props.organization) {
    carbonData.value = null
    return
  }

  loading.value = true

  try {
    const data = await bookingService.getCarbonBudgetAnalysis({
      organization: props.organization
    })
    carbonData.value = data

    console.log('✅ [CarbonBudgetWidget] Loaded carbon budget data:', data)

    // Render chart after data loads
    await nextTick()
    await nextTick()
    setTimeout(() => {
      renderChart()
    }, 100)
  } catch (error) {
    console.error('❌ [CarbonBudgetWidget] Error loading carbon budget data:', error)
    if (error.response && error.response.data && error.response.data.error) {
      carbonData.value = { error: error.response.data.error }
    } else {
      carbonData.value = { error: 'Failed to load carbon budget data' }
    }
  } finally {
    loading.value = false
  }
}

// Render chart
const renderChart = () => {
  if (!carbonData.value || !carbonData.value.monthly_trend) {
    console.log('⚠️ [CarbonBudgetWidget] No data available for chart')
    return
  }

  const chartCanvas = carbonChart.value
  if (!chartCanvas) {
    console.log('⚠️ [CarbonBudgetWidget] Chart canvas not found')
    return
  }

  // Destroy existing chart
  if (carbonChartInstance) {
    carbonChartInstance.destroy()
  }

  const months = carbonData.value.monthly_trend.map(d => d.month)
  const emissions = carbonData.value.monthly_trend.map(d => d.emissions)
  const cumulativeEmissions = carbonData.value.monthly_trend.map(d => d.cumulative_emissions)
  const cumulativeBudget = carbonData.value.monthly_trend.map(d => d.cumulative_budget)

  carbonChartInstance = new Chart(chartCanvas, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: 'Monthly Emissions (tonnes CO₂)',
          data: emissions,
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          yAxisID: 'y'
        },
        {
          label: 'Cumulative Emissions (tonnes CO₂)',
          data: cumulativeEmissions,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          fill: true,
          yAxisID: 'y1'
        },
        {
          label: 'Cumulative Budget (tonnes CO₂)',
          data: cumulativeBudget,
          borderColor: 'rgb(156, 163, 175)',
          backgroundColor: 'rgba(156, 163, 175, 0.1)',
          borderWidth: 2,
          borderDash: [5, 5],
          tension: 0.3,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || ''
              if (label) {
                label += ': '
              }
              label += context.parsed.y.toFixed(2) + ' tonnes CO₂'
              return label
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: 'Monthly Emissions (tonnes CO₂)'
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: {
            display: true,
            text: 'Cumulative Emissions (tonnes CO₂)'
          },
          grid: {
            drawOnChartArea: false
          }
        }
      }
    }
  })

  console.log('✅ [CarbonBudgetWidget] Chart rendered successfully')
}

// Helper functions
const getStatusColorClass = () => {
  if (!carbonData.value) return 'bg-gray-100'

  const status = carbonData.value.summary.status
  switch (status) {
    case 'ON_TRACK':
      return 'bg-gradient-to-br from-green-50 to-green-100 border-green-200'
    case 'ON_TRACK_WARN':
      return 'bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200'
    case 'AT_RISK':
      return 'bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200'
    case 'WILL_EXCEED':
      return 'bg-gradient-to-br from-red-50 to-red-100 border-red-200'
    default:
      return 'bg-gray-100'
  }
}

const getStatusTextColor = () => {
  if (!carbonData.value) return 'text-gray-600'

  const status = carbonData.value.summary.status
  switch (status) {
    case 'ON_TRACK':
      return 'text-green-700'
    case 'ON_TRACK_WARN':
      return 'text-yellow-700'
    case 'AT_RISK':
      return 'text-orange-700'
    case 'WILL_EXCEED':
      return 'text-red-700'
    default:
      return 'text-gray-700'
  }
}

const getStatusIcon = () => {
  if (!carbonData.value) return 'mdi-help-circle'

  const status = carbonData.value.summary.status
  switch (status) {
    case 'ON_TRACK':
      return 'mdi-check-circle'
    case 'ON_TRACK_WARN':
      return 'mdi-alert-circle'
    case 'AT_RISK':
      return 'mdi-alert'
    case 'WILL_EXCEED':
      return 'mdi-close-circle'
    default:
      return 'mdi-help-circle'
  }
}

const getStatusText = () => {
  if (!carbonData.value) return 'Unknown'

  const status = carbonData.value.summary.status
  switch (status) {
    case 'ON_TRACK':
      return 'On Track'
    case 'ON_TRACK_WARN':
      return 'Warning'
    case 'AT_RISK':
      return 'At Risk'
    case 'WILL_EXCEED':
      return 'Will Exceed'
    case 'NO_BUDGET':
      return 'No Budget'
    default:
      return 'Unknown'
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })
}

// Watch for organization changes
watch(() => props.organization, () => {
  loadCarbonData()
}, { immediate: true })
</script>
