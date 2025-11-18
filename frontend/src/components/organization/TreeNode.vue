<template>
  <div class="tree-node">
    <!-- Node Row -->
    <div
      class="node-row flex items-center py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors"
      :style="{ paddingLeft: `${level * 2 + 0.75}rem` }"
    >
      <!-- Expand/Collapse Button -->
      <button
        v-if="node.children && node.children.length > 0"
        @click="$emit('toggle', node.id)"
        class="mr-2 text-gray-500 hover:text-gray-700 focus:outline-none"
      >
        <span
          class="mdi text-lg transition-transform"
          :class="isExpanded ? 'mdi-chevron-down' : 'mdi-chevron-right'"
        ></span>
      </button>
      <div v-else class="w-6 mr-2"></div>

      <!-- Node Type Icon -->
      <div class="mr-3">
        <span
          class="mdi text-xl"
          :class="getNodeTypeIcon(node.node_type)"
          :style="{ color: getNodeTypeColor(node.node_type) }"
        ></span>
      </div>

      <!-- Node Info -->
      <div class="flex-1 flex items-center">
        <div class="flex-1">
          <div class="flex items-center space-x-2">
            <span class="font-medium text-gray-900">{{ node.name }}</span>
            <span class="text-sm text-gray-500">{{ node.code }}</span>

            <!-- Node Type Badge -->
            <span
              class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
              :class="getNodeTypeBadgeClass(node.node_type)"
            >
              {{ getNodeTypeLabel(node.node_type) }}
            </span>
          </div>

          <!-- Metadata Row -->
          <div class="flex items-center space-x-3 mt-1">
            <!-- Full Path (on hover, show as tooltip) -->
            <span v-if="node.full_path" class="text-xs text-gray-400" :title="node.full_path">
              {{ getTruncatedPath(node.full_path) }}
            </span>

            <!-- Counts -->
            <div class="flex items-center space-x-3">
              <span
                v-if="node.traveller_count > 0"
                class="inline-flex items-center text-xs text-gray-600"
                :title="`${node.traveller_count} traveller(s)`"
              >
                <span class="mdi mdi-account-multiple text-sm mr-1"></span>
                {{ node.traveller_count }}
              </span>

              <span
                v-if="node.budget_count > 0"
                class="inline-flex items-center text-xs text-gray-600"
                :title="`${node.budget_count} budget(s)`"
              >
                <span class="mdi mdi-currency-usd text-sm mr-1"></span>
                {{ node.budget_count }}
              </span>

              <span
                v-if="node.descendant_count > 0"
                class="inline-flex items-center text-xs text-gray-600"
                :title="`${node.descendant_count} child node(s)`"
              >
                <span class="mdi mdi-file-tree text-sm mr-1"></span>
                {{ node.descendant_count }}
              </span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center space-x-1 ml-4">
          <button
            @click="$emit('add-child', node)"
            class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
            title="Add child node"
          >
            <span class="mdi mdi-plus-circle text-lg"></span>
          </button>

          <button
            @click="$emit('edit', node)"
            class="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
            title="Edit node"
          >
            <span class="mdi mdi-pencil text-lg"></span>
          </button>

          <button
            @click="$emit('merge', node)"
            class="p-1.5 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded transition-colors"
            title="Merge node"
          >
            <span class="mdi mdi-merge text-lg"></span>
          </button>

          <button
            @click="$emit('delete', node)"
            class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
            title="Delete node"
            :disabled="hasChildren || hasReferences"
          >
            <span class="mdi mdi-delete text-lg"></span>
          </button>
        </div>
      </div>
    </div>

    <!-- Children (Recursive) -->
    <div v-if="isExpanded && node.children && node.children.length > 0" class="children">
      <tree-node
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :level="level + 1"
        :expanded-nodes="expandedNodes"
        @toggle="$emit('toggle', $event)"
        @add-child="$emit('add-child', $event)"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
        @merge="$emit('merge', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  level: {
    type: Number,
    default: 0
  },
  expandedNodes: {
    type: Set,
    required: true
  }
})

defineEmits(['toggle', 'add-child', 'edit', 'delete', 'merge'])

// Computed
const isExpanded = computed(() => props.expandedNodes.has(props.node.id))

const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
})

const hasReferences = computed(() => {
  return (props.node.traveller_count > 0 || props.node.budget_count > 0)
})

// Helper Methods
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
    'COST_CENTER': '#10b981', // green
    'BUSINESS_UNIT': '#3b82f6', // blue
    'REGION': '#f59e0b', // amber
    'DEPARTMENT': '#8b5cf6', // violet
    'DIVISION': '#ec4899', // pink
    'GROUP': '#6366f1', // indigo
    'OTHER': '#6b7280' // gray
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
  const maxLength = 50
  if (path.length <= maxLength) return path
  return path.substring(0, maxLength) + '...'
}
</script>

<style scoped>
.tree-node {
  position: relative;
}

.node-row {
  border-left: 2px solid transparent;
}

.node-row:hover {
  border-left-color: #3b82f6;
}

.children {
  position: relative;
}

/* Disabled state for delete button */
button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

button:disabled:hover {
  background-color: transparent !important;
  color: #9ca3af !important;
}
</style>
