<template>
  <div class="p-6">
    <div class="text-center py-12">
      <span class="mdi mdi-room-service-outline text-6xl text-gray-300"></span>
      <h3 class="mt-4 text-lg font-medium text-gray-900">Service Fee Merge</h3>
      <p class="mt-2 text-sm text-gray-600">
        Service fee merging functionality will be available soon.
      </p>
      <p class="mt-1 text-xs text-gray-500">
        This will consolidate service fee descriptions like "Dom Online", "Domestic Online Booking", etc.
      </p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

const emit = defineEmits(['duplicates-updated'])

onMounted(() => {
  emit('duplicates-updated', 0)
})
</script>
