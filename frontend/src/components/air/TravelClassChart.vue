<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Bookings by Travel Class</h3>
      <p class="mt-1 text-sm text-gray-600">Distribution of flight classes</p>
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
const classData = ref({})

// Colors for each class
const colors = {
  Economy: '#3B82F6', // Blue
  'Premium Economy': '#8B5CF6', // Purple
  Business: '#F59E0B', // Amber
  First: '#10B981', // Green
}

// Chart data
const chartData = computed(() => {
  const data = Object.values(classData.value)
  const labels = Object.keys(classData.value)

  return {
    labels,
    datasets: [
      {
        data,
        backgroundColor: labels.map((label) => colors[label] || '#6B7280'),
        borderWidth: 2,
        borderColor: '#ffffff',
        hoverOffset: 10,
      },
    ],
  }
})

// Legend items with calculations
const legendItems = computed(() => {
  const data = Object.values(classData.value)
  const total = data.reduce((sum, val) => sum + val, 0)
  const labels = Object.keys(classData.value)

  return labels.map((label, index) => ({
    label,
    count: data[index],
    percentage: total > 0 ? ((data[index] / total) * 100).toFixed(1) : 0,
    color: colors[label] || '#6B7280',
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

// Load class data
const loadClassData = async () => {
  try {
    loading.value = true

    const params = {
      booking_type: 'AIR',
    }

    if (props.filters.dateFrom) params.travel_date__gte = props.filters.dateFrom
    if (props.filters.dateTo) params.travel_date__lte = props.filters.dateTo

    const response = await api.get('/bookings/', { params })
    const bookings = response.data.results || []

    // Aggregate bookings by class
    const classMap = {}
    bookings.forEach((booking) => {
      const travelClass = booking.air_details?.class_of_travel || 'Economy'

      if (!classMap[travelClass]) {
        classMap[travelClass] = 0
      }

      classMap[travelClass] += 1
    })

    classData.value = classMap
  } catch (error) {
    console.error('Error loading class data:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadClassData()
})

watch(
  () => props.filters,
  () => {
    loadClassData()
  },
  { deep: true }
)

defineExpose({
  refresh: loadClassData,
})
</script>