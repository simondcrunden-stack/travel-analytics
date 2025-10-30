<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Spend by Airline</h3>
      <p class="mt-1 text-sm text-gray-600">Top airlines by total spend</p>
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
const airlineData = ref([])

// Chart data
const chartData = computed(() => {
  if (!airlineData.value.length) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: airlineData.value.map((item) => item.airline),
    datasets: [
      {
        label: 'Total Spend',
        data: airlineData.value.map((item) => item.spend),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgb(59, 130, 246)',
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
          return `Spend: ${formatCurrency(context.parsed.y)}`
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

// Load airline data
const loadAirlineData = async () => {
  try {
    loading.value = true

    const params = {
      booking_type: 'AIR',
    }

    if (props.filters.dateFrom) params.travel_date__gte = props.filters.dateFrom
    if (props.filters.dateTo) params.travel_date__lte = props.filters.dateTo

    const response = await api.get('/bookings/', { params })
    const bookings = response.data.results || []

    // Aggregate spend by airline
    const airlineMap = {}
    bookings.forEach((booking) => {
      const airline = booking.air_details?.airline || 'Unknown'
      const amount = parseFloat(booking.total_amount || 0)

      if (!airlineMap[airline]) {
        airlineMap[airline] = {
          airline,
          spend: 0,
          bookings: 0,
        }
      }

      airlineMap[airline].spend += amount
      airlineMap[airline].bookings += 1
    })

    // Sort by spend and take top 10
    airlineData.value = Object.values(airlineMap)
      .sort((a, b) => b.spend - a.spend)
      .slice(0, 10)
  } catch (error) {
    console.error('Error loading airline data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadAirlineData()
})

watch(
  () => props.filters,
  () => {
    loadAirlineData()
  },
  { deep: true }
)

defineExpose({
  refresh: loadAirlineData,
})
</script>