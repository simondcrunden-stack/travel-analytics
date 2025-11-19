<template>
  <div class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
    <!-- Backdrop -->
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="$emit('close')"></div>

    <!-- Modal -->
    <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
      <div class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
        <!-- Header -->
        <div class="bg-white px-6 pt-5 pb-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <span class="mdi mdi-merge text-2xl text-purple-600 mr-2"></span>
              <h3 class="text-lg font-medium text-gray-900" id="modal-title">
                Merge Organizational Node
              </h3>
            </div>
            <button
              @click="$emit('close')"
              class="text-gray-400 hover:text-gray-500 focus:outline-none"
            >
              <span class="mdi mdi-close text-xl"></span>
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="px-6 pb-4">
          <!-- Warning Banner -->
          <div class="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div class="flex">
              <span class="mdi mdi-alert text-amber-600 text-xl mr-3"></span>
              <div class="flex-1">
                <h4 class="text-sm font-medium text-amber-900">Warning: This action cannot be undone</h4>
                <p class="text-sm text-amber-700 mt-1">
                  Merging will move all child nodes, travellers, and budgets from the source node to the target node.
                  The source node will be marked as inactive and hidden from the tree.
                </p>
              </div>
            </div>
          </div>

          <!-- Source Node Info -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-700 mb-3">Source Node (will be merged)</h4>
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div class="flex items-start">
                <span
                  class="mdi text-2xl mr-3"
                  :class="getNodeTypeIcon(sourceNode.node_type)"
                  :style="{ color: getNodeTypeColor(sourceNode.node_type) }"
                ></span>
                <div class="flex-1">
                  <div class="flex items-center space-x-2">
                    <span class="font-medium text-gray-900">{{ sourceNode.name }}</span>
                    <span class="text-sm text-gray-500">{{ sourceNode.code }}</span>
                    <span
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                      :class="getNodeTypeBadgeClass(sourceNode.node_type)"
                    >
                      {{ getNodeTypeLabel(sourceNode.node_type) }}
                    </span>
                  </div>
                  <div class="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                    <span v-if="sourceNode.descendant_count > 0" class="inline-flex items-center">
                      <span class="mdi mdi-file-tree mr-1"></span>
                      {{ sourceNode.descendant_count }} child node(s)
                    </span>
                    <span v-if="sourceNode.traveller_count > 0" class="inline-flex items-center">
                      <span class="mdi mdi-account-multiple mr-1"></span>
                      {{ sourceNode.traveller_count }} traveller(s)
                    </span>
                    <span v-if="sourceNode.budget_count > 0" class="inline-flex items-center">
                      <span class="mdi mdi-currency-usd mr-1"></span>
                      {{ sourceNode.budget_count }} budget(s)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Target Node Selection -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-700 mb-3">
              Target Node (will receive merged data)
            </h4>
            <select
              v-model="selectedTargetId"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              required
            >
              <option value="">Select target node...</option>
              <option
                v-for="node in availableNodes"
                :key="node.id"
                :value="node.id"
              >
                {{ node.name }} ({{ node.code }})
                <template v-if="node.full_path"> - {{ getTruncatedPath(node.full_path) }}</template>
              </option>
            </select>
            <p class="mt-2 text-xs text-gray-500">
              Only nodes with the same type ({{ getNodeTypeLabel(sourceNode.node_type) }}) are available for merging
            </p>
          </div>

          <!-- Selected Target Info -->
          <div v-if="selectedTarget" class="mb-6">
            <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div class="flex items-start">
                <span
                  class="mdi text-2xl mr-3"
                  :class="getNodeTypeIcon(selectedTarget.node_type)"
                  :style="{ color: getNodeTypeColor(selectedTarget.node_type) }"
                ></span>
                <div class="flex-1">
                  <div class="flex items-center space-x-2">
                    <span class="font-medium text-gray-900">{{ selectedTarget.name }}</span>
                    <span class="text-sm text-gray-500">{{ selectedTarget.code }}</span>
                  </div>
                  <div class="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                    <span v-if="selectedTarget.descendant_count > 0" class="inline-flex items-center">
                      <span class="mdi mdi-file-tree mr-1"></span>
                      {{ selectedTarget.descendant_count }} child node(s)
                    </span>
                    <span v-if="selectedTarget.traveller_count > 0" class="inline-flex items-center">
                      <span class="mdi mdi-account-multiple mr-1"></span>
                      {{ selectedTarget.traveller_count }} traveller(s)
                    </span>
                    <span v-if="selectedTarget.budget_count > 0" class="inline-flex items-center">
                      <span class="mdi mdi-currency-usd mr-1"></span>
                      {{ selectedTarget.budget_count }} budget(s)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Merge Summary (when target selected) -->
          <div v-if="selectedTarget" class="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div class="flex">
              <span class="mdi mdi-information text-blue-600 text-xl mr-3"></span>
              <div class="flex-1">
                <h4 class="text-sm font-medium text-blue-900">Merge Summary</h4>
                <ul class="mt-2 text-sm text-blue-700 space-y-1">
                  <li v-if="sourceNode.descendant_count > 0">
                    • {{ sourceNode.descendant_count }} child node(s) will be moved to {{ selectedTarget.name }}
                  </li>
                  <li v-if="sourceNode.traveller_count > 0">
                    • {{ sourceNode.traveller_count }} traveller(s) will be reassigned to {{ selectedTarget.name }}
                  </li>
                  <li v-if="sourceNode.budget_count > 0">
                    • {{ sourceNode.budget_count }} budget(s) will be reassigned to {{ selectedTarget.name }}
                  </li>
                  <li>
                    • "{{ sourceNode.name }}" will be marked as inactive and hidden
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              @click="$emit('close')"
              class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="handleMerge"
              :disabled="!selectedTargetId"
              class="px-4 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span class="inline-flex items-center">
                <span class="mdi mdi-merge mr-2"></span>
                Confirm Merge
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  sourceNode: {
    type: Object,
    required: true
  },
  availableNodes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['merge', 'cancel'])

