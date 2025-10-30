<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">Travel Spend by Month</h3>
        <p class="mt-1 text-sm text-gray-600">Monthly breakdown of travel expenses</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-for="type in chartTypes"
          :key="type.value"
          @click="selectedChartType = type.value"
          class="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors"
          :class="
            selectedChartType === type.value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          "
        >
          {{ type.label }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex h-80 items-center justify-center">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
    </div>

    <!-- Chart -->
    <div v-else class="h-80">
      <Bar v-if="selectedChartType === 'bar'" :data="chartData" :options="chartOptions" />
      <Line v-else :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import dashboardService from '@/services/dashboardService'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({}),
  },
})

const loading = ref(false)
const selectedChartType = ref('bar')
const monthlyData = ref([])

const chartTypes = [
  { label: 'Bar', value: 'bar' },
  { label: 'Line', value: 'line' },
]

// Chart data
const chartData = computed(() => {
  if (!monthlyData.value.length) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: monthlyData.value.map((item) => item.month),
    datasets: [
      {
        label: 'Air Travel',
        data: monthlyData.value.map((item) => item.air),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 2,
        fill: selectedChartType.value === 'line',
      },
      {
        label: 'Accommodation',
        data: monthlyData.value.map((item) => item.accommodation),
        backgroundColor: 'rgba(139, 92, 246, 0.8)',
        borderColor: 'rgb(139, 92, 246)',
        borderWidth: 2,
        fill: selectedChartType.value === 'line',
      },
      {
        label: 'Car Hire',
        data: monthlyData.value.map((item) => item.car),
        backgroundColor: 'rgba(16, 185, 129, 0.8)',
        borderColor: 'rgb(16, 185, 129)',
        borderWidth: 2,
        fill: selectedChartType.value === 'line',
      },
      {
        label: 'Other',
        data: monthlyData.value.map((item) => item.other),
        backgroundColor: 'rgba(107, 114, 128, 0.8)',
        borderColor: 'rgb(107, 114, 128)',
        borderWidth: 2,
        fill: selectedChartType.value === 'line',
      },
    ],
  }
})

// Chart options
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        usePointStyle: true,
        padding: 15,
        font: {
          size: 12,
        },
      },
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
          let label = context.dataset.label || ''
          if (label) {
            label += ': '
          }
          if (context.parsed.y !== null) {
            label += new Intl.NumberFormat('en-AU', {
              style: 'currency',
              currency: 'AUD',
              minimumFractionDigits: 0,
            }).format(context.parsed.y)
          }
          return label
        },
      },
    },
  },
  scales: {
    x: {
      stacked: selectedChartType.value === 'bar',
      grid: {
        display: false,
      },
    },
    y: {
      stacked: selectedChartType.value === 'bar',
      beginAtZero: true,
      ticks: {
        callback: function (value) {
          return new Intl.NumberFormat('en-AU', {
            style: 'currency',
            currency: 'AUD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }).format(value)
        },
      },
    },
  },
}))

// Load data
const loadMonthlyData = async () => {
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

    // Fetch bookings and aggregate by month
    const response = await dashboardService.getSpendBreakdown(params)
    
    // For now, create mock monthly data based on the date range
    // In production, this would come from a proper monthly aggregation endpoint
    const months = getMonthsInRange(props.filters.dateRange)
    monthlyData.value = months.map((month) => ({
      month,
      air: Math.random() * 15000000 + 5000000,
      accommodation: Math.random() * 5000000 + 2000000,
      car: Math.random() * 1000000 + 500000,
      other: Math.random() * 500000 + 200000,
    }))
  } catch (error) {
    console.error('Error loading monthly data:', error)
  } finally {
    loading.value = false
  }
}

// Helper to get months in date range
const getMonthsInRange = (dateRange) => {
  if (!dateRange || dateRange.length !== 2) {
    // Default to last 3 months
    const months = []
    const now = new Date()
    for (let i = 2; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
      months.push(
        date.toLocaleDateString('en-AU', { month: 'short', year: 'numeric' })
      )
    }
    return months
  }

  const months = []
  const start = new Date(dateRange[0])
  const end = new Date(dateRange[1])
  
  let current = new Date(start.getFullYear(), start.getMonth(), 1)
  while (current <= end) {
    months.push(
      current.toLocaleDateString('en-AU', { month: 'short', year: 'numeric' })
    )
    current.setMonth(current.getMonth() + 1)
  }
  
  return months
}

// Lifecycle
onMounted(() => {
  loadMonthlyData()
})

watch(() => props.filters, () => {
  loadMonthlyData()
}, { deep: true })

defineExpose({
  refresh: loadMonthlyData,
})
</script>