// src/services/organizationService.js
import api from './api'

export default {
  // Get full organizational tree (recursive with children)
  async getOrganizationTree(params = {}) {
    const response = await api.get('/organizational-nodes/tree/', { params })
    return response
  },

  // Get root nodes only
  async getRootNodes(params = {}) {
    const response = await api.get('/organizational-nodes/roots/', { params })
    return response.data
  },

  // Get all organizational nodes (flat list)
  async getOrganizationalNodes(params = {}) {
    const response = await api.get('/organizational-nodes/', { params })
    return response.data
  },

  // Get single organizational node
  async getOrganizationalNode(id) {
    const response = await api.get(`/organizational-nodes/${id}/`)
    return response.data
  },

  // Create new organizational node
  async createOrganizationalNode(data) {
    const response = await api.post('/organizational-nodes/', data)
    return response.data
  },

  // Update organizational node
  async updateOrganizationalNode(id, data) {
    const response = await api.patch(`/organizational-nodes/${id}/`, data)
    return response.data
  },

  // Delete organizational node
  async deleteOrganizationalNode(id) {
    const response = await api.delete(`/organizational-nodes/${id}/`)
    return response.data
  },

  // Get children of a node
  async getChildren(nodeId, params = {}) {
    const response = await api.get(`/organizational-nodes/${nodeId}/children/`, { params })
    return response.data
  },

  // Get ancestors of a node
  async getAncestors(nodeId, params = {}) {
    const response = await api.get(`/organizational-nodes/${nodeId}/ancestors/`, { params })
    return response.data
  },

  // Get descendants of a node
  async getDescendants(nodeId, params = {}) {
    const response = await api.get(`/organizational-nodes/${nodeId}/descendants/`, { params })
    return response.data
  },

  // Move node to new position
  async moveOrganizationalNode(nodeId, targetId, position = 'last-child') {
    const response = await api.post(`/organizational-nodes/${nodeId}/move/`, {
      target_id: targetId,
      position: position
    })
    return response.data
  },

  // Merge node into target
  async mergeOrganizationalNode(sourceId, targetId) {
    const response = await api.post(`/organizational-nodes/${sourceId}/merge/`, {
      target_id: targetId
    })
    return response.data
  },

  // Helper: Get node type label
  getNodeTypeLabel(nodeType) {
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
  },

  // Helper: Get node type icon
  getNodeTypeIcon(nodeType) {
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
  },

  // Helper: Get node type color
  getNodeTypeColor(nodeType) {
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
  },

  // Helper: Build tree from flat list
  buildTree(nodes) {
    const nodeMap = new Map()
    const rootNodes = []

    // First pass: create map of all nodes
    nodes.forEach(node => {
      nodeMap.set(node.id, { ...node, children: [] })
    })

    // Second pass: build tree structure
    nodes.forEach(node => {
      const currentNode = nodeMap.get(node.id)
      if (node.parent) {
        const parentNode = nodeMap.get(node.parent)
        if (parentNode) {
          parentNode.children.push(currentNode)
        } else {
          // Parent not found, treat as root
          rootNodes.push(currentNode)
        }
      } else {
        // No parent, this is a root node
        rootNodes.push(currentNode)
      }
    })

    return rootNodes
  },

  // Helper: Flatten tree to list
  flattenTree(nodes) {
    const result = []
    const flatten = (nodeList) => {
      nodeList.forEach(node => {
        result.push(node)
        if (node.children && node.children.length > 0) {
          flatten(node.children)
        }
      })
    }
    flatten(nodes)
    return result
  },

  // Helper: Find node in tree by ID
  findNodeInTree(nodes, nodeId) {
    for (const node of nodes) {
      if (node.id === nodeId) {
        return node
      }
      if (node.children && node.children.length > 0) {
        const found = this.findNodeInTree(node.children, nodeId)
        if (found) {
          return found
        }
      }
    }
    return null
  },

  // Helper: Get all node IDs from tree
  getAllNodeIds(nodes) {
    const ids = []
    const collect = (nodeList) => {
      nodeList.forEach(node => {
        ids.push(node.id)
        if (node.children && node.children.length > 0) {
          collect(node.children)
        }
      })
    }
    collect(nodes)
    return ids
  }
}
