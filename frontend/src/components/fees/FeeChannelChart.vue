<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Fees by Channel</h3>
      <p class="mt-1 text-sm text-gray-600">Online vs Offline bookings</p>
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
            <p class="text-xs text-gray-500">{{ formatCurrency(item.amount) }}</p>
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
import api from '@/services/api'

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({}),
  },
})

const loading = ref(false)
const channelData = ref({
  online: 0,
  offline: 0,
})

// Colors
const colors = {
  online: '#10B981', // Green
  offline: '#F59E0B', // Amber
}

// Chart data
const chartData = computed(() => {
  return {
    labels: ['Online', 'Offline'],
    datasets: [
      {
        data: [channelData.value.online, channelData.value.offline],
        backgroundColor: [colors.online, colors.offline],
        borderWidth: 2,
        borderColor: '#ffffff',
        hoverOffset: 10,
      },
    ],
  }
})

// Legend items with calculations
const legendItems = computed(() => {
  const total = channelData.value.online + channelData.value.offline
  
  return [
    {
      label: 'Online',
      amount: channelData.value.online,
      percentage: total > 0 ? ((channelData.value.online / total) * 100).toFixed(1) : 0,
      color: colors.online,
    },
    {
      label: 'Offline',
      amount: channelData.value.offline,
      percentage: total > 0 ? ((channelData.value.offline / total) * 100).toFixed(1) : 0,
      color: colors.offline,
    },
  ]
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
          return `${label}: ${formatCurrency(value)} (${percentage}%)`
        },
      },
    },
  },
  cutout: '65%', // Makes it a donut instead of pie
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

// Load channel data
const loadChannelData = async () => {
  try {
    loading.value = true

    const params = {}

    if (props.filters.dateFrom) params.date__gte = props.filters.dateFrom
    if (props.filters.dateTo) params.date__lte = props.filters.dateTo

    const response = await api.get('/service-fees/', { params })
    const fees = response.data.results || []

    // Aggregate by channel (online vs offline based on fee type)
    let onlineTotal = 0
    let offlineTotal = 0

    fees.forEach((fee) => {
      const amount = parseFloat(fee.amount || 0)
      const feeType = fee.fee_type || ''

      if (feeType.includes('ONLINE')) {
        onlineTotal += amount
      } else if (feeType.includes('OFFLINE')) {
        offlineTotal += amount
      }
    })

    channelData.value = {
      online: onlineTotal,
      offline: offlineTotal,
    }
  } catch (error) {
    console.error('Error loading channel data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadChannelData()
})

watch(
  () => props.filters,
  () => {
    loadChannelData()
  },
  { deep: true }
)

defineExpose({
  refresh: loadChannelData,
})
</script>