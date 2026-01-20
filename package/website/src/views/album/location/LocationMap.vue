<template>
  <div class="relative w-full h-full">
    <div id="tianditu-map" class="w-full h-full z-10 overflow-hidden"></div>
    
    <!-- Loading Overlay -->
    <div v-if="loading" class="absolute inset-0 z-50 flex items-center justify-center bg-white/50 backdrop-blur-sm">
      <div class="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
// @ts-ignore  缺少 supercluster 类型声明，暂时忽略
import Supercluster from 'supercluster'
import { locationService } from '@/api/location'
import { useRouter } from 'vue-router'
import { useLocationStore } from '@/stores/locationStore'
import { loadMapScript } from '@/utils/mapLoader'
import { storeToRefs } from 'pinia'
import { ElMessageBox, ElMessage } from 'element-plus'

// Declare T globally
declare const T: any

const map = ref<any>(null)
const loading = ref(false)
const index = new Supercluster({
  radius: 60,
  maxZoom: 18
})
const router = useRouter()
const locationStore = useLocationStore()
const { level } = storeToRefs(locationStore)

onMounted(async () => {
  try {
    await loadMapScript()
    initMap()
    await loadContent()
  } catch (e: any) {
    if (e.code === 'MAP_KEY_MISSING') {
      ElMessageBox.confirm(
        '查看地图照片需要配置地图 API Key。是否立即前往设置？',
        '缺少配置',
        {
          confirmButtonText: '去设置',
          cancelButtonText: '取消',
          type: 'warning',
        }
      ).then(() => {
        router.push('/settings#basic')
      }).catch(() => {
        // User cancelled
      })
    } else {
      ElMessage.error('地图加载失败: ' + e.message)
    }
  }
})

watch(level, async (newVal) => {
  if (!map.value) return
  map.value.clearOverLays()
  await loadContent()
})

const initMap = () => {
  if (map.value) return
  
  map.value = new T.Map('tianditu-map')
  map.value.centerAndZoom(new T.LngLat(104.195, 35.861), 4) // Center of China
  map.value.enableScrollWheelZoom()
}

const scenesData = ref<any[]>([])

const loadContent = async () => {
  // Remove listeners first to avoid conflicts
  if (map.value) {
      map.value.removeEventListener('moveend', updateClusters)
      map.value.removeEventListener('zoomend', updateClusters)
      map.value.removeEventListener('zoomend', renderScenes)
  }

  if (level.value === 'scene') {
    if (map.value) {
        map.value.addEventListener('zoomend', renderScenes)
    }
    await loadScenes()
  } else {
    // Add listeners for clusters
    if (map.value) {
        map.value.addEventListener('moveend', updateClusters)
        map.value.addEventListener('zoomend', updateClusters)
    }
    await loadData()
  }
}

const loadScenes = async () => {
  loading.value = true
  try {
    scenesData.value = await locationService.getScenesList()
    
    if (scenesData.value.length === 0) {
      ElMessage.info('暂无景区数据')
      return
    }

    renderScenes()
    
    // Fit view to scenes if any
    if (scenesData.value.length > 0) {
       const first = scenesData.value[0]
       if (first.latitude && first.longitude) {
           map.value.panTo(new T.LngLat(first.longitude, first.latitude))
       }
    }

  } catch (e) {
    console.error('Failed to load scenes:', e)
  } finally {
    loading.value = false
  }
}

const renderScenes = () => {
  if (!map.value || !scenesData.value) return
  map.value.clearOverLays()

  const zoom = map.value.getZoom()
  const showPolygon = zoom >= 12

  scenesData.value.forEach((scene: any) => {
    const hasPhotos = scene.photo_count && scene.photo_count > 0
    const hasPolygon = scene.polygon && scene.polygon.length > 0
    
    // Determine center point
    let centerPt = null
    if (scene.latitude && scene.longitude) {
        centerPt = new T.LngLat(scene.longitude, scene.latitude)
    } else if (hasPolygon) {
        centerPt = new T.LngLat(scene.polygon[0][1], scene.polygon[0][0])
    }
    
    if (!centerPt) return

    const createLabel = (position: any, offset: any) => {
      const label = new T.Label({
        text: `<div class="px-2 py-1 bg-white/90 rounded shadow text-sm font-medium ${hasPhotos ? 'text-blue-600' : 'text-gray-600'}">${scene.name}</div>`,
        position: position,
        offset: offset
      })
      label.setBackgroundColor("transparent")
      label.setBorderLine(0)
      return label
    }

    const handleClick = () => goToScene(scene.name)

    // Always draw Marker
    const marker = new T.Marker(centerPt)
    map.value.addOverLay(marker)
    marker.addEventListener('click', handleClick)

    // Create Label
    const label = createLabel(centerPt, new T.Point(0, -25))
    label.addEventListener('click', handleClick)

    // Helper to manage label visibility
    const showLabel = () => map.value.addOverLay(label)
    const hideLabel = () => map.value.removeOverLay(label)

    // Label Visibility Logic
    if (hasPhotos) {
      // Always show if has photos
      showLabel()
    } else {
      // Show on hover if no photos
      marker.addEventListener('mouseover', showLabel)
      marker.addEventListener('mouseout', hideLabel)
    }

    // Draw Polygon if needed
    if (hasPolygon && showPolygon) {
        const points = scene.polygon.map((p: any) => new T.LngLat(p[1], p[0]))
        const polygon = new T.Polygon(points, {
          color: "#3b82f6", 
          weight: 3, 
          opacity: 0.8, 
          fillColor: "#3b82f6", 
          fillOpacity: 0.2
        })
        map.value.addOverLay(polygon)
        
        polygon.addEventListener('click', handleClick)

        // Add hover logic to polygon only if label is not permanent
        if (!hasPhotos) {
          polygon.addEventListener('mouseover', showLabel)
          polygon.addEventListener('mouseout', hideLabel)
        }
    }
  })
}

