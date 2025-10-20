<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Travel Policy Compliance</h3>
      <p class="mt-1 text-sm text-gray-600">Breakdown of compliance categories</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex h-80 items-center justify-center">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
    </div>

    <!-- Chart -->
    <div v-else>
      <div class="h-80">
        <Doughnut :data="chartData" :options="chartOptions" />
      </div>

      <!-- Legend with percentages -->
      <div class="mt-6 space-y-3">
        <div
          v-for="(item, index) in legendItems"
          :key="item.label"
          class="flex items-center justify-between rounded-lg border border-gray-100 p-3 hover:bg-gray-50"
        >
          <div class="flex items-center gap-3">
            <div
              class="h-4 w-4 rounded-full"
              :style="{ backgroundColor: item.color }"
            ></div>
            <span class="text-sm font-medium text-gray-700">{{ item.label }}</span>
          </div>
          <div class="text-right">
            <p class="text-sm font-bold text-gray-900">{{ item.percentage }}%</p>
            <p class="text-xs text-gray-500">{{ item.count }} bookings</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import complianceService from '@/services/complianceService'

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({}),
  },
})

const loading = ref(false)
const complianceData = ref({
  lowest_fare_compliant: 0,
  company_policy_compliant: 0,
  authorized_by_management: 0,
  schedule_on_change_alternative: 0,
  flight_times_better_suit_traveller: 0,
  others: 0,
})

// Colors matching your screenshot
const colors = [
  '#DC2626', // Red - Lowest Fare Required
  '#F59E0B', // Amber - Company Policy
  '#3B82F6', // Blue - Authorized
  '#8B5CF6', // Purple - Schedule Change
  '#10B981', // Green - Flight Times
  '#6B7280', // Gray - Others
]

// Chart data
const chartData = computed(() => {
  const data = Object.values(complianceData.value)
  const total = data.reduce((sum, val) => sum + val, 0)

  return {
    labels: [
      'Lowest Fare Required',
      'Company Policy',
      'Authorized by Management',
      'Schedule On-Change Alternative Not Suitable',
      'Flight Times Better Suit Traveller Requirements',
      'Others',
    ],
    datasets: [
      {
        data,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: '#ffffff',
        hoverOffset: 10,
      },
    ],
  }
})

// Legend items with calculations
const legendItems = computed(() => {
  const data = Object.values(complianceData.value)
  const total = data.reduce((sum, val) => sum + val, 0)
  const labels = [
    'Lowest Fare Required',
    'Company Policy',
    'Authorized by Management',
    'Schedule On-Change Alternative Not Suitable',
    'Flight Times Better Suit Traveller Requirements',
    'Others',
  ]

  return labels.map((label, index) => ({
    label,
    count: data[index],
    percentage: total > 0 ? ((data[index] / total) * 100).toFixed(1) : 0,
    color: colors[index],
  }))
})

// Chart options
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false, // We'll use custom legend
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      padding: 12,
      titleFont: {
        size: 14,
      },
      bodyFont: {
        size: 13,
      },
      callbacks: {
        label: function (context) {
          const label = context.label || ''
          const value = context.parsed
          const total = context.dataset.data.reduce((a, b) => a + b, 0)
          const percentage = ((value / total) * 100).toFixed(1)
          return `${label}: ${value} (${percentage}%)`
        },
      },
    },
  },
  cutout: '65%', // Makes it a donut instead of pie
}

// Load data
const loadComplianceData = async () => {
  try {
    loading.value = true

    const params = {}
    if (props.filters.dateRange && props.filters.dateRange.length === 2) {
      params.start_date = props.filters.dateRange[0].toISOString().split('T')[0]
      params.end_date = props.filters.dateRange[1].toISOString().split('T')[0]
    }
    if (props.filters.organization) {
      params.organization = props.filters.organization
    }

    // For now, use mock data
    // In production, this would come from the violations API
    complianceData.value = {
      lowest_fare_compliant: 245,
      company_policy_compliant: 18,
      authorized_by_management: 8,
      schedule_on_change_alternative: 4,
      flight_times_better_suit_traveller: 12,
      others: 13,
    }
  } catch (error) {
    console.error('Error loading compliance data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadComplianceData()
})

watch(() => props.filters, () => {
  loadComplianceData()
}, { deep: true })

defineExpose({
  refresh: loadComplianceData,
})
</script>