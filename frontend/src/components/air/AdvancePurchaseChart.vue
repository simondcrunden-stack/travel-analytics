<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">Average Fare by Advance Purchase Period</h3>
        <p class="mt-1 text-sm text-gray-600">Book earlier to save more</p>
      </div>
      <div v-if="potentialSavings > 0" class="text-right">
        <p class="text-sm text-gray-600">Potential Savings</p>
        <p class="text-xl font-bold text-green-600">{{ formatCurrency(potentialSavings) }}</p>
      </div>
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
const advanceData = ref([])

// Calculate days between two dates
const daysBetween = (date1, date2) => {
  const oneDay = 24 * 60 * 60 * 1000
  return Math.round(Math.abs((date1 - date2) / oneDay))
}

// Get period label
const getPeriodLabel = (days) => {
  if (days <= 2) return '0-2 days'
  if (days <= 7) return '3-7 days'
  if (days <= 15) return '8-15 days'
  if (days <= 21) return '16-21 days'
  if (days <= 30) return '22-30 days'
  return '31+ days'
}

// Get period color
const getPeriodColor = (days) => {
  if (days <= 7) return '#EF4444' // Red - Last minute
  if (days <= 15) return '#F59E0B' // Orange - Short notice
  return '#10B981' // Green - Well planned
}

// Calculate potential savings
const potentialSavings = computed(() => {
  if (!advanceData.value.length) return 0

  // Find the average of well-planned bookings (16+ days)
  const wellPlanned = advanceData.value.filter((item) => item.minDays >= 16)
  if (!wellPlanned.length) return 0

  const avgWellPlanned =
    wellPlanned.reduce((sum, item) => sum + item.avgFare, 0) / wellPlanned.length

  // Find the average of last-minute bookings (0-7 days)
  const lastMinute = advanceData.value.filter((item) => item.maxDays <= 7)
  if (!lastMinute.length) return 0

  const avgLastMinute =
    lastMinute.reduce((sum, item) => sum + item.avgFare * item.bookings, 0) /
    lastMinute.reduce((sum, item) => sum + item.bookings, 0)

  const totalLastMinuteBookings = lastMinute.reduce((sum, item) => sum + item.bookings, 0)

  return (avgLastMinute - avgWellPlanned) * totalLastMinuteBookings
})

// Chart data
const chartData = computed(() => {
  if (!advanceData.value.length) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: advanceData.value.map((item) => item.period),
    datasets: [
      {
        label: 'Average Fare',
        data: advanceData.value.map((item) => item.avgFare),
        backgroundColor: advanceData.value.map((item) => item.color),
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
          const item = advanceData.value[index]
          return [
            `Average Fare: ${formatCurrency(context.parsed.y)}`,
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

// Load advance purchase data
const loadAdvanceData = async () => {
  try {
    loading.value = true

    const params = {
      booking_type: 'AIR',
    }

    if (props.filters.dateFrom) params.travel_date__gte = props.filters.dateFrom
    if (props.filters.dateTo) params.travel_date__lte = props.filters.dateTo

    const response = await api.get('/bookings/', { params })
    const bookings = response.data.results || []

    // Aggregate by advance purchase period
    const periodMap = {}
    bookings.forEach((booking) => {
      const bookingDate = new Date(booking.booking_date)
      const travelDate = new Date(booking.travel_date)
      const days = daysBetween(bookingDate, travelDate)
      const period = getPeriodLabel(days)
      const fare = parseFloat(booking.total_amount || 0)

      if (!periodMap[period]) {
        periodMap[period] = {
          period,
          totalFare: 0,
          bookings: 0,
          minDays: days,
          maxDays: days,
        }
      }

      periodMap[period].totalFare += fare
      periodMap[period].bookings += 1
      periodMap[period].minDays = Math.min(periodMap[period].minDays, days)
      periodMap[period].maxDays = Math.max(periodMap[period].maxDays, days)
    })

    // Calculate averages and add colors
    const periods = ['0-2 days', '3-7 days', '8-15 days', '16-21 days', '22-30 days', '31+ days']
    advanceData.value = periods
      .map((period) => {
        const data = periodMap[period]
        if (!data) return null

        const avgFare = data.totalFare / data.bookings
        const color = getPeriodColor(data.minDays)

        return {
          ...data,
          avgFare,
          color,
        }
      })
      .filter((item) => item !== null)
  } catch (error) {
    console.error('Error loading advance purchase data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadAdvanceData()
})

watch(
  () => props.filters,
  () => {
    loadAdvanceData()
  },
  { deep: true }
)

defineExpose({
  refresh: loadAdvanceData,
})
</script>