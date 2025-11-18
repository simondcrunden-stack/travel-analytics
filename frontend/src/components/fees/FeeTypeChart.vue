<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Fees by Type</h3>
      <p class="mt-1 text-sm text-gray-600">Service fees breakdown by category</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex h-80 items-center justify-center">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
    </div>

    <!-- Chart -->
    <div v-else class="h-80">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import api from '@/services/api'

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({}),
  },
})

const loading = ref(false)
const feeData = ref([])

// Fee type colors
const feeColors = {
  'BOOKING_ONLINE_DOM': '#3B82F6',
  'BOOKING_ONLINE_INTL': '#8B5CF6',
  'BOOKING_OFFLINE_DOM': '#F59E0B',
  'BOOKING_OFFLINE_INTL': '#EF4444',
  'CHANGE_FEE': '#10B981',
  'REFUND_FEE': '#6B7280',
  'AFTER_HOURS': '#EC4899',
  'CONSULTATION': '#14B8A6',
  'OTHER': '#64748B',
}

// Chart data
const chartData = computed(() => {
  if (!feeData.value.length) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: feeData.value.map((item) => item.label),
    datasets: [
      {
        label: 'Total Fees',
        data: feeData.value.map((item) => item.total),
        backgroundColor: feeData.value.map((item) => feeColors[item.type] || '#6B7280'),
        borderWidth: 0,
        borderRadius: 8,
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
          const item = feeData.value[index]
          return [
            `Total: ${formatCurrency(context.parsed.y)}`,
            `Transactions: ${item.count}`,
            `Avg Fee: ${formatCurrency(item.avg)}`,
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
      ticks: {
        font: {
          size: 11,
        },
      },
    },
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

// Fee type labels
const feeTypeLabels = {
  'BOOKING_ONLINE_DOM': 'Online - Domestic',
  'BOOKING_ONLINE_INTL': 'Online - International',
  'BOOKING_OFFLINE_DOM': 'Offline - Domestic',
  'BOOKING_OFFLINE_INTL': 'Offline - International',
  'CHANGE_FEE': 'Change Fee',
  'REFUND_FEE': 'Refund Fee',
  'AFTER_HOURS': 'After Hours',
  'CONSULTATION': 'Consultation',
  'OTHER': 'Other',
}

// Load fee type data
const loadFeeData = async () => {
  try {
    loading.value = true

    const params = {}

    if (props.filters.dateFrom) params.date__gte = props.filters.dateFrom
    if (props.filters.dateTo) params.date__lte = props.filters.dateTo
    if (props.filters.feeType) params.fee_type = props.filters.feeType

    const response = await api.get('/service-fees/', { params })
    const fees = response.data.results || []

    // Aggregate by fee type
    const feeMap = {}
    fees.forEach((fee) => {
      const type = fee.fee_type || 'OTHER'

      if (!feeMap[type]) {
        feeMap[type] = {
          type,
          label: feeTypeLabels[type] || type,
          total: 0,
          count: 0,
        }
      }

      feeMap[type].total += parseFloat(fee.fee_amount || 0)
      feeMap[type].count += 1
    })

    // Calculate averages and sort by total
    feeData.value = Object.values(feeMap)
      .map((item) => ({
        ...item,
        avg: item.total / item.count,
      }))
      .sort((a, b) => b.total - a.total)
  } catch (error) {
    console.error('Error loading fee type data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadFeeData()
})

watch(
  () => props.filters,
  () => {
    loadFeeData()
  },
  { deep: true }
)

defineExpose({
  refresh: loadFeeData,
})
</script>