<template>
  <div class="relative" ref="containerRef">
    <div class="relative">
      <input
        ref="inputRef"
        v-model="searchQuery"
        type="text"
        :placeholder="placeholder"
        :disabled="disabled"
        class="w-full rounded-lg border border-gray-300 px-4 py-2.5 pr-10 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:bg-gray-100 disabled:cursor-not-allowed"
        @focus="handleFocus"
        @input="handleInput"
        @keydown.down.prevent="moveHighlight(1)"
        @keydown.up.prevent="moveHighlight(-1)"
        @keydown.enter.prevent="selectHighlighted"
        @keydown.escape="closeDropdown"
      />

      <!-- Loading Spinner -->
      <div v-if="loading" class="absolute right-3 top-1/2 -translate-y-1/2">
        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
      </div>

      <!-- Clear Button -->
      <button
        v-else-if="searchQuery && !disabled"
        @click="clearSelection"
        type="button"
        class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Dropdown -->
    <Transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="showDropdown && (filteredOptions.length > 0 || loading || (!loading && searchQuery && filteredOptions.length === 0))"
        class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto"
      >
        <!-- Loading State -->
        <div v-if="loading" class="px-4 py-3 text-sm text-gray-500 text-center">
          Loading...
        </div>

        <!-- No Results -->
        <div v-else-if="searchQuery && filteredOptions.length === 0" class="px-4 py-3 text-sm text-gray-500 text-center">
          {{ noResultsText }}
        </div>

        <!-- Options List -->
        <div v-else>
          <button
            v-for="(option, index) in filteredOptions"
            :key="option.value"
            type="button"
            @click="selectOption(option)"
            @mouseenter="highlightedIndex = index"
            :class="[
              'w-full text-left px-4 py-2.5 text-sm hover:bg-blue-50 cursor-pointer transition-colors',
              highlightedIndex === index ? 'bg-blue-50' : '',
            ]"
          >
            <div class="font-medium text-gray-900">{{ option.label }}</div>
            <div v-if="option.subtitle" class="text-xs text-gray-500 mt-0.5">{{ option.subtitle }}</div>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  options: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: 'Search...',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  noResultsText: {
    type: String,
    default: 'No results found',
  },
  minChars: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['update:modelValue', 'search'])

const searchQuery = ref(props.modelValue || '')
const showDropdown = ref(false)
const highlightedIndex = ref(0)
const containerRef = ref(null)
const inputRef = ref(null)

// Find the option that matches the current modelValue
const selectedOption = computed(() => {
  return props.options.find(opt => opt.value === props.modelValue || opt.label === props.modelValue)
})

// Update search query when modelValue changes from parent
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    const option = props.options.find(opt => opt.value === newValue)
    searchQuery.value = option ? option.label : newValue
  } else {
    searchQuery.value = ''
  }
})

// Filter options based on search query
const filteredOptions = computed(() => {
  if (!searchQuery.value || searchQuery.value.length < props.minChars) {
    return props.options.slice(0, 50) // Show first 50 options if no search
  }

  const query = searchQuery.value.toLowerCase()
  return props.options.filter(option => {
    const matchLabel = option.label.toLowerCase().includes(query)
    const matchSubtitle = option.subtitle?.toLowerCase().includes(query)
    return matchLabel || matchSubtitle
  }).slice(0, 50) // Limit to 50 results
})

const handleFocus = () => {
  showDropdown.value = true
  highlightedIndex.value = 0
}

const handleInput = () => {
  showDropdown.value = true
  highlightedIndex.value = 0

  // Emit search event for dynamic loading
  emit('search', searchQuery.value)

  // Clear selection if user types something different
  if (selectedOption.value && searchQuery.value !== selectedOption.value.label) {
    emit('update:modelValue', '')
  }
}

const selectOption = (option) => {
  searchQuery.value = option.label
  emit('update:modelValue', option.value)
  closeDropdown()
}

const selectHighlighted = () => {
  if (filteredOptions.value.length > 0 && highlightedIndex.value >= 0) {
    selectOption(filteredOptions.value[highlightedIndex.value])
  }
}

const moveHighlight = (direction) => {
  if (!showDropdown.value) {
    showDropdown.value = true
    return
  }

  highlightedIndex.value += direction

  if (highlightedIndex.value < 0) {
    highlightedIndex.value = filteredOptions.value.length - 1
  } else if (highlightedIndex.value >= filteredOptions.value.length) {
    highlightedIndex.value = 0
  }
}

const closeDropdown = () => {
  showDropdown.value = false
  highlightedIndex.value = 0
}

const clearSelection = () => {
  searchQuery.value = ''
  emit('update:modelValue', '')
  emit('search', '')
  inputRef.value?.focus()
}

// Click outside handler
const handleClickOutside = (event) => {
  if (containerRef.value && !containerRef.value.contains(event.target)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)

  // Initialize search query from model value
  if (props.modelValue && props.options.length > 0) {
    const option = props.options.find(opt => opt.value === props.modelValue)
    if (option) {
      searchQuery.value = option.label
    }
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
