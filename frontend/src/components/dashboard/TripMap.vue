<template>
  <div class="trip-map-container">
    <div ref="mapContainer" class="map"></div>

    <!-- Loading overlay -->
    <div v-if="loading" class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-[1000]">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="absolute top-4 left-1/2 transform -translate-x-1/2 bg-red-50 border border-red-200 rounded-lg p-3 shadow-lg z-[1000]">
      <p class="text-sm text-red-800">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  mapData: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  }
})

const mapContainer = ref(null)
let map = null
let markers = []

onMounted(() => {
  initializeMap()
  if (props.mapData.length > 0) {
    renderMarkers()
  }
})

onBeforeUnmount(() => {
  if (map) {
    map.remove()
  }
})

watch(() => props.mapData, (newData) => {
  if (newData && newData.length > 0) {
    renderMarkers()
  }
}, { deep: true })

const initializeMap = () => {
  if (!mapContainer.value) return

  // Create map centered on Australia
  map = L.map(mapContainer.value, {
    zoomControl: true,
    scrollWheelZoom: true
  }).setView([-25, 135], 4)

  // Add OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
  }).addTo(map)
}

const renderMarkers = () => {
  if (!map) return

  // Clear existing markers
  markers.forEach(marker => map.removeLayer(marker))
  markers = []

  if (props.mapData.length === 0) return

  // Calculate marker sizes based on trip count
  const maxTrips = Math.max(...props.mapData.map(d => d.trips))
  const minTrips = Math.min(...props.mapData.map(d => d.trips))

  // Create markers for each destination
  props.mapData.forEach(destination => {
    // Calculate marker size (radius 5-25px based on trip count)
    const normalizedSize = minTrips === maxTrips ? 0.5 :
      (destination.trips - minTrips) / (maxTrips - minTrips)
    const radius = 8 + (normalizedSize * 17) // 8px to 25px

    // Color based on number of trips
    const color = getColorForTrips(destination.trips, maxTrips)

    // Create circle marker
    const marker = L.circleMarker([destination.latitude, destination.longitude], {
      radius: radius,
      fillColor: color,
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.7
    }).addTo(map)

    // Create popup with destination info
    const popupContent = `
      <div class="text-sm">
        <div class="font-bold text-base mb-2">${destination.city}, ${destination.country}</div>
        <div class="space-y-1">
          <div class="flex justify-between">
            <span class="text-gray-600">Airport:</span>
            <span class="font-semibold">${destination.code}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Trips:</span>
            <span class="font-semibold">${destination.trips}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Travellers:</span>
            <span class="font-semibold">${destination.travellers}</span>
          </div>
          <div class="flex justify-between border-t pt-1 mt-1">
            <span class="text-gray-600">Total Spend:</span>
            <span class="font-semibold">${formatCurrency(destination.total_spend)}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Avg per Trip:</span>
            <span class="font-semibold">${formatCurrency(destination.avg_spend)}</span>
          </div>
        </div>
      </div>
    `

    marker.bindPopup(popupContent, {
      maxWidth: 250,
      className: 'custom-popup'
    })

    // Show popup on hover
    marker.on('mouseover', function() {
      this.openPopup()
    })

    markers.push(marker)
  })

  // Fit map bounds to show all markers
  if (markers.length > 0) {
    const group = L.featureGroup(markers)
    map.fitBounds(group.getBounds().pad(0.1))
  }
}

const getColorForTrips = (trips, maxTrips) => {
  // Color gradient from blue (few trips) to red (many trips)
  const ratio = trips / maxTrips

  if (ratio > 0.7) return '#dc2626' // red-600
  if (ratio > 0.4) return '#f59e0b' // amber-500
  if (ratio > 0.2) return '#10b981' // emerald-500
  return '#0ea5e9' // sky-500
}

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount || 0)
}
</script>

<style scoped>
.trip-map-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.map {
  width: 100%;
  height: 100%;
  min-height: 400px;
  border-radius: 0.5rem;
}

/* Custom popup styling */
:deep(.custom-popup .leaflet-popup-content-wrapper) {
  border-radius: 0.5rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

:deep(.custom-popup .leaflet-popup-content) {
  margin: 0.75rem;
  min-width: 200px;
}
</style>
