<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Bookings by City</h3>
      <p class="mt-1 text-sm text-gray-600">Top destinations for accommodation</p>
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
const cityData = ref([])

// Chart data
const chartData = computed(() => {
  if (!cityData.value.length) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: cityData.value.map((item) => item.city),
    datasets: [
      {
        label: 'Room Nights',
        data: cityData.value.map((item) => item.nights),
        backgroundColor: 'rgba(16, 185, 129, 0.8)',
        borderColor: 'rgb(16, 185, 129)',
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
          const item = cityData.value[index]
          return [
            `Nights: ${context.parsed.y}`,
            `Bookings: ${item.bookings}`,
            `Spend: ${formatCurrency(item.spend)}`,
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
          return value.toLocaleString()
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

// Load city data
const loadCityData = async () => {
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

    // Aggregate by city
    const cityMap = {}
    bookings.forEach((booking) => {
      const city = booking.accommodation_details?.city || 'Unknown'
      const amount = parseFloat(booking.total_amount || 0)
      const nights = parseInt(booking.accommodation_details?.number_of_nights || 0)

      if (!cityMap[city]) {
        cityMap[city] = {
          city,
          spend: 0,
          bookings: 0,
          nights: 0,
        }
      }

      cityMap[city].spend += amount
      cityMap[city].bookings += 1
      cityMap[city].nights += nights
    })

    // Sort by nights and take top 10
    cityData.value = Object.values(cityMap)
      .sort((a, b) => b.nights - a.nights)
      .slice(0, 10)
  } catch (error) {
    console.error('Error loading city data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadCityData()
})

watch(
  () => props.filters,
  () => {
    loadCityData()
  },
  { deep: true }
)

defineExpose({
  refresh: loadCityData,
})
</script>