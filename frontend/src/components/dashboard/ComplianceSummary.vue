<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">Compliance Overview</h3>
        <p class="mt-1 text-sm text-gray-600">Policy adherence and savings opportunities</p>
      </div>
      <router-link
        to="/compliance"
        class="flex items-center gap-2 rounded-lg border border-blue-600 px-4 py-2 text-sm font-medium text-blue-600 transition-colors hover:bg-blue-50"
      >
        View Details
        <MdiIcon :path="mdiChevronRight" :size="20" />
      </router-link>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="rounded-lg bg-red-50 p-4 text-sm text-red-800">
      {{ error }}
    </div>

    <!-- Compliance Content -->
    <div v-else>
      <!-- Overall Compliance -->
      <div class="mb-6 rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600">Overall Compliance Rate</p>
            <p class="mt-2 text-4xl font-bold text-gray-900">
              {{ complianceData.compliance_rate.toFixed(1) }}%
            </p>
            <p class="mt-1 text-sm text-gray-600">
              {{ complianceData.compliant_bookings }} of {{ complianceData.total_bookings }} bookings compliant
            </p>
          </div>
          <div class="flex h-24 w-24 items-center justify-center rounded-full" :class="overallStatusBg">
            <MdiIcon :path="overallStatusIcon" :size="48" :class="overallStatusColor" />
          </div>
        </div>
      </div>

      <!-- Compliance Metrics Grid -->
      <div class="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        <ComplianceMetric
          label="Online Booking"
          :value="complianceData.online_booking_rate"
          subtitle="Bookings made online"
          :icon="mdiWeb"
        />
        <ComplianceMetric
          label="Lowest Fare"
          :value="complianceData.lowest_fare_rate"
          subtitle="Cheapest option selected"
          :icon="mdiCurrencyUsdOff"
          :thresholds="{ good: 80, warning: 60 }"
        />
        <ComplianceMetric
          label="Advance Booking"
          :value="complianceData.advance_booking_rate"
          subtitle="Booked 7+ days ahead"
          :icon="mdiCalendarClock"
          :thresholds="{ good: 75, warning: 50 }"
        />
      </div>

      <!-- Financial Impact -->
      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div class="rounded-xl border border-red-200 bg-red-50 p-4">
          <div class="mb-2 flex items-center gap-2">
            <MdiIcon :path="mdiAlertCircle" :size="20" class="text-red-600" />
            <span class="text-sm font-medium text-red-900">Cost of Change</span>
          </div>
          <p class="text-2xl font-bold text-red-700">
            {{ formatCurrency(complianceData.cost_of_change) }}
          </p>
          <p class="mt-1 text-xs text-red-600">Airline charges for changes to bookings</p>
        </div>

        <div class="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <div class="mb-2 flex items-center gap-2">
            <MdiIcon :path="mdiCashMinus" :size="20" class="text-amber-600" />
            <span class="text-sm font-medium text-amber-900">Out-of-Policy Spend</span>
          </div>
          <p class="text-2xl font-bold text-amber-700">
            {{ formatCurrency(complianceData.out_of_policy_spend) }}
          </p>
          <p class="mt-1 text-xs text-amber-600">Non-compliant bookings</p>
        </div>

        <div class="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
          <div class="mb-2 flex items-center gap-2">
            <MdiIcon :path="mdiPiggyBank" :size="20" class="text-emerald-600" />
            <span class="text-sm font-medium text-emerald-900">Potential Savings</span>
          </div>
          <p class="text-2xl font-bold text-emerald-700">
            {{ formatCurrency(complianceData.potential_savings) }}
          </p>
          <p class="mt-1 text-xs text-emerald-600">If fully compliant</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ComplianceMetric from './ComplianceMetric.vue'
import MdiIcon from '@/components/ui/MdiIcon.vue'
import complianceService from '@/services/complianceService'
import {
  mdiChevronRight,
  mdiShieldCheck,
  mdiShieldAlert,
  mdiShieldOff,
  mdiWeb,
  mdiCurrencyUsdOff,
  mdiCalendarClock,
  mdiAlertCircle,
  mdiCashMinus,
  mdiPiggyBank,
} from '@mdi/js'

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({}),
  },
})

const router = useRouter()
const loading = ref(false)
const error = ref(null)
const complianceData = ref({
  total_bookings: 0,
  compliant_bookings: 0,
  non_compliant_bookings: 0,
  compliance_rate: 0,
  online_booking_rate: 0,
  lowest_fare_rate: 0,
  advance_booking_rate: 0,
  cost_of_change: 0,
  out_of_policy_spend: 0,
  potential_savings: 0,
})

// Overall status
const overallStatus = computed(() => {
  const rate = complianceData.value.compliance_rate
  if (rate >= 90) return 'excellent'
  if (rate >= 75) return 'good'
  if (rate >= 60) return 'warning'
  return 'critical'
})

const overallStatusIcon = computed(() => {
  const icons = {
    excellent: mdiShieldCheck,
    good: mdiShieldCheck,
    warning: mdiShieldAlert,
    critical: mdiShieldOff,
  }
  return icons[overallStatus.value]
})

const overallStatusColor = computed(() => {
  const colors = {
    excellent: 'text-emerald-600',
    good: 'text-blue-600',
    warning: 'text-amber-600',
    critical: 'text-red-600',
  }
  return colors[overallStatus.value]
})

const overallStatusBg = computed(() => {
  const colors = {
    excellent: 'bg-emerald-100',
    good: 'bg-blue-100',
    warning: 'bg-amber-100',
    critical: 'bg-red-100',
  }
  return colors[overallStatus.value]
})

// Methods
const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

const loadComplianceData = async () => {
  try {
    loading.value = true
    error.value = null

    const params = {}
    if (props.filters.dateRange && props.filters.dateRange.length === 2) {
      params.start_date = props.filters.dateRange[0].toISOString().split('T')[0]
      params.end_date = props.filters.dateRange[1].toISOString().split('T')[0]
    }
    if (props.filters.organization) {
      params.organization = props.filters.organization
    }

    const data = await complianceService.getComplianceSummary(params)
    complianceData.value = data
  } catch (err) {
    console.error('Error loading compliance data:', err)
    error.value = 'Failed to load compliance data'
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadComplianceData()
})

// Watch for filter changes
defineExpose({
  refresh: loadComplianceData,
})
</script>