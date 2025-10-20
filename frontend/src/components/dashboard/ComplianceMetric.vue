<template>
  <div class="rounded-xl bg-white p-4">
    <div class="mb-3 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <MdiIcon :path="icon" :size="20" :class="iconColorClass" />
        <span class="text-sm font-medium text-gray-700">{{ label }}</span>
      </div>
      <span class="text-2xl font-bold" :class="valueColorClass">{{ formattedValue }}</span>
    </div>

    <!-- Progress Bar -->
    <div class="mb-2 h-2 overflow-hidden rounded-full bg-gray-200">
      <div
        class="h-full transition-all duration-500"
        :class="progressColorClass"
        :style="{ width: `${percentage}%` }"
      ></div>
    </div>

    <!-- Status Label -->
    <div class="flex items-center justify-between text-xs">
      <span class="text-gray-500">{{ subtitle }}</span>
      <span class="font-medium" :class="statusColorClass">{{ statusText }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MdiIcon from '@/components/ui/MdiIcon.vue'

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  value: {
    type: Number,
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
  icon: {
    type: String,
    required: true,
  },
  format: {
    type: String,
    default: 'percentage', // percentage, number, currency
  },
  thresholds: {
    type: Object,
    default: () => ({
      good: 90,
      warning: 70,
    }),
  },
})

// Format value
const formattedValue = computed(() => {
  if (props.format === 'percentage') {
    return `${props.value.toFixed(1)}%`
  } else if (props.format === 'currency') {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(props.value)
  } else {
    return new Intl.NumberFormat('en-AU').format(props.value)
  }
})

// Calculate percentage for progress bar
const percentage = computed(() => {
  if (props.format === 'percentage') {
    return Math.min(props.value, 100)
  }
  return 100 // Full bar for non-percentage metrics
})

// Determine status
const status = computed(() => {
  if (props.format !== 'percentage') return 'neutral'
  
  if (props.value >= props.thresholds.good) {
    return 'good'
  } else if (props.value >= props.thresholds.warning) {
    return 'warning'
  } else {
    return 'critical'
  }
})

const statusText = computed(() => {
  const statusMap = {
    good: 'Excellent',
    warning: 'Needs Attention',
    critical: 'Critical',
    neutral: '',
  }
  return statusMap[status.value]
})

// Color classes
const iconColorClass = computed(() => {
  const classes = {
    good: 'text-emerald-600',
    warning: 'text-amber-600',
    critical: 'text-red-600',
    neutral: 'text-gray-600',
  }
  return classes[status.value]
})

const valueColorClass = computed(() => {
  const classes = {
    good: 'text-emerald-700',
    warning: 'text-amber-700',
    critical: 'text-red-700',
    neutral: 'text-gray-900',
  }
  return classes[status.value]
})

const progressColorClass = computed(() => {
  const classes = {
    good: 'bg-emerald-500',
    warning: 'bg-amber-500',
    critical: 'bg-red-500',
    neutral: 'bg-gray-400',
  }
  return classes[status.value]
})

const statusColorClass = computed(() => {
  const classes = {
    good: 'text-emerald-700',
    warning: 'text-amber-700',
    critical: 'text-red-700',
    neutral: 'text-gray-600',
  }
  return classes[status.value]
})
</script>