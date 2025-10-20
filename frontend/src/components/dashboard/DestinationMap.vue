<template>
  <div class="rounded-2xl bg-white p-6 shadow-sm">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">Trips by Destination</h3>
        <p class="mt-1 text-sm text-gray-600">
            {{ totalTrips }} trips across {{ topRegions.length }} regions
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-for="view in mapViews"
          :key="view.value"
          @click="selectedView = view.value"
          class="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors"
          :class="
            selectedView === view.value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          "
        >
          {{ view.label }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex h-96 items-center justify-center">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
    </div>

    <!-- Map -->
    <div v-else class="relative">
      <div id="map" class="h-96 rounded-lg shadow-inner"></div>

      <!-- Legend -->
      <div class="absolute bottom-4 right-4 rounded-lg bg-white p-4 shadow-lg">
        <p class="mb-2 text-xs font-semibold uppercase text-gray-600">Trip Volume</p>
        <div class="space-y-2">
          <div class="flex items-center gap-2">
            <div class="h-3 w-3 rounded-full bg-red-500"></div>
            <span class="text-xs text-gray-700">High (20+)</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="h-3 w-3 rounded-full bg-amber-500"></div>
            <span class="text-xs text-gray-700">Medium (10-19)</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="h-3 w-3 rounded-full bg-blue-500"></div>
            <span class="text-xs text-gray-700">Low (1-9)</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Top Regions List -->
    <div class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div
            v-for="region in topRegions"
            :key="region.region"
            class="rounded-lg border border-gray-200 p-3 hover:bg-gray-50"
            >
            <div class="mb-1 flex items-center gap-2">
            <MdiIcon 
                :path="regionIcons[region.region] || mdiEarth" 
                :size="16" 
                :class="regionColors[region.region] || 'text-gray-600'" 
            />
            <span class="text-sm font-semibold text-gray-900">{{ region.region }}</span>
            </div>
            <p class="text-xs text-gray-600">{{ region.destinations }} destinations</p>
            <p class="mt-2 text-lg font-bold" :class="regionColors[region.region] || 'text-blue-600'">
            {{ region.trips }}
            </p>
            <p class="text-xs text-gray-500">trips</p>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import MdiIcon from '@/components/ui/MdiIcon.vue'
import { mdiMapMarker, mdiEarth } from '@mdi/js'
import bookingService from '@/services/bookingService'

// Region icon mapping
const regionIcons = {
  'Asia': mdiEarth,
  'Oceania': mdiEarth,
  'Europe': mdiEarth,
  'North America': mdiEarth,
  'Middle East': mdiEarth,
  'Africa': mdiEarth,
}

// Region color mapping
const regionColors = {
  'Asia': 'text-red-600',
  'Oceania': 'text-blue-600',
  'Europe': 'text-purple-600',
  'North America': 'text-green-600',
  'Middle East': 'text-amber-600',
  'Africa': 'text-orange-600',
}

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({}),
  },
})

// Computed
const loading = ref(false)
const selectedView = ref('world')
const mapInstance = ref(null)
const destinations = ref([])
const totalTrips = ref(0)
const uniqueDestinations = ref(0)
const topDestinations = ref([])

// Aggregate to display trips by region
const topRegions = computed(() => {
  if (!destinations.value.length) return []

  // Group by region
  const regionMap = {}
  destinations.value.forEach((dest) => {
    if (!regionMap[dest.region]) {
      regionMap[dest.region] = {
        region: dest.region,
        trips: 0,
        destinations: 0,
      }
    }
    regionMap[dest.region].trips += dest.trips
    regionMap[dest.region].destinations += 1
  })

  // Convert to array and sort by trips
  return Object.values(regionMap)
    .sort((a, b) => b.trips - a.trips)
    .slice(0, 4) // Top 4 regions
})

const mapViews = [
  { label: 'World', value: 'world' },
  { label: 'Asia Pacific', value: 'apac' },
]

// Sample destination data with coordinates
const destinationCoordinates = {
  'Sydney': { lat: -33.8688, lng: 151.2093, country: 'Australia', region: 'Oceania' },
  'Melbourne': { lat: -37.8136, lng: 144.9631, country: 'Australia', region: 'Oceania' },
  'Brisbane': { lat: -27.4698, lng: 153.0251, country: 'Australia', region: 'Oceania' },
  'Perth': { lat: -31.9505, lng: 115.8605, country: 'Australia', region: 'Oceania' },
  'Auckland': { lat: -36.8485, lng: 174.7633, country: 'New Zealand', region: 'Oceania' },
  'Singapore': { lat: 1.3521, lng: 103.8198, country: 'Singapore', region: 'Asia' },
  'Tokyo': { lat: 35.6762, lng: 139.6503, country: 'Japan', region: 'Asia' },
  'Hong Kong': { lat: 22.3193, lng: 114.1694, country: 'Hong Kong', region: 'Asia' },
  'Los Angeles': { lat: 34.0522, lng: -118.2437, country: 'United States', region: 'North America' },
  'London': { lat: 51.5074, lng: -0.1278, country: 'United Kingdom', region: 'Europe' },
  'Bangkok': { lat: 13.7563, lng: 100.5018, country: 'Thailand', region: 'Asia' },
  'Dubai': { lat: 25.2048, lng: 55.2708, country: 'United Arab Emirates', region: 'Middle East' },
}

