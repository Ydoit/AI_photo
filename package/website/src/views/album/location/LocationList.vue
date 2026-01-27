<template>
  <div :class="['container mx-auto location-list min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col h-screen relative', (viewMode === 'map') ? 'p-0' : 'px-6']">
    <!-- Header -->
    <div :class="['flex sm:flex-row justify-between items-start sm:items-center gap-4 flex-shrink-0 z-50 transition-all duration-300', (viewMode === 'map') ? 'absolute top-0 left-0 right-0 p-4 pointer-events-none' : 'mb-6']">
      <div class="flex flex-col gap-3 pointer-events-auto">
        <div class="flex items-center gap-3 w-full md:w-auto bg-white/80 dark:bg-gray-900/80 backdrop-blur-md px-1 py-1.5 rounded-full shadow-sm border border-gray-200/50 dark:border-gray-700/50">
          <button @click="router.back()" class="p-0 md:p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors bg-white dark:bg-gray-900">
            <ArrowLeft class="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
          <h1 class="text-xl md:text-2xl font-bold text-gray-800 dark:text-white">位置相册</h1>
        </div>

        <!-- Stats Block -->
        <div v-if="viewMode === 'map' && statistics" class="self-start bg-white/80 dark:bg-gray-900/80 backdrop-blur-md px-4 py-2.5 rounded-xl shadow-sm border border-gray-200/50 dark:border-gray-700/50 transition-all">
           <div class="text-sm font-bold text-gray-800 dark:text-white">
              累计点亮 <span class="text-primary-500 text-base">{{ statistics.province_count }}</span> 省 <span class="text-primary-500 text-base">{{ statistics.city_count }}</span> 市
           </div>
           <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              已解锁 {{ unlockPercentage }}%
           </div>
        </div>
      </div>

      <div class="pointer-events-auto flex items-center gap-1 md:gap-3">
        <!-- Level Toggle -->
        <div class="bg-gray-200 dark:bg-gray-800 p-0 md:p-1 rounded-lg flex relative" ref="levelMenuRef">
          <!-- Mobile Dropdown Trigger -->
          <button
            @click="showLevelMenu = !showLevelMenu"
            class="md:hidden px-3 py-1.5 rounded-md text-sm font-medium bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white flex items-center gap-1.5"
          >
            {{ currentLevelLabel }}
            <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': showLevelMenu }" />
          </button>

          <!-- Mobile Dropdown Menu -->
          <div
            v-show="showLevelMenu"
            class="md:hidden absolute top-full left-0 mt-2 w-32 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden z-[60]"
          >
            <button
              v-for="opt in levelOptions"
              :key="opt.value"
              @click="changeLevel(opt.value as any); showLevelMenu = false"
              :class="['w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors', level === opt.value ? 'text-primary-500 font-medium' : 'text-gray-700 dark:text-gray-200']"
            >
              {{ opt.label }}
            </button>
            <div class="h-px bg-gray-200 dark:bg-gray-700 my-1"></div>
            <button
               v-show="viewMode !== 'grid'"
               @click="level = 'photo-map'; showLevelMenu = false"
               :class="['w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center gap-2', level === 'photo-map' ? 'text-primary-500 font-medium' : 'text-gray-700 dark:text-gray-200']"
            >
               <Images class="w-4 h-4" />
               地图照片
            </button>
          </div>

          <!-- Desktop Buttons -->
          <div class="hidden md:flex">
            <button
              @click="changeLevel('district')"
              :class="['px-4 py-1.5 rounded-md text-sm font-medium transition-all bg-white dark:bg-gray-700', level === 'district' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700']"
            >
              区县
            </button>
            <button
              @click="changeLevel('city')"
              :class="['px-4 py-1.5 rounded-md text-sm font-medium transition-all bg-white dark:bg-gray-700', level === 'city' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700']"
            >
              城市
            </button>
            <button
              @click="changeLevel('province')"
              :class="['px-4 py-1.5 rounded-md text-sm font-medium transition-all bg-white dark:bg-gray-700', level === 'province' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700']"
            >
              省份
            </button>
            <button
              @click="changeLevel('scene')"
              :class="['px-4 py-1.5 rounded-md text-sm font-medium transition-all bg-white dark:bg-gray-700', level === 'scene' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700']"
            >
              景区
            </button>
          </div>

          <div v-show="viewMode !== 'grid'" class="hidden md:block w-px h-4 bg-gray-300 dark:bg-gray-600 mx-1 my-auto"></div>

          <button
            v-if="level === 'scene'"
            @click="editingScene = null; showAddScene = true"
            class="px-3 py-1.5 rounded-md bg-primary-500 text-white hover:bg-primary-600 transition-colors flex items-center gap-1.5 ml-1"
            title="新增景区"
          >
            <Plus class="w-4 h-4" />
            <span class="hidden sm:inline">新增</span>
          </button>

          <button
            v-show="viewMode !== 'grid'"
            @click="level = 'photo-map'"
            :class="['hidden md:flex px-3 py-1.5 rounded-md text-sm font-medium transition-all items-center gap-1.5', level === 'photo-map' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700']"
            title="地图照片"
          >
            <Images class="w-4 h-4" />
            <span class="hidden sm:inline">照片</span>
          </button>
        </div>
        <!-- View Toggle -->
        <div class="bg-gray-200 dark:bg-gray-800 p-1 rounded-lg flex">
          <button
            @click="viewMode = 'grid'"
            :class="['p-1.5 rounded-md transition-all  bg-white dark:bg-gray-700', viewMode === 'grid' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700']"
            title="网格视图"
          >
            <LayoutGrid class="w-4 h-4" />
          </button>
          <button
            @click="viewMode = 'map'"
            :class="['p-1.5 rounded-md transition-all  bg-white dark:bg-gray-700', viewMode === 'map' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700']"
            title="地图视图"
          >
            <Map class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Map View -->
    <div v-show="viewMode === 'map' && level !== 'photo-map' && level !== 'scene'" class="flex-1 relative overflow-hidden bg-white dark:bg-gray-900 shadow-sm">
       <div ref="mapContainer" class="w-full h-full"></div>
       
       <!-- Map Controls Overlay -->
       <div class="absolute bottom-6 right-6 flex flex-col gap-2">
          <!-- Add any custom map controls here if needed -->
       </div>
    </div>

    <!-- Photo Map View -->
    <LocationMap v-if="viewMode === 'map' && (level === 'photo-map' || level === 'scene')" class="flex-1 overflow-hidden bg-white dark:bg-gray-900 shadow-sm" />

    <!-- Grid View -->
    <div v-show="viewMode === 'grid'" class="flex-1 overflow-y-auto">
      <!-- Loading State -->
      <div v-if="loading" class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-12 gap-6">
        <div v-for="i in 10" :key="i" class="flex flex-col">
          <div class="w-full aspect-square bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse"></div>
          <div class="mt-3 h-4 bg-gray-200 dark:bg-gray-800 rounded w-2/3 animate-pulse"></div>
          <div class="mt-1 h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/3 animate-pulse"></div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="locations.length === 0" class="flex flex-col items-center justify-center h-[50vh] text-gray-500">
        <div class="p-6 rounded-full bg-gray-100 dark:bg-gray-900 mb-4">
          <MapPin class="w-12 h-12 opacity-20" />
        </div>
        <p class="text-lg font-medium">暂无位置信息</p>
      </div>

      <!-- Content Grid -->
      <div v-else class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-12 gap-6">
        <div
          v-for="loc in locations"
          :key="loc.name"
          class="group cursor-pointer flex flex-col"
          @click="goToLocation(loc.name)"
        >
          <div class="relative w-full aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 shadow-sm group-hover:shadow-md transition-all duration-300">
             <button
                v-if="level === 'scene' && loc.id"
                @click.stop="handleEdit(loc)"
                class="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full shadow-sm hover:bg-white transition-all opacity-0 group-hover:opacity-100 z-10 text-gray-600 hover:text-primary-500"
                title="编辑景区"
             >
                <Pencil class="w-4 h-4" />
             </button>
             <img
               v-if="loc.cover"
               :src="mapPhotoToImage(loc.cover).thumbnail"
               class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
               loading="lazy"
             />
             <div v-else class="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-600">
               <MapPin class="w-12 h-12" />
             </div>
             
             <!-- Overlay -->
             <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors"></div>
          </div>

          <div class="mt-2.5 px-1">
            <h3 class="font-semibold text-gray-900 dark:text-white truncate" :title="loc.name">
              {{ loc.name }}
            </h3>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {{ loc.count }} 个项目
            </p>
          </div>
        </div>
      </div>
    </div>
    
    <AddSceneDialog v-model="showAddScene" :edit-data="editingScene" @success="fetchLocations" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useLocationStore } from '@/stores/locationStore'
