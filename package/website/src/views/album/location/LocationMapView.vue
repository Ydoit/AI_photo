<template>
  <div class="flex-1 relative overflow-hidden bg-white dark:bg-gray-900 shadow-sm">
     <div ref="mapContainer" class="w-full h-full"></div>
     
     <!-- Map Controls Overlay -->
     <div class="absolute bottom-6 right-6 flex flex-col gap-2">
        <!-- Add any custom map controls here if needed -->
     </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useDark } from '@vueuse/core'
import { locationService } from '@/api/location'

const props = defineProps<{
  level: string
  viewMode: string
}>()

const emit = defineEmits<{
  (e: 'click-location', name: string): void
  (e: 'change-level', level: string, viewState: { zoom: number, center: number[] }): void
}>()

const mapContainer = ref<HTMLElement | null>(null)
let myMap: echarts.ECharts | null = null
let zoomTimer: any = null
const isDark = useDark()

const initMap = async (viewState?: { zoom: number, center: number[] }) => {
  if (!mapContainer.value) return

  // Dispose existing instance if any
  if (myMap) {
    myMap.dispose()
  }

  myMap = echarts.init(mapContainer.value)
  myMap.showLoading()

  try {
    if (props.level === 'photo-map') return
    // 1. Fetch GeoJSON
    const geoResponse = await fetch(`/api/medias/geojson?level=${props.level}`)
    if (!geoResponse.ok) throw new Error('Failed to load GeoJSON')
    const geoJson = await geoResponse.json()
    echarts.registerMap('china', geoJson)

    // 2. Fetch Distribution Data
    const distribution = await locationService.getDistribution(props.level as 'city' | 'province' | 'district' | 'scene' | undefined)
    
    // 3. Prepare Data
    const data = distribution.map(item => ({
      name: item.name,
      value: item.count,
      // Ensure specific style for each item if needed, but visualMap handles it
    }))
    
    // Calculate 90th percentile to handle outliers for better color distribution
    const values = data.map(d => d.value).sort((a, b) => a - b)
    const p90 = values[Math.floor(values.length * 0.9)] || 10
    const maxVal = Math.max(...values, 10)
    // Use p90 as visual max, but allow real max to be shown
    const visualMax = maxVal > p90 * 2 ? p90 * 1.5 : maxVal

    renderMap(data, visualMax, viewState)
    myMap.hideLoading()

    // 4. Bind Events
    myMap.on('click', (params) => {
      if (params.name) {
        emit('click-location', params.name)
      }
    })

    // Zoom event for level switching
    myMap.on('georoam', () => {
      if (zoomTimer) clearTimeout(zoomTimer)
      zoomTimer = setTimeout(() => {
        const option = myMap?.getOption() as any
        if (option && option.geo && option.geo[0]) {
          const zoom = option.geo[0].zoom
          const center = option.geo[0].center
          
          // if (props.level === 'province' && zoom > 2.5) {
          //    emit('change-level', 'city', { zoom, center })
          // } else if (props.level === 'city' && zoom < 1.5) {
          //    emit('change-level', 'province', { zoom, center })
          // }
        }
      }, 300)
    })

  } catch (e) {
    console.error('Map init failed', e)
    myMap?.hideLoading()
  }
}

const renderMap = (data: any[], max: number, viewState?: { zoom: number, center: number[] }) => {
  if (!myMap) return

  const isDarkMode = isDark.value
  const isMobile = window.innerWidth < 768

  // High contrast palette: Deep Blue -> Cyan -> Green -> Yellow
  // Designed to be visible on both Light and Dark themes
  const colors = [
    '#3b82f6', // Blue 500
    '#06b6d4', // Cyan 500
    '#10b981', // Emerald 500
    '#84cc16', // Lime 500
    '#facc15', // Yellow 400
  ]

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (!params.value) return params.name
        return `
          <div class="font-bold">${params.name}</div>
          <div class="text-sm">照片数量: ${params.value}</div>
        `
      },
      backgroundColor: isDarkMode ? 'rgba(30, 41, 59, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: isDarkMode ? '#475569' : '#e2e8f0',
      textStyle: {
        color: isDarkMode ? '#f1f5f9' : '#1e293b'
      }
    },
    visualMap: {
      min: 1, // Start from 1 so 0 is not colored (treated as empty)
      max: max,
      left: isMobile ? 'center' : 'left',
      bottom: isMobile ? 20 : 30,
      orient: isMobile ? 'horizontal' : 'vertical',
      text: ['高', '低'],
      calculable: true, // Show handles
      inRange: {
        color: colors,
        // Ensure opacity is high enough for visibility
        opacity: [0.7, 1] 
      },
      textStyle: {
        color: isDarkMode ? '#cbd5e1' : '#475569'
      },
      // Ensure the legend is large enough
      itemWidth: isMobile ? 15 : 20,
      itemHeight: isMobile ? 100 : 140
    },
    geo: {
      map: 'china',
      roam: true,
      zoom: viewState?.zoom || 1.2,
      center: viewState?.center || undefined,
      label: {
        show: false
      },
      itemStyle: {
        // Distinct color for empty regions
        areaColor: isDarkMode ? '#1e293b' : '#f1f5f9',
        borderColor: isDarkMode ? '#334155' : '#cbd5e1',
        borderWidth: 1
      },
      emphasis: {
        itemStyle: {
          areaColor: isDarkMode ? '#334155' : '#e2e8f0',
          // Highlight border on hover
          borderColor: isDarkMode ? '#94a3b8' : '#64748b',
          borderWidth: 2
        },
        label: {
          show: true,
          color: isDarkMode ? '#fff' : '#0f172a'
        }
      }
    },
    series: [
      {
        name: '照片数量',
        type: 'map',
        geoIndex: 0,
        data: data,
        // Add specific border to data items to make them pop against empty regions
        itemStyle: {
          borderColor: isDarkMode ? '#334155' : '#fff',
          borderWidth: 0.5
        }
      }
    ],
    // 工具栏：保存为图片
    toolbox: {
      show: true,
      right: isMobile ? 10 : 20,
      top: 20,
      feature: {
        saveAsImage: {
          title: '保存为图片',
          name: '位置分布图',
          backgroundColor: isDarkMode ? '#0f172a' : '#ffffff',
          excludeComponents: ['toolbox'],
          pixelRatio: isMobile ? 5 : 3,
        }
      },
      iconStyle: {
        borderColor: isDarkMode ? '#cbd5e1' : '#475569'
      },
      emphasis: {
        iconStyle: {
          borderColor: isDarkMode ? '#fff' : '#0f172a'
        }
      }
    }
  }

  myMap.setOption(option)
}

// Watchers
watch(() => props.viewMode, (newMode) => {
  if (newMode === 'map') {
    nextTick(() => {
      initMap()
    })
  }
})

// When level changes, we might need to re-init if we are in map view
watch(() => props.level, (newLevel) => {
  if (props.viewMode === 'map' && newLevel !== 'photo-map' && newLevel !== 'scene') {
      initMap()
  }
})

watch(isDark, () => {
  if (props.viewMode === 'map' && myMap) {
    initMap()
  }
})

// Resize handler
const handleResize = () => {
  myMap?.resize()
}

onMounted(() => {
  if (props.viewMode === 'map' && props.level !== 'photo-map') {
    nextTick(() => {
      initMap()
    })
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  myMap?.dispose()
})
</script>
