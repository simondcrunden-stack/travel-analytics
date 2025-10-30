<template>
  <div
    class="relative overflow-hidden rounded-2xl bg-white p-6 shadow-sm transition-all duration-300 hover:shadow-lg"
    :class="[gradientClass]"
  >
    <!-- Gradient Overlay -->
    <div class="absolute inset-0 opacity-5" :class="[overlayClass]"></div>

    <!-- Content -->
    <div class="relative">
      <!-- Icon & Title -->
      <div class="mb-4 flex items-start justify-between">
        <div class="flex items-center space-x-3">
          <div class="rounded-xl p-3" :class="[iconBgClass]">
            <MdiIcon :path="icon" :size="24" :class="[iconColorClass]" />
          </div>
          <div>
            <p class="text-sm font-medium text-gray-600">{{ title }}</p>
            <p class="mt-1 text-2xl font-bold text-gray-900">{{ formattedValue }}</p>
          </div>
        </div>

        <!-- Trend Indicator (Optional) -->
        <div
          v-if="trend !== null"
          class="flex items-center space-x-1 rounded-full px-2 py-1 text-xs font-medium"
          :class="trendClasses"
        >
          <MdiIcon 
            :path="trend >= 0 ? mdiTrendingUp : mdiTrendingDown" 
            :size="16" 
          />
          <span>{{ Math.abs(trend) }}%</span>
        </div>
      </div>

      <!-- Subtitle/Description -->
      <p v-if="subtitle" class="text-sm text-gray-500">{{ subtitle }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MdiIcon from '@/components/ui/MdiIcon.vue'
import { mdiTrendingUp, mdiTrendingDown } from '@mdi/js'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  value: {
    type: [Number, String],
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
  icon: {
    type: String,  // Now expects MDI path string
    required: true,
  },
  type: {
    type: String,
    default: 'default',
  },
  format: {
    type: String,
    default: 'currency',
  },
  trend: {
    type: Number,
    default: null,
  },
})

// Format value based on type
const formattedValue = computed(() => {
  if (props.format === 'currency') {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(props.value)
  } else if (props.format === 'percentage') {
    return `${props.value}%`
  } else {
    return new Intl.NumberFormat('en-AU').format(props.value)
  }
})

// Gradient classes based on type
const gradientClass = computed(() => {
  const classes = {
    default: 'border border-gray-100',
    primary: 'border border-blue-100',
    success: 'border border-emerald-100',
    info: 'border border-purple-100',
    warning: 'border border-amber-100',
  }
  return classes[props.type] || classes.default
})

const overlayClass = computed(() => {
  const classes = {
    default: 'bg-gradient-to-br from-gray-500 to-gray-600',
    primary: 'bg-gradient-to-br from-blue-500 to-blue-600',
    success: 'bg-gradient-to-br from-emerald-500 to-emerald-600',
    info: 'bg-gradient-to-br from-purple-500 to-purple-600',
    warning: 'bg-gradient-to-br from-amber-500 to-amber-600',
  }
  return classes[props.type] || classes.default
})

const iconBgClass = computed(() => {
  const classes = {
    default: 'bg-gray-100',
    primary: 'bg-blue-100',
    success: 'bg-emerald-100',
    info: 'bg-purple-100',
    warning: 'bg-amber-100',
  }
  return classes[props.type] || classes.default
})

const iconColorClass = computed(() => {
  const classes = {
    default: 'text-gray-600',
    primary: 'text-blue-600',
    success: 'text-emerald-600',
    info: 'text-purple-600',
    warning: 'text-amber-600',
  }
  return classes[props.type] || classes.default
})

const trendClasses = computed(() => {
  if (props.trend >= 0) {
    return 'bg-emerald-100 text-emerald-700'
  } else {
    return 'bg-red-100 text-red-700'
  }
})
</script>