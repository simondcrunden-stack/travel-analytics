<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Bookings by Vehicle Type</h3>
      <p class="mt-1 text-sm text-gray-600">Distribution of rental vehicle types</p>
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
            <p class="text-xs text-gray-500">{{ item.count }} bookings</p>
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
const vehicleData = ref({})

// Colors for vehicle types
const colors = [
  '#3B82F6', // Blue
  '#8B5CF6', // Purple
  '#10B981', // Green
  '#F59E0B', // Amber
  '#EF4444', // Red
  '#6B7280', // Gray
]

// Chart data
const chartData = computed(() => {
  const data = Object.values(vehicleData.value)
  const labels = Object.keys(vehicleData.value)

  return {
    labels,
    datasets: [
      {
        data,
        backgroundColor: labels.map((_, index) => colors[index % colors.length]),
        borderWidth: 2,
        borderColor: '#ffffff',
        hoverOffset: 10,
      },
    ],
  }
})

// Legend items with calculations
const legendItems = computed(() => {
  const data = Object.values(vehicleData.value)
  const total = data.reduce((sum, val) => sum + val, 0)
  const labels = Object.keys(vehicleData.value)

  return labels.map((label, index) => ({
    label,
    count: data[index],
    percentage: total > 0 ? ((data[index] / total) * 100).toFixed(1) : 0,
    color: colors[index % colors.length],
  }))
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
          return `${label}: ${value} (${percentage}%)`
        },
      },
    },
  },
  cutout: '65%', // Makes it a donut instead of pie
}

// Load vehicle type data
const loadVehicleData = async () => {
  try {
    loading.value = true

    const params = {
      booking_type: 'CAR',
    }

    if (props.filters.pickupFrom) params.travel_date__gte = props.filters.pickupFrom
    if (props.filters.pickupTo) params.travel_date__lte = props.filters.pickupTo

    const response = await api.get('/bookings/', { params })
    const bookings = response.data.results || []

    // Aggregate bookings by vehicle type
    const vehicleMap = {}
    bookings.forEach((booking) => {
      const vehicleType = booking.car_hire_details?.vehicle_type || 'Unknown'

      if (!vehicleMap[vehicleType]) {
        vehicleMap[vehicleType] = 0
      }

      vehicleMap[vehicleType] += 1
    })

    vehicleData.value = vehicleMap
  } catch (error) {
    console.error('Error loading vehicle type data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadVehicleData()
})

watch(
  () => props.filters,
  () => {
    loadVehicleData()
  },
  { deep: true }
)

defineExpose({
  refresh: loadVehicleData,
})
</script>