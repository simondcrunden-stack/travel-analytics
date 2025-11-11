<template>
  <div class="multi-select-wrapper">
    <v-select
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :options="options"
      :multiple="true"
      :searchable="true"
      :close-on-select="false"
      :clear-on-select="false"
      :preserve-search="true"
      :placeholder="placeholder"
      :label="labelKey"
      :reduce="reduceKey ? (option) => option[reduceKey] : undefined"
      :disabled="disabled"
      class="multi-select-vue"
    >
      <template #no-options>
        <div class="text-sm text-gray-500 py-2">{{ noOptionsText }}</div>
      </template>
      
      <template #selected-option="{ label }">
        <span class="selected-tag">{{ label }}</span>
      </template>
    </v-select>
  </div>
</template>

<script setup>
import vSelect from 'vue-select'
import 'vue-select/dist/vue-select.css'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  options: {
    type: Array,
    required: true,
    default: () => []
  },
  placeholder: {
    type: String,
    default: 'Select options...'
  },
  labelKey: {
    type: String,
    default: 'label'
  },
  reduceKey: {
    type: String,
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  },
  noOptionsText: {
    type: String,
    default: 'No options available'
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.multi-select-wrapper :deep(.vs__dropdown-toggle) {
  @apply rounded-lg border border-gray-300 px-2 py-1;
  min-height: 42px;
}

.multi-select-wrapper :deep(.vs__dropdown-toggle:focus-within) {
  @apply border-blue-500 ring-2 ring-blue-500/20;
}

.multi-select-wrapper :deep(.vs__selected) {
  @apply m-1 rounded bg-blue-100 px-2 py-1 text-sm text-blue-800;
  border: none;
}

.multi-select-wrapper :deep(.vs__deselect) {
  @apply ml-1 text-blue-600 hover:text-blue-800;
}

.multi-select-wrapper :deep(.vs__search) {
  @apply text-sm;
  margin: 4px 0;
  padding: 0 4px;
}

.multi-select-wrapper :deep(.vs__search::placeholder) {
  @apply text-gray-400;
}

.multi-select-wrapper :deep(.vs__dropdown-menu) {
  @apply rounded-lg border border-gray-200 shadow-lg;
  max-height: 250px;
}

.multi-select-wrapper :deep(.vs__dropdown-option) {
  @apply px-3 py-2 text-sm;
}

.multi-select-wrapper :deep(.vs__dropdown-option--highlight) {
  @apply bg-blue-50 text-blue-900;
}

.multi-select-wrapper :deep(.vs__dropdown-option--selected) {
  @apply bg-blue-100 text-blue-900;
}

.multi-select-wrapper :deep(.vs__clear) {
  @apply text-gray-400 hover:text-gray-600;
}

.multi-select-wrapper :deep(.vs__open-indicator) {
  @apply text-gray-400;
}

.multi-select-wrapper :deep(.vs__spinner) {
  @apply border-blue-500;
}

/* Disabled state */
.multi-select-wrapper :deep(.vs--disabled .vs__dropdown-toggle) {
  @apply bg-gray-100 cursor-not-allowed;
}

.multi-select-wrapper :deep(.vs--disabled .vs__selected) {
  @apply bg-gray-200 text-gray-600;
}
</style>