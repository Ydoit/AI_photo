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
import { onMounted, onUnmounted, ref } from 'vue'
// @ts-ignore  缺少 supercluster 类型声明，暂时忽略
import Supercluster from 'supercluster'
import { locationService } from '@/api/location'
import { useRouter } from 'vue-router'
import { useLocationStore } from '@/stores/locationStore'
import { loadMapScript } from '@/utils/mapLoader'
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

onMounted(async () => {
  try {
    await loadMapScript()
    initMap()
    await loadData()
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

const initMap = () => {
  if (map.value) return
  
  map.value = new T.Map('tianditu-map')
  map.value.centerAndZoom(new T.LngLat(104.195, 35.861), 4) // Center of China
  map.value.enableScrollWheelZoom()
  
  // Listen to move/zoom events
  map.value.addEventListener('moveend', updateClusters)
  map.value.addEventListener('zoomend', updateClusters)
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
