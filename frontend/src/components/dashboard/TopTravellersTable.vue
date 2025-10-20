<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">Top 10 Travellers by Total Travel Spend</h3>
        <p class="mt-1 text-sm text-gray-600">Click on table to view all travellers</p>
      </div>
      <button
        @click="viewAllTravellers"
        class="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
      >
        View All
        <MdiIcon :path="mdiChevronRight" :size="16" />
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
    </div>

    <!-- Table -->
    <div v-else class="overflow-hidden rounded-lg border border-gray-200">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Traveller Name
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              Bookings
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              Spend
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              % of Total
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 bg-white">
          <tr
            v-for="(traveller, index) in topTravellers"
            :key="traveller.id"
            class="transition-colors hover:bg-gray-50"
          >
            <td class="whitespace-nowrap px-6 py-4">
              <div class="flex items-center gap-3">
                <div
                  class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-600"
                >
                  {{ index + 1 }}
                </div>
                <div>
                  <div class="font-medium text-gray-900">{{ traveller.name }}</div>
                  <div class="text-sm text-gray-500">{{ traveller.department }}</div>
                </div>
              </div>
            </td>
            <td class="whitespace-nowrap px-6 py-4 text-right text-sm text-gray-900">
              {{ traveller.bookings }}
            </td>
            <td class="whitespace-nowrap px-6 py-4 text-right text-sm font-medium text-gray-900">
              {{ formatCurrency(traveller.spend) }}
            </td>
            <td class="whitespace-nowrap px-6 py-4 text-right text-sm text-gray-500">
              {{ traveller.percentage }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import MdiIcon from '@/components/ui/MdiIcon.vue'
import { mdiChevronRight } from '@mdi/js'
import dashboardService from '@/services/dashboardService'

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({}),
  },
})

const router = useRouter()
const loading = ref(false)
const topTravellers = ref([])

// Methods
const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

const viewAllTravellers = () => {
  router.push('/travellers')
}

const loadTopTravellers = async () => {
  try {
    loading.value = true

    const params = {}
    if (props.filters.dateRange && props.filters.dateRange.length === 2) {
      params.start_date = props.filters.dateRange[0].toISOString().split('T')[0]
      params.end_date = props.filters.dateRange[1].toISOString().split('T')[0]
    }
    if (props.filters.organization) {
      params.organization = props.filters.organization
    }

    // Mock data for now - in production, this would come from API
    const totalSpend = 41165088.18
    topTravellers.value = [
      { id: 1, name: 'Chin Ash', department: 'Sales', bookings: 100, spend: 853186.23, percentage: 2.07 },
      { id: 2, name: 'Brown Lionel Mr1', department: 'Engineering', bookings: 59, spend: 663572.91, percentage: 1.61 },
      { id: 3, name: 'Wallace Brent Mr1', department: 'Marketing', bookings: 45, spend: 589375.16, percentage: 1.43 },
      { id: 4, name: 'Alderson Salil Mr1', department: 'Operations', bookings: 50, spend: 461282.05, percentage: 1.12 },
      { id: 5, name: 'Gubernia Marianne Mr1', department: 'Finance', bookings: 59, spend: 431445.04, percentage: 1.05 },
      { id: 6, name: 'Richmond Paul Dr1', department: 'Executive', bookings: 2, spend: 351393.57, percentage: 0.85 },
      { id: 7, name: 'Davis-Jacenko Rory Mrs', department: 'HR', bookings: 2, spend: 343941.81, percentage: 0.84 },
      { id: 8, name: 'King Vicky Mr1', department: 'Sales', bookings: 40, spend: 329752.64, percentage: 0.80 },
      { id: 9, name: 'Heine Michael Mac Mi', department: 'IT', bookings: 4, spend: 315134.89, percentage: 0.77 },
      { id: 10, name: 'Keating Jacqui Ms1', department: 'Marketing', bookings: 28, spend: 302692.94, percentage: 0.74 },
    ]
  } catch (error) {
    console.error('Error loading top travellers:', error)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadTopTravellers()
})

watch(() => props.filters, () => {
  loadTopTravellers()
}, { deep: true })

defineExpose({
  refresh: loadTopTravellers,
})
</script>