<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Spend by Hotel Chain</h3>
      <p class="mt-1 text-sm text-gray-600">Top hotel chains by total spend</p>
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
const chainData = ref([])

// Chart data
const chartData = computed(() => {
  if (!chainData.value.length) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: chainData.value.map((item) => item.chain),
    datasets: [
      {
        label: 'Total Spend',
        data: chainData.value.map((item) => item.spend),
        backgroundColor: 'rgba(139, 92, 246, 0.8)',
        borderColor: 'rgb(139, 92, 246)',
        borderWidth: 1,
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
          const item = chainData.value[index]
          return [
            `Spend: ${formatCurrency(context.parsed.y)}`,
            `Bookings: ${item.bookings}`,
            `Nights: ${item.nights}`,
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

// Load hotel chain data
const loadChainData = async () => {
  try {
    loading.value = true

    const params = {
      booking_type: 'HOTEL',
    }

    if (props.filters.city) params.city = props.filters.city
    if (props.filters.dateFrom) params.travel_date__gte = props.filters.dateFrom
    if (props.filters.dateTo) params.travel_date__lte = props.filters.dateTo

    const response = await api.get('/bookings/', { params })
    const bookings = response.data.results || []

    // Aggregate spend by hotel chain
    const chainMap = {}
    bookings.forEach((booking) => {
      const chain = booking.accommodation_details?.hotel_chain || 'Independent'
      const amount = parseFloat(booking.total_amount || 0)
      const nights = parseInt(booking.accommodation_details?.number_of_nights || 0)

      if (!chainMap[chain]) {
        chainMap[chain] = {
          chain,
          spend: 0,
          bookings: 0,
          nights: 0,
        }
      }

      chainMap[chain].spend += amount
      chainMap[chain].bookings += 1
      chainMap[chain].nights += nights
    })

    // Sort by spend and take top 10
    chainData.value = Object.values(chainMap)
      .sort((a, b) => b.spend - a.spend)
      .slice(0, 10)
  } catch (error) {
    console.error('Error loading hotel chain data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadChainData()
})

watch(
  () => props.filters,
  () => {
    loadChainData()
  },
  { deep: true }
)

defineExpose({
  refresh: loadChainData,
})
</script>