const goToScene = (name: string) => {
  router.push({
    name: 'LocationDetail',
    params: { name: name },
    query: { level: 'scene' }
  })
}

const loadData = async () => {
  loading.value = true
  try {
    const rawMarkers = await locationService.getMapMarkers()
    // Convert to GeoJSON features
    const points = rawMarkers.map(m => ({
      type: 'Feature' as const,
      properties: { 
        cluster: false, 
        photoId: m.id,
        thumbnail: `/api/medias/${m.id}/thumbnail` 
      },
      geometry: {
        type: 'Point' as const,
        coordinates: [m.lng, m.lat]
      }
    }))
    
    if (points.length === 0) {
      console.warn('No photo markers found.')
    }

    index.load(points)
    
    // Slight delay to ensure map bounds are ready
    setTimeout(() => {
        updateClusters()
    }, 100)
    
  } catch (e) {
    console.error('Failed to load map data:', e)
  } finally {
    loading.value = false
  }
}

const updateClusters = () => {
  if (!map.value) return

  const bounds = map.value.getBounds()
  const sw = bounds.getSouthWest()
  const ne = bounds.getNorthEast()
  const zoom = map.value.getZoom()
  map.value.clearOverLays()

  const bbox = [sw.getLng(), sw.getLat(), ne.getLng(), ne.getLat()] as [number, number, number, number]

  const clusters = index.getClusters(bbox, zoom)

  clusters.forEach((cluster: any) => {
    const [lng, lat] = cluster.geometry.coordinates
    const isCluster = cluster.properties.cluster
    const count = cluster.properties.point_count || 1

    // Get cover photo
    let coverUrl = ''
    let photoId = ''
    if (isCluster) {
      // Get leaves to find a cover photo
      const leaves = index.getLeaves(cluster.id, 1)
      coverUrl = leaves[0].properties.thumbnail
      photoId = leaves[0].properties.photoId // Just one of them
    } else {
      coverUrl = cluster.properties.thumbnail
      photoId = cluster.properties.photoId
    }

    // Create custom marker using T.Label
    // We use a div with background image and inline styles to ensure rendering
    const iconHtml = `
      <div class="map-marker-cluster" style="position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);">
        <div style="width: 44px; height: 44px; border-radius: 8px; border: 2px solid white; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); overflow: hidden; background-color: #e5e7eb;">
          <img src="${coverUrl}" style="width: 100%; height: 100%; object-fit: cover; display: block;" onerror="this.parentElement.style.backgroundColor='#e5e7eb'; this.style.display='none';" />
        </div>
        ${count > 1 ? `<div style="position: absolute; top: -6px; right: -6px; background-color: #ef4444; color: white; font-size: 11px; font-weight: 600; padding: 0 5px; height: 18px; line-height: 16px; border-radius: 9px; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); min-width: 18px; text-align: center;">${count}</div>` : ''}
      </div>
    `
    
    const label = new T.Label({
      text: iconHtml,
      position: new T.LngLat(lng, lat),
      offset: new T.Point(-22, -22)
    })
    
    label.setBackgroundColor("transparent")
    label.setBorderLine(0)
    label.setTitle(count > 1 ? `${count} photos` : 'Photo')
    
    // Removed JS hover listeners to fix "label.getObject is not a function" error
    // Hover effect is now handled by CSS
    
    label.addEventListener('click', () => {
      if (isCluster) {
        // If it's a cluster, check zoom. 
        // Optimized: Open detail earlier (zoom > 16) to avoid excessive clicking
        const expansionZoom = index.getClusterExpansionZoom(cluster.id)
        
        openClusterDetail(cluster.id)
      } else {
        // Single photo
        openPhotoDetail(photoId)
      }
    })
    
    map.value.addOverLay(label)
  })
}

const openClusterDetail = (clusterId: number) => {
  // Get all leaves
  const leaves = index.getLeaves(clusterId, Infinity)
  const ids = leaves.map((l: any) => l.properties.photoId)
  
  // Store IDs in store and navigate
  locationStore.setMapSelection(ids)
  router.push({
    name: 'LocationDetail',
    params: { name: 'map_selection' },
    query: { title: '地图精选' }
  })
}

const openPhotoDetail = (photoId: string) => {
  locationStore.setMapSelection([photoId])
  router.push({
    name: 'LocationDetail',
    params: { name: 'map_selection' },
    query: { title: '地图照片' }
  })
}

onUnmounted(() => {
  if (map.value) {
    // map.value.destroy() // Tianditu might not have destroy, usually safe to leave
  }
})
</script>

<style>
/* Ensure label doesn't have default styles interfering */
.tdt-label {
  box-shadow: none !important;
}

.map-marker-cluster:hover {
  transform: scale(1.15);
  z-index: 9999;
}
</style>
