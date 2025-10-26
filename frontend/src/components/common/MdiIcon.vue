<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    :class="className"
  >
    <path :d="path" fill="currentColor" />
  </svg>
</template>

<script setup>
defineProps({
  path: {
    type: String,
    required: true,
  },
  size: {
    type: [Number, String],
    default: 24,
  },
  className: {
    type: String,
    default: '',
  },
})
</script>