// State
const selectedTargetId = ref('')

// Computed
const selectedTarget = computed(() => {
  if (!selectedTargetId.value) return null
  return props.availableNodes.find(node => node.id === selectedTargetId.value)
})

// Methods
const handleMerge = () => {
  if (!selectedTargetId.value) {
    alert('Please select a target node')
    return
  }

  // Double confirmation for safety
  const confirmation = confirm(
    `Are you absolutely sure you want to merge "${props.sourceNode.name}" into "${selectedTarget.value.name}"?\n\n` +
    'This action cannot be undone!'
  )

  if (confirmation) {
    emit('merge', selectedTargetId.value)
  }
}

const getNodeTypeIcon = (nodeType) => {
  const icons = {
    'COST_CENTER': 'mdi-currency-usd-circle',
    'BUSINESS_UNIT': 'mdi-office-building',
    'REGION': 'mdi-map-marker-radius',
    'DEPARTMENT': 'mdi-domain',
    'DIVISION': 'mdi-sitemap',
    'GROUP': 'mdi-folder-multiple',
    'OTHER': 'mdi-shape'
  }
  return icons[nodeType] || 'mdi-circle'
}

const getNodeTypeColor = (nodeType) => {
  const colors = {
    'COST_CENTER': '#10b981',
    'BUSINESS_UNIT': '#3b82f6',
    'REGION': '#f59e0b',
    'DEPARTMENT': '#8b5cf6',
    'DIVISION': '#ec4899',
    'GROUP': '#6366f1',
    'OTHER': '#6b7280'
  }
  return colors[nodeType] || '#6b7280'
}

const getNodeTypeLabel = (nodeType) => {
  const labels = {
    'COST_CENTER': 'Cost Center',
    'BUSINESS_UNIT': 'Business Unit',
    'REGION': 'Region',
    'DEPARTMENT': 'Department',
    'DIVISION': 'Division',
    'GROUP': 'Group',
    'OTHER': 'Other'
  }
  return labels[nodeType] || nodeType
}

const getNodeTypeBadgeClass = (nodeType) => {
  const classes = {
    'COST_CENTER': 'bg-green-100 text-green-800',
    'BUSINESS_UNIT': 'bg-blue-100 text-blue-800',
    'REGION': 'bg-amber-100 text-amber-800',
    'DEPARTMENT': 'bg-violet-100 text-violet-800',
    'DIVISION': 'bg-pink-100 text-pink-800',
    'GROUP': 'bg-indigo-100 text-indigo-800',
    'OTHER': 'bg-gray-100 text-gray-800'
  }
  return classes[nodeType] || 'bg-gray-100 text-gray-800'
}

const getTruncatedPath = (path) => {
  if (!path) return ''
  const maxLength = 60
  if (path.length <= maxLength) return path
  return '...' + path.substring(path.length - maxLength)
}
</script>

<style scoped>
/* Smooth transitions */
.transition-opacity {
  transition: opacity 0.2s ease-in-out;
}
</style>
