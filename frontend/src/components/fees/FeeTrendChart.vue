<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Fee Trends Over Time</h3>
      <p class="mt-1 text-sm text-gray-600">Monthly service fee trends</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex h-80 items-center justify-center">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
    </div>

    <!-- Chart -->
    <div v-else class="h-80">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import api from '@/services/api'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
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
const trendData = ref([])

// Chart data
const chartData = computed(() => {
  if (!trendData.value.length) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: trendData.value.map((item) => item.month),
    datasets: [
      {
        label: 'Total Fees',
        data: trendData.value.map((item) => item.total),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: 'rgb(59, 130, 246)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      },
    ],
  }
})

// Chart options
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
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
          const index = context.dataIndex
          const item = trendData.value[index]
          return [
            `Total: ${formatCurrency(context.parsed.y)}`,
            `Transactions: ${item.count}`,
          ]
        },
      },
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: function (value) {
          return formatCurrency(value)
        },
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
    },
    x: {
      grid: {
        display: false,
      },
    },
  },
  interaction: {
    mode: 'index',
    intersect: false,
  },
}

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

// Load trend data
const loadTrendData = async () => {
  try {
    loading.value = true

    const params = {}

    if (props.filters.dateFrom) params.date__gte = props.filters.dateFrom
    if (props.filters.dateTo) params.date__lte = props.filters.dateTo

    const response = await api.get('/service-fees/', { params })
    const fees = response.data.results || []

    // Aggregate by month
    const monthMap = {}
    fees.forEach((fee) => {
      const date = new Date(fee.date)
      const monthKey = date.toLocaleDateString('en-AU', { month: 'short', year: 'numeric' })
      const amount = parseFloat(fee.amount || 0)

      if (!monthMap[monthKey]) {
        monthMap[monthKey] = {
          month: monthKey,
          total: 0,
          count: 0,
          date: date,
        }
      }

      monthMap[monthKey].total += amount
      monthMap[monthKey].count += 1
    })

    // Sort by date and format
    trendData.value = Object.values(monthMap)
      .sort((a, b) => a.date - b.date)
      .map((item) => ({
        month: item.month,
        total: item.total,
        count: item.count,
      }))
  } catch (error) {
    console.error('Error loading trend data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadTrendData()
})

watch(
  () => props.filters,
  () => {
    loadTrendData()
  },
  { deep: true }
)

defineExpose({
  refresh: loadTrendData,
})
</script>