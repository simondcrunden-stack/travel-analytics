<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Spend by Rental Company</h3>
      <p class="mt-1 text-sm text-gray-600">Top car rental suppliers by spend</p>
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
const companyData = ref([])

// Chart data
const chartData = computed(() => {
  if (!companyData.value.length) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: companyData.value.map((item) => item.company),
    datasets: [
      {
        label: 'Total Spend',
        data: companyData.value.map((item) => item.spend),
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
          const item = companyData.value[index]
          return [
            `Spend: ${formatCurrency(context.parsed.y)}`,
            `Bookings: ${item.bookings}`,
            `Rental Days: ${item.days}`,
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

// Load rental company data
const loadCompanyData = async () => {
  try {
    loading.value = true

    const params = {
      booking_type: 'CAR',
    }

    if (props.filters.pickupFrom) params.travel_date__gte = props.filters.pickupFrom
    if (props.filters.pickupTo) params.travel_date__lte = props.filters.pickupTo

    const response = await api.get('/bookings/', { params })
    const bookings = response.data.results || []

    // Aggregate by rental company
    const companyMap = {}
    bookings.forEach((booking) => {
      const company = booking.car_hire_details?.rental_company || 'Unknown'
      const amount = parseFloat(booking.total_amount || 0)
      const days = parseInt(booking.car_hire_details?.number_of_days || 0)

      if (!companyMap[company]) {
        companyMap[company] = {
          company,
          spend: 0,
          bookings: 0,
          days: 0,
        }
      }

      companyMap[company].spend += amount
      companyMap[company].bookings += 1
      companyMap[company].days += days
    })

    // Sort by spend and take top 10
    companyData.value = Object.values(companyMap)
      .sort((a, b) => b.spend - a.spend)
      .slice(0, 10)
  } catch (error) {
    console.error('Error loading rental company data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadCompanyData()
})

watch(
  () => props.filters,
  () => {
    loadCompanyData()
  },
  { deep: true }
)

defineExpose({
  refresh: loadCompanyData,
})
</script>