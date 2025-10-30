<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Average Nightly Rate by City</h3>
      <p class="mt-1 text-sm text-gray-600">Accommodation pricing by destination</p>
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
const rateData = ref([])

// Chart data
const chartData = computed(() => {
  if (!rateData.value.length) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: rateData.value.map((item) => item.city),
    datasets: [
      {
        label: 'Average Rate',
        data: rateData.value.map((item) => item.avgRate),
        backgroundColor: 'rgba(245, 158, 11, 0.8)',
        borderColor: 'rgb(245, 158, 11)',
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
          const item = rateData.value[index]
          return [
            `Avg Rate: ${formatCurrency(context.parsed.y)}`,
            `Min Rate: ${formatCurrency(item.minRate)}`,
            `Max Rate: ${formatCurrency(item.maxRate)}`,
            `Bookings: ${item.bookings}`,
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

// Load rate data
const loadRateData = async () => {
  try {
    loading.value = true

    const params = {
      booking_type: 'HOTEL',
    }

    if (props.filters.hotelChain) params.hotel_chain = props.filters.hotelChain
    if (props.filters.dateFrom) params.travel_date__gte = props.filters.dateFrom
    if (props.filters.dateTo) params.travel_date__lte = props.filters.dateTo

    const response = await api.get('/bookings/', { params })
    const bookings = response.data.results || []

    // Aggregate rates by city
    const cityMap = {}
    bookings.forEach((booking) => {
      const city = booking.accommodation_details?.city || 'Unknown'
      const nightlyRate = parseFloat(booking.accommodation_details?.nightly_rate || 0)

      if (!cityMap[city]) {
        cityMap[city] = {
          city,
          rates: [],
          bookings: 0,
        }
      }

      if (nightlyRate > 0) {
        cityMap[city].rates.push(nightlyRate)
      }
      cityMap[city].bookings += 1
    })

    // Calculate averages
    rateData.value = Object.values(cityMap)
      .map((item) => {
        if (item.rates.length === 0) return null

        return {
          city: item.city,
          avgRate: item.rates.reduce((sum, rate) => sum + rate, 0) / item.rates.length,
          minRate: Math.min(...item.rates),
          maxRate: Math.max(...item.rates),
          bookings: item.bookings,
        }
      })
      .filter((item) => item !== null)
      .sort((a, b) => b.avgRate - a.avgRate)
      .slice(0, 10)
  } catch (error) {
    console.error('Error loading rate data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadRateData()
})

watch(
  () => props.filters,
  () => {
    loadRateData()
  },
  { deep: true }
)

defineExpose({
  refresh: loadRateData,
})
</script>