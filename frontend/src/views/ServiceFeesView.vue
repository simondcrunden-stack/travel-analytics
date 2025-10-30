<template>
  <div class="min-h-screen bg-gray-50 p-8">
    <div class="mx-auto max-w-7xl">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Service Fees Analytics</h1>
        <p class="mt-2 text-gray-600">Analyze booking fees, channels, and trends</p>
      </div>

      <!-- Filters Section -->
      <div class="mb-8 rounded-2xl bg-white p-6 shadow-sm">
        <h3 class="mb-4 text-lg font-semibold text-gray-900">Filters</h3>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <!-- Fee Type Filter -->
          <div>
            <label for="feeType" class="block text-sm font-medium text-gray-700">Fee Type</label>
            <select
              id="feeType"
              v-model="filters.feeType"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="">All Fee Types</option>
              <option value="ONLINE_DOMESTIC">Online Domestic</option>
              <option value="ONLINE_INTERNATIONAL">Online International</option>
              <option value="OFFLINE_DOMESTIC">Offline Domestic</option>
              <option value="OFFLINE_INTERNATIONAL">Offline International</option>
              <option value="CHANGE_FEE">Change Fee</option>
              <option value="REFUND_FEE">Refund Fee</option>
              <option value="AFTER_HOURS">After Hours</option>
              <option value="CONSULTATION">Consultation</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          <!-- Date From Filter -->
          <div>
            <label for="dateFrom" class="block text-sm font-medium text-gray-700">Date From</label>
            <input
              id="dateFrom"
              v-model="filters.dateFrom"
              type="date"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <!-- Date To Filter -->
          <div>
            <label for="dateTo" class="block text-sm font-medium text-gray-700">Date To</label>
            <input
              id="dateTo"
              v-model="filters.dateTo"
              type="date"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <!-- Channel Filter -->
          <div>
            <label for="channel" class="block text-sm font-medium text-gray-700">Channel</label>
            <select
              id="channel"
              v-model="filters.channel"
              class="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="">All Channels</option>
              <option value="ONLINE">Online</option>
              <option value="OFFLINE">Offline</option>
            </select>
          </div>
        </div>

        <!-- Clear Filters Button -->
        <div class="mt-4">
          <button
            @click="clearFilters"
            class="rounded-lg bg-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-300"
          >
            Clear Filters
          </button>
        </div>
      </div>

      <!-- Stats Cards - Note the mb-6 class added -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <!-- Total Fees -->
        <div class="rounded-2xl bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Total Fees</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                ${{ formatNumber(stats.totalFees) }}
              </p>
            </div>
            <div class="rounded-full bg-blue-100 p-3">
              <svg class="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Total Transactions -->
        <div class="rounded-2xl bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Total Transactions</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                {{ stats.totalTransactions }}
              </p>
            </div>
            <div class="rounded-full bg-purple-100 p-3">
              <svg class="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Average Fee -->
        <div class="rounded-2xl bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Average Fee</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                ${{ formatNumber(stats.avgFee) }}
              </p>
            </div>
            <div class="rounded-full bg-green-100 p-3">
              <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Online Percentage -->
        <div class="rounded-2xl bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Online %</p>
              <p class="mt-2 text-3xl font-bold text-gray-900">
                {{ stats.onlinePercentage }}%
              </p>
            </div>
            <div class="rounded-full bg-amber-100 p-3">
              <svg class="h-6 w-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Chart Components Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <FeeTypeChart :filters="filters" />
        <FeeChannelChart :filters="filters" />
      </div>

      <FeeTrendChart :filters="filters" class="mb-6" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import api from '@/services/api'
import FeeTypeChart from '@/components/fees/FeeTypeChart.vue'
import FeeChannelChart from '@/components/fees/FeeChannelChart.vue'
import FeeTrendChart from '@/components/fees/FeeTrendChart.vue'

// Filters
const filters = reactive({
  feeType: '',
  dateFrom: '',
  dateTo: '',
  channel: '',
})

// Stats
const stats = reactive({
  totalFees: 0,
  totalTransactions: 0,
  avgFee: 0,
  onlinePercentage: 0,
})

// Format number helper
const formatNumber = (num) => {
  return new Intl.NumberFormat('en-AU').format(Math.round(num || 0))
}

// Clear filters
const clearFilters = () => {
  filters.feeType = ''
  filters.dateFrom = ''
  filters.dateTo = ''
  filters.channel = ''
}

// Load stats
const loadStats = async () => {
  try {
    const params = {}

    if (filters.dateFrom) params.fee_date__gte = filters.dateFrom
    if (filters.dateTo) params.fee_date__lte = filters.dateTo
    if (filters.feeType) params.fee_type = filters.feeType

    const response = await api.get('/service-fees/', { params })
    
    const fees = response.data.results || []
    
    stats.totalTransactions = fees.length
    stats.totalFees = fees.reduce((sum, f) => sum + parseFloat(f.amount || 0), 0)
    stats.avgFee = stats.totalTransactions > 0 ? Math.round(stats.totalFees / stats.totalTransactions) : 0
    
    // Calculate online percentage
    const onlineFees = fees.filter(f => 
      f.fee_type && f.fee_type.includes('ONLINE')
    ).length
    stats.onlinePercentage = stats.totalTransactions > 0 
      ? Math.round((onlineFees / stats.totalTransactions) * 100) 
      : 0
  } catch (error) {
    console.error('Error loading service fees stats:', error)
  }
}

// Watch filters
watch(filters, () => {
  loadStats()
}, { deep: true })

// Load data on mount
onMounted(() => {
  loadStats()
})
</script>