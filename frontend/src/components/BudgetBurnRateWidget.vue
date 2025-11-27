<template>
  <div class="bg-white rounded-xl shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <span class="mdi mdi-chart-line text-blue-600" style="font-size: 24px;"></span>
            Budget Burn Rate & Forecast
          </h3>
          <p class="text-sm text-gray-500 mt-1">Track spending rate and project year-end budget status</p>
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
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="text-sm text-gray-500 mt-2">Loading burn rate data...</p>
      </div>

      <!-- No Data / No Budget -->
      <div v-else-if="!loading && (!burnRateData || burnRateData.error)" class="px-6 py-8 text-center">
        <span class="mdi mdi-alert-circle text-4xl text-gray-300"></span>
        <p class="text-sm text-gray-500 mt-2">{{ burnRateData?.error || 'No burn rate data available' }}</p>
        <p class="text-xs text-gray-400 mt-1">Ensure an organization is selected and a current fiscal year exists</p>
      </div>

      <!-- Data Display -->
      <div v-else class="p-6 space-y-6">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- Burn Rate -->
          <div class="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-blue-700 font-medium uppercase">Monthly Burn Rate</p>
                <p class="text-2xl font-bold text-blue-900 mt-1">{{ formatCurrency(burnRateData.summary.burn_rate) }}</p>
                <p class="text-xs text-blue-600 mt-0.5">per month</p>
              </div>
              <span class="mdi mdi-fire text-3xl text-blue-600"></span>
            </div>
          </div>

          <!-- Projected Spend -->
          <div class="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-purple-700 font-medium uppercase">Projected Total</p>
                <p class="text-2xl font-bold text-purple-900 mt-1">{{ formatCurrency(burnRateData.summary.projected_total_spend) }}</p>
                <p class="text-xs text-purple-600 mt-0.5">end of FY</p>
              </div>
              <span class="mdi mdi-crystal-ball text-3xl text-purple-600"></span>
            </div>
          </div>

          <!-- Status -->
          <div :class="getStatusColorClass()" class="border rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs font-medium uppercase" :class="getStatusTextColor()">Budget Status</p>
                <p class="text-2xl font-bold mt-1" :class="getStatusTextColor()">{{ getStatusText() }}</p>
                <p class="text-xs mt-0.5" :class="getStatusTextColor()">{{ burnRateData.summary.risk_level }} risk</p>
              </div>
              <span class="mdi text-3xl" :class="[getStatusIcon(), getStatusTextColor()]"></span>
            </div>
          </div>

          <!-- Overrun Amount (if any) -->
          <div v-if="burnRateData.summary.projected_overrun > 0" class="bg-gradient-to-br from-red-50 to-red-100 border border-red-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-red-700 font-medium uppercase">Projected Overrun</p>
                <p class="text-2xl font-bold text-red-900 mt-1">{{ formatCurrency(burnRateData.summary.projected_overrun) }}</p>
                <p class="text-xs text-red-600 mt-0.5">over budget</p>
              </div>
              <span class="mdi mdi-alert-octagon text-3xl text-red-600"></span>
            </div>
          </div>

          <!-- Remaining Months (if no overrun) -->
          <div v-else class="bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-gray-700 font-medium uppercase">Months Remaining</p>
                <p class="text-2xl font-bold text-gray-900 mt-1">{{ burnRateData.fiscal_year.months_remaining }}</p>
                <p class="text-xs text-gray-600 mt-0.5">of {{ burnRateData.fiscal_year.total_months }} total</p>
              </div>
              <span class="mdi mdi-calendar-clock text-3xl text-gray-600"></span>
            </div>
          </div>
        </div>

        <!-- Burn Rate Chart -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <h4 class="text-sm font-semibold text-gray-900 mb-4">Budget vs Actual Spending Trend</h4>
          <div class="h-80">
            <canvas ref="burnRateChart"></canvas>
          </div>
        </div>

        <!-- Fiscal Year Info -->
        <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p class="text-gray-500">Fiscal Year Period</p>
              <p class="font-semibold text-gray-900 mt-1">
                {{ formatDate(burnRateData.fiscal_year.start_date) }} - {{ formatDate(burnRateData.fiscal_year.end_date) }}
              </p>
            </div>
            <div>
              <p class="text-gray-500">Progress</p>
              <p class="font-semibold text-gray-900 mt-1">
                {{ burnRateData.fiscal_year.months_elapsed }} of {{ burnRateData.fiscal_year.total_months }} months
                ({{ Math.round((burnRateData.fiscal_year.months_elapsed / burnRateData.fiscal_year.total_months) * 100) }}%)
              </p>
            </div>
            <div>
              <p class="text-gray-500">Budget Utilization</p>
              <p class="font-semibold text-gray-900 mt-1">
                {{ formatCurrency(burnRateData.summary.total_spent) }} / {{ formatCurrency(burnRateData.summary.total_budget) }}
                ({{ burnRateData.summary.current_utilization.toFixed(1) }}%)
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
const burnRateData = ref(null)

// Chart ref
const burnRateChart = ref(null)
let burnRateChartInstance = null

// Load burn rate data
const loadBurnRateData = async () => {
  if (!props.organization) {
    burnRateData.value = null
    return
  }

  loading.value = true

  try {
    const data = await bookingService.getBudgetBurnRate({
      organization: props.organization
    })
    burnRateData.value = data

    console.log('✅ [BudgetBurnRateWidget] Loaded burn rate data:', data)

    // Render chart after data loads - use setTimeout to ensure DOM is ready
    await nextTick()
    await nextTick() // Double nextTick for Chart.js
    setTimeout(() => {
      renderChart()
    }, 100)
  } catch (error) {
    console.error('❌ [BudgetBurnRateWidget] Error loading burn rate data:', error)
    if (error.response && error.response.data && error.response.data.error) {
      burnRateData.value = { error: error.response.data.error }
    } else {
      burnRateData.value = { error: 'Failed to load burn rate data' }
    }
  } finally {
    loading.value = false
  }
}

// Render chart
const renderChart = () => {
  if (!burnRateData.value || !burnRateData.value.monthly_trend) {
    console.log('⚠️ [BudgetBurnRateWidget] No data available for chart')
    return
  }

  console.log('🎨 [BudgetBurnRateWidget] Rendering chart with data:', {
    monthlyTrendPoints: burnRateData.value.monthly_trend.length,
    totalBudget: burnRateData.value.summary.total_budget,
    totalSpent: burnRateData.value.summary.total_spent,
    burnRate: burnRateData.value.summary.burn_rate
  })

  // Destroy existing chart
  if (burnRateChartInstance) {
    burnRateChartInstance.destroy()
  }

  if (burnRateChart.value) {
    const ctx = burnRateChart.value.getContext('2d')
    console.log('📊 [BudgetBurnRateWidget] Creating burn rate chart')

    const labels = burnRateData.value.monthly_trend.map(d => {
      const [year, month] = d.month.split('-')
      return new Date(year, month - 1).toLocaleDateString('en-AU', {
        month: 'short',
        year: 'numeric'
      })
    })

    const actualSpend = burnRateData.value.monthly_trend.map(d => d.is_actual ? d.cumulative_spend : null)
    const projectedSpend = burnRateData.value.monthly_trend.map(d => !d.is_actual ? d.cumulative_spend : null)
    const budgetAllocation = burnRateData.value.monthly_trend.map(d => d.cumulative_budget)

    burnRateChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Actual Spend',
            data: actualSpend,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4,
            fill: true,
            spanGaps: false
          },
          {
            label: 'Projected Spend',
            data: projectedSpend,
            borderColor: '#a855f7',
            borderDash: [5, 5],
            backgroundColor: 'rgba(168, 85, 247, 0.1)',
            tension: 0.4,
            fill: false,
            spanGaps: true
          },
          {
            label: 'Budget Allocation',
            data: budgetAllocation,
            borderColor: '#10b981',
            borderDash: [2, 2],
            tension: 0.4,
            fill: false
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
            position: 'bottom'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.dataset.label || ''
                const value = context.parsed.y
                return value !== null ? `${label}: ${formatCurrency(value)}` : null
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => formatCurrency(value)
            }
          }
        }
      }
    })
  }
}

// Watch for organization changes
watch(() => props.organization, () => {
  loadBurnRateData()
}, { immediate: true })

// Helper functions
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount || 0)
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getStatusColorClass = () => {
  if (!burnRateData.value) return 'bg-gray-50'

  const status = burnRateData.value.summary.status
  if (status === 'WILL_EXCEED') return 'bg-gradient-to-br from-red-50 to-red-100 border-red-200'
  if (status === 'AT_RISK') return 'bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200'
  if (status === 'ON_TRACK_WARN') return 'bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200'
  if (status === 'ON_TRACK') return 'bg-gradient-to-br from-green-50 to-green-100 border-green-200'
  return 'bg-gray-50'
}

const getStatusTextColor = () => {
  if (!burnRateData.value) return 'text-gray-600'

  const status = burnRateData.value.summary.status
  if (status === 'WILL_EXCEED') return 'text-red-700'
  if (status === 'AT_RISK') return 'text-amber-700'
  if (status === 'ON_TRACK_WARN') return 'text-yellow-700'
  if (status === 'ON_TRACK') return 'text-green-700'
  return 'text-gray-700'
}

const getStatusText = () => {
  if (!burnRateData.value) return 'Unknown'

  const status = burnRateData.value.summary.status
  if (status === 'WILL_EXCEED') return 'Will Exceed'
  if (status === 'AT_RISK') return 'At Risk'
  if (status === 'ON_TRACK_WARN') return 'On Track'
  if (status === 'ON_TRACK') return 'On Track'
  return 'Unknown'
}

const getStatusIcon = () => {
  if (!burnRateData.value) return 'mdi-help-circle'

  const status = burnRateData.value.summary.status
  if (status === 'WILL_EXCEED') return 'mdi-alert-octagon'
  if (status === 'AT_RISK') return 'mdi-alert'
  if (status === 'ON_TRACK_WARN') return 'mdi-information'
  if (status === 'ON_TRACK') return 'mdi-check-circle'
  return 'mdi-help-circle'
}
</script>
