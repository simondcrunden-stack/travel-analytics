<template>
  <div class="p-6">
    <div class="text-center py-12">
      <span class="mdi mdi-office-building text-6xl text-gray-300"></span>
      <h3 class="mt-4 text-lg font-medium text-gray-900">Organization Merge</h3>
      <p class="mt-2 text-sm text-gray-600">
        Organization merging functionality will be available soon.
      </p>
      <p class="mt-1 text-xs text-gray-500">
        This will use the same pattern as Traveller merging.
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