// Initialize map
const initMap = async () => {
  // Wait for next tick to ensure DOM is ready
  await nextTick()
  
  // Check if element exists
  const mapElement = document.getElementById('map')
  if (!mapElement) {
    console.error('Map container not found')
    return
  }

  if (mapInstance.value) {
    mapInstance.value.remove()
  }

  // Create map
  const map = L.map('map', {
    zoomControl: true,
    scrollWheelZoom: true,
  })

  // Set view based on selected region
  if (selectedView.value === 'world') {
    map.setView([20, 0], 2)
  } else if (selectedView.value === 'apac') {
    map.setView([10, 120], 4)
  }

  // Add tile layer (map style)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap contributors © CARTO',
    subdomains: 'abcd',
    maxZoom: 19,
  }).addTo(map)

  mapInstance.value = map

  // Add markers
  addMarkers()
}

// Add markers to map
const addMarkers = () => {
  if (!mapInstance.value || !destinations.value.length) return

  destinations.value.forEach((destination) => {
    const coords = destinationCoordinates[destination.city]
    if (!coords) return

    // Determine marker color based on trip volume
    let markerColor = '#3B82F6' // Blue - low
    if (destination.trips >= 20) {
      markerColor = '#EF4444' // Red - high
    } else if (destination.trips >= 10) {
      markerColor = '#F59E0B' // Amber - medium
    }

    // Create custom icon
    const icon = L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="
          background-color: ${markerColor};
          width: ${Math.min(12 + destination.trips, 40)}px;
          height: ${Math.min(12 + destination.trips, 40)}px;
          border-radius: 50%;
          border: 3px solid white;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 10px;
          font-weight: bold;
        ">
          ${destination.trips > 9 ? destination.trips : ''}
        </div>
      `,
      iconSize: [Math.min(12 + destination.trips, 40), Math.min(12 + destination.trips, 40)],
    })

    // Add marker
    const marker = L.marker([coords.lat, coords.lng], { icon }).addTo(mapInstance.value)

    // Add tooltip (shows on hover) - FIXED: options as second parameter
    marker.bindTooltip(
      `
      <div style="text-align: center;">
        <strong>${destination.city}</strong><br>
        ${coords.country}<br>
        <span style="color: ${markerColor}; font-weight: bold; font-size: 16px;">
          ${destination.trips} trips
        </span>
      </div>
      `,
      {
        permanent: false,
        direction: 'top',
        offset: [0, -10],
        className: 'custom-tooltip',
      }
    )

    // Optional: Still allow click to open persistent popup
    marker.bindPopup(`
      <div style="text-align: center;">
        <strong>${destination.city}</strong><br>
        ${coords.country}<br>
        <span style="color: ${markerColor}; font-weight: bold; font-size: 16px;">
          ${destination.trips} trips
        </span>
      </div>
    `)
  })
}

// Load destination data
const loadDestinations = async () => {
  try {
    loading.value = true

    const params = {}
    if (props.filters.dateRange && props.filters.dateRange.length === 2) {
      params.start_date = props.filters.dateRange[0].toISOString().split('T')[0]
      params.end_date = props.filters.dateRange[1].toISOString().split('T')[0]
    }
    if (props.filters.organization) {
      params.organization = props.filters.organization
    }

    // Fetch bookings and aggregate by destination
    // For now, use mock data - in production, aggregate from bookings API
    destinations.value = [
      { city: 'Sydney', trips: 45, country: 'Australia', region: 'Oceania' },
      { city: 'Melbourne', trips: 38, country: 'Australia', region: 'Oceania' },
      { city: 'Singapore', trips: 28, country: 'Singapore', region: 'Asia' },
      { city: 'Tokyo', trips: 22, country: 'Japan', region: 'Asia' },
      { city: 'Hong Kong', trips: 19, country: 'Hong Kong', region: 'Asia' },
      { city: 'Auckland', trips: 15, country: 'New Zealand', region: 'Oceania' },
      { city: 'Brisbane', trips: 12, country: 'Australia', region: 'Oceania' },
      { city: 'Bangkok', trips: 11, country: 'Thailand', region: 'Asia' },
      { city: 'London', trips: 8, country: 'United Kingdom', region: 'Europe' },
      { city: 'Los Angeles', trips: 6, country: 'United States', region: 'North America' },
      { city: 'Dubai', trips: 5, country: 'United Arab Emirates', region: 'Middle East' },
      { city: 'Perth', trips: 4, country: 'Australia', region: 'Oceania' },
    ]

    // Calculate totals
    totalTrips.value = destinations.value.reduce((sum, d) => sum + d.trips, 0)
    uniqueDestinations.value = destinations.value.length

    // Get top 4 destinations
    topDestinations.value = destinations.value
      .sort((a, b) => b.trips - a.trips)
      .slice(0, 4)

    loading.value = false

    // Initialize map after data is loaded and loading is false
    await nextTick()
    await initMap()
  } catch (error) {
    console.error('Error loading destinations:', error)
    loading.value = false
  }
}

// Watch for view changes
watch(selectedView, () => {
  if (mapInstance.value) {
    initMap()
  }
})

// Watch for filter changes
watch(() => props.filters, () => {
  loadDestinations()
}, { deep: true })

// Lifecycle
onMounted(() => {
  loadDestinations()
})

defineExpose({
  refresh: loadDestinations,
})
</script>

<style scoped>
/* Leaflet map styling */
:deep(.leaflet-container) {
  font-family: inherit;
}

:deep(.leaflet-popup-content-wrapper) {
  border-radius: 8px;
}

:deep(.leaflet-popup-content) {
  margin: 12px;
}
</style>