import { locationService } from '@/api/location'
import { mapPhotoToImage } from '@/stores/photoStore'
import type { Location, LocationStatistics, Scene } from '@/types/location'
import { ArrowLeft, MapPin, LayoutGrid, Map, Images, Plus, ChevronDown, Pencil } from 'lucide-vue-next'
import * as echarts from 'echarts'
import { useDark, onClickOutside } from '@vueuse/core'
import LocationMap from './LocationMap.vue'
import AddSceneDialog from './AddSceneDialog.vue'

const router = useRouter()
const isDark = useDark()
const locationStore = useLocationStore()
const { level, viewMode } = storeToRefs(locationStore)
const locations = ref<Location[]>([])
const statistics = ref<LocationStatistics | null>(null)
const loading = ref(true)
const showAddScene = ref(false)
const editingScene = ref<Scene | null>(null)
const mapContainer = ref<HTMLElement | null>(null)
let myMap: echarts.ECharts | null = null
let zoomTimer: any = null
const showLevelMenu = ref(false)
const levelMenuRef = ref<HTMLElement | null>(null)

onClickOutside(levelMenuRef, () => {
  showLevelMenu.value = false
})

const levelOptions = [
  { label: '区县', value: 'district' },
  { label: '城市', value: 'city' },
  { label: '省份', value: 'province' },
  { label: '景区', value: 'scene' }
]

const currentLevelLabel = computed(() => {
  if (level.value === 'photo-map') return '照片'
  const option = levelOptions.find(opt => opt.value === level.value)
  return option ? option.label : '区县'
})

const unlockPercentage = computed(() => {
  if (!statistics.value) return 0
  // 34 provincial administrative divisions in China
  return Math.min(Math.round((statistics.value.province_count / 34) * 100), 100)
})

// Fetch data for Grid View
const fetchLocations = async () => {
  loading.value = true
  try {
    // Fetch stats
    statistics.value = await locationService.getStatistics()

    if (level.value === 'photo-map') {
      locations.value = await locationService.getLocations('city')
      return
    }
    locations.value = await locationService.getLocations(level.value)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const changeLevel = (newLevel: 'city' | 'province' | 'district' | 'scene', viewState?: { zoom: number, center: number[] }) => {
  console.log(newLevel, viewState, level.value)
  if (level.value === newLevel) return
  level.value = newLevel
  fetchLocations()
  if (viewMode.value === 'map') {
    nextTick(() => {
      initMap(viewState)
    })
  }
}

const goToLocation = (name: string) => {
  router.push({
    name: 'LocationDetail',
    params: { name: name },
    query: { level: level.value }
  })
}

const handleEdit = async (loc: Location) => {
  if (!loc.id) return
  try {
    const scene = await locationService.getScene(loc.id)
    editingScene.value = scene
    showAddScene.value = true
  } catch (e) {
    console.error(e)
  }
}

// --- Map Logic ---

const initMap = async (viewState?: { zoom: number, center: number[] }) => {
  if (!mapContainer.value) return

  // Dispose existing instance if any
  if (myMap) {
    myMap.dispose()
  }

  myMap = echarts.init(mapContainer.value)
  myMap.showLoading()

  try {
    if (level.value === 'photo-map') return
    // 1. Fetch GeoJSON
    const geoResponse = await fetch(`/api/medias/geojson?level=${level.value}`)
    if (!geoResponse.ok) throw new Error('Failed to load GeoJSON')
    const geoJson = await geoResponse.json()
    echarts.registerMap('china', geoJson)

    // 2. Fetch Distribution Data
    const distribution = await locationService.getDistribution(level.value)
    
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
        goToLocation(params.name)
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
          
          // if (level.value === 'province' && zoom > 2.5) {
          //    changeLevel('city', { zoom, center })
          // } else if (level.value === 'city' && zoom < 1.5) {
          //    changeLevel('province', { zoom, center })
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
watch(viewMode, (newMode) => {
  if (newMode === 'map') {
    nextTick(() => {
      initMap()
    })
  } else if (level.value === 'photo-map') {
    level.value = 'city'
  }
})

watch(isDark, () => {
  if (viewMode.value === 'map' && myMap) {
    // Re-render to update colors
    // We need data again. Ideally store data in a ref.
    // For simplicity, just re-init.
    initMap()
  }
})

// Resize handler
const handleResize = () => {
  myMap?.resize()
}

onMounted(() => {
  fetchLocations()
  if (viewMode.value === 'map' && level.value !== 'photo-map') {
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

<style scoped>
/* Optional transitions */
</style>
