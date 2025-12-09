<template>
  <div class="photo-gallery min-h-screen relative" ref="galleryEl">
    <!-- Selection Header (Floating) -->
    <transition
      enter-active-class="transform ease-out duration-300 transition"
      enter-from-class="translate-y-[-100%] opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-[-100%] opacity-0"
    >
      <div 
        v-if="isSelectionMode || localSelectedIds.size > 0"
        class="fixed top-0 left-0 right-0 z-50 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md shadow-lg border-b border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center justify-between"
      >
        <div class="flex items-center gap-4">
          <button 
            @click="exitSelectionMode"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
          >
            <X class="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
          <span class="text-sm font-medium text-gray-700 dark:text-gray-200">
            已选择 {{ localSelectedIds.size }} 张照片
          </span>
        </div>
        
        <div class="flex items-center gap-2">
          <!-- Action Buttons -->
          <div class="flex items-center gap-2">
             <button 
              @click="handleDownload" 
              :disabled="localSelectedIds.size === 0 || isDownloading"
              class="p-2 text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              title="下载选中"
            >
              <Loader2 v-if="isDownloading" class="w-5 h-5 animate-spin" />
              <Download v-else class="w-5 h-5" />
            </button>
            
            <button 
              @click="handleDelete" 
              :disabled="localSelectedIds.size === 0"
              class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              :title="deleteLabel"
            >
              <Trash2 v-if="deleteLabel.includes('删除')" class="w-5 h-5" />
              <FolderMinus v-else class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Virtual Scroll Container -->
    <div :style="{ height: totalHeight + 'px', position: 'relative' }">
      <div
        v-for="block in monthBlocks"
        :key="block.key"
        :style="{ 
          position: 'absolute', 
          top: block.top + 'px', 
          left: 0, 
          width: '100%',
          height: block.height + 'px'
        }"
        class="month-block px-4"
        :data-month="block.key"
      >
        <!-- Render month content only if visible -->
        <template v-if="visibleBlockKeys.has(block.key)">
            <!-- Month Header -->
            <div class="flex items-center h-[60px] absolute top-0 left-4 right-4 z-20 pointer-events-none">
                <h3 class="text-sm font-bold text-gray-800 dark:text-gray-200 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm px-4 py-1.5 rounded-full shadow-sm border border-gray-100 dark:border-gray-800 flex items-center gap-2 pointer-events-auto cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                    @click="toggleMonthSelection(block.key)">
                    <CalendarDays class="w-4 h-4 text-primary-500" />
                    {{ block.year }}年{{ block.month }}月
                    <span class="text-xs text-gray-400 font-normal ml-1">{{ block.count }}张</span>
                </h3>
                <div class="h-px bg-gray-200 dark:bg-gray-700 flex-1 ml-4 opacity-50"></div>
            </div>

            <!-- Days Container -->
            <div
                v-for="day in block.days"
                :key="day.key"
                :style="{
                    position: 'absolute',
                    top: day.top + 'px',
                    left: 0,
                    width: '100%',
                    height: day.height + 'px'
                }"
                class="day-block"
            >
                <template v-if="visibleDayRanges.has(day.key)">
                     <!-- Day Header -->
                    <div class="h-[40px] flex items-center text-xs font-medium text-gray-500 dark:text-gray-400 pl-1">
                        {{ day.day }}日
                    </div>
                    
                    <!-- Photos Grid -->
                    <div 
                        class="grid w-full" 
                        :style="{
                            gridTemplateColumns: `repeat(${colCount}, minmax(0, 1fr))`,
                            gap: gap + 'px'
                        }"
                    >
                        <!-- Top Spacer -->
                        <div v-if="getRange(day.key).topH > 0" 
                             :style="{ gridColumn: '1 / -1', height: getRange(day.key).topH + 'px' }">
                        </div>

                        <!-- Actual Photos -->
                        <template v-if="getPhotos(day.key).length > 0">
                            <div
                                v-for="img in getPhotos(day.key).slice(getRange(day.key).start, getRange(day.key).end)"
                                :key="img.id"
                                class="relative group aspect-[3/2] bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden cursor-pointer transform transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:z-10 flex items-center justify-center"
                                @click="handlePhotoClick(img)"
                                @mouseenter="enterSelectionMode(img)"
                                @vue:mounted="loadImage(img)"
                                @vue:unmounted="cancelImageLoad(img.id)"
                            >
                                <img 
                                    :src="loadedImages[img.id] || placeholderSrc" 
                                    class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                                    :alt="img.category" 
                                />
                                
                                <!-- Selection Overlay -->
                                <div 
                                    v-if="isSelectionMode || localSelectedIds.has(img.id)"
                                    class="absolute inset-0 bg-black/20 transition-opacity duration-200 flex items-center justify-center z-20"
                                    @click.stop="toggleSelection(img)"
                                >
                                    <div 
                                    class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-200"
                                    :class="localSelectedIds.has(img.id) ? 'bg-primary-500 border-primary-500' : 'bg-black/20 border-white/70 hover:bg-black/40 backdrop-blur-sm'"
                                    >
                                    <Check v-if="localSelectedIds.has(img.id)" class="w-3.5 h-3.5 text-white" />
                                    </div>
                                </div>

                                <!-- Info Overlay -->
                                <div class="absolute inset-x-0 bottom-0 p-2 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex justify-between items-end">
                                    <p class="text-white text-xs font-medium truncate flex items-center gap-1">
                                    <MapPin v-if="img.location" class="w-3 h-3 text-white/80" />
                                    {{ img.location || formatTime(img.timestamp) }}
                                    </p>
                                    <slot name="overlay-actions" :photo="img"></slot>
                                </div>
                            </div>
                        </template>

                        <!-- Placeholders for missing photos -->
                         <template v-else>
                             <div
                                v-for="n in (getRange(day.key).end - getRange(day.key).start)"
                                :key="`ph-${day.key}-${getRange(day.key).start + n}`"
                                class="aspect-[3/2] bg-gray-50 dark:bg-gray-900/50 rounded-lg animate-pulse"
                            ></div>
                         </template>
                         
                         <!-- Bottom Spacer -->
                        <div v-if="getRange(day.key).bottomH > 0" 
                             :style="{ gridColumn: '1 / -1', height: getRange(day.key).bottomH + 'px' }">
                        </div>
                    </div>
                </template>
            </div>
        </template>
        <template v-else>
            <!-- Invisible Placeholder -->
             <div class="w-full h-full bg-gray-50/50 dark:bg-gray-900/20 rounded-lg border border-transparent"></div>
        </template>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="totalHeight === 0 && !loading" class="flex flex-col items-center justify-center py-20 text-gray-400">
        <ImageIcon class="w-16 h-16 mb-4 opacity-20" />
        <p>暂无照片</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ref, computed, watch, onMounted, onUnmounted, nextTick, toRef, reactive
} from 'vue'
import { CalendarDays, Image as ImageIcon, MapPin, Check, X, Download, Trash2, FolderMinus, Loader2 } from 'lucide-vue-next'
import { format } from 'date-fns'
import { useAlbumStore, type AlbumImage } from '@/stores/albumStore'
import type { TimelineStats } from '@/types/album'
import { useVirtualLayout, type MonthBlock, type DayBlock } from '@/composables/useVirtualLayout'
import { useWindowScroll, useDebounceFn } from '@vueuse/core'

const store = useAlbumStore()

// Props
interface Props {
  photos: AlbumImage[]
  timelineStats?: TimelineStats
  loading?: boolean
  hasMore?: boolean
  layoutMode?: 'grid' | 'masonry' | 'list'
  viewSize?: 'sm' | 'md' | 'lg'
  groupByDate?: boolean
  deleteLabel?: string
  activeDate?: string // v-model
}

const props = withDefaults(defineProps<Props>(), {
  layoutMode: 'masonry',
  viewSize: 'md',
  groupByDate: true,
  deleteLabel: '删除',
  loading: false,
  hasMore: false
})

const emit = defineEmits(['click-photo', 'load-more', 'load-range', 'update:activeDate', 'batch-delete'])

// --- Selection State ---
const isSelectionMode = ref(false)
const localSelectedIds = ref(new Set<string>())

const isDownloading = ref(false)
const downloadProgress = ref(0)

// --- Image Loading Logic ---
const loadedImages = reactive<Record<string, string>>({})
const imageLoaders = new Map<string, AbortController>()
const placeholderSrc = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'

const loadImage = async (image: AlbumImage) => {
    if (loadedImages[image.id]) return 
    if (imageLoaders.has(image.id)) return 

    const controller = new AbortController()
    imageLoaders.set(image.id, controller)

    try {
        const response = await fetch(image.thumbnail, { signal: controller.signal })
        if (response.ok) {
            loadedImages[image.id] = image.thumbnail
        }
    } catch (e: any) {
        if (e.name !== 'AbortError') {
            // console.error('Image load failed', e)
        }
    } finally {
        imageLoaders.delete(image.id)
    }
}

const cancelImageLoad = (imageId: string) => {
    const controller = imageLoaders.get(imageId)
    if (controller) {
        controller.abort()
        imageLoaders.delete(imageId)
    }
}

// Ensure cleanup on component unmount
onUnmounted(() => {
    imageLoaders.forEach(c => c.abort())
    imageLoaders.clear()
})
// --- End Image Loading Logic ---

// --- Virtual Scroll & Layout ---
const galleryEl = ref<HTMLElement | null>(null)
const containerWidth = ref(1000)

const { y: scrollTop } = useWindowScroll()
const viewportHeight = ref(window.innerHeight)

const layoutOptions = {
    timelineStats: toRef(props, 'timelineStats'),
    containerWidth,
    layoutMode: toRef(props, 'layoutMode'),
    viewSize: toRef(props, 'viewSize')
}

const { monthBlocks, totalHeight, getVisibleBlocks, recalculateLayout, colCount, rowHeight, gap } = useVirtualLayout(layoutOptions)

// Visible Blocks Calculation
const visibleBlockKeys = ref(new Set<string>())
// Map<dayKey, { start: number, end: number, topH: number, bottomH: number }>
const visibleDayRanges = ref(new Map<string, { start: number, end: number, topH: number, bottomH: number }>())
// We keep a reference to visible blocks for active date calculation
const visibleBlocksList = ref<MonthBlock[]>([])

const DAY_HEADER_HEIGHT = 40

const getRange = (key: string) => {
    return visibleDayRanges.value.get(key) || { start: 0, end: 0, topH: 0, bottomH: 0 }
}

const updateVisibleBlocks = () => {
    const buffer = 1000 // Month Buffer
    const visibleMonths = getVisibleBlocks(scrollTop.value, viewportHeight.value, buffer)
    visibleBlocksList.value = visibleMonths
    
    const newMonthKeys = new Set<string>()
    const newDayRanges = new Map<string, { start: number, end: number, topH: number, bottomH: number }>()
    
    // Dynamic Buffer for Rows: (hn + 2 + 2) * wn -> 2 rows buffer
    // But here we calculate based on pixels
    const rHeight = rowHeight.value || 200
    const rGap = gap.value || 0
    const rowUnit = rHeight + rGap
    const rowBuffer = rowUnit * 2 
    
    const startY = scrollTop.value - rowBuffer
    const endY = scrollTop.value + viewportHeight.value + rowBuffer

    visibleMonths.forEach(m => {
        newMonthKeys.add(m.key)
        
        // Check Days visibility
        m.days.forEach(d => {
            // Calculate absolute top of the day block
            const dayTopAbs = m.top + d.top
            const dayBottomAbs = dayTopAbs + d.height
            
            // Check if day is within buffer
            if (dayBottomAbs > startY && dayTopAbs < endY) {
                // Calculate visible rows within the day
                // The photos start after the header
                const photosTopAbs = dayTopAbs + DAY_HEADER_HEIGHT
                
                // Relative to photos start
                const relStart = startY - photosTopAbs
                const relEnd = endY - photosTopAbs
                
                let startRow = Math.floor(relStart / rowUnit)
                let endRow = Math.ceil(relEnd / rowUnit)
                
                // Clamp rows
                startRow = Math.max(0, startRow)
                endRow = Math.min(d.rows, endRow) // d.rows is total rows in day
                
                if (startRow < d.rows && endRow > 0) {
                     const startIndex = startRow * colCount.value
                     const endIndex = Math.min(d.count, endRow * colCount.value)
                     
                     const topH = startRow * rowUnit
                     const bottomH = Math.max(0, d.rows - endRow) * rowUnit
                     
                     newDayRanges.set(d.key, { start: startIndex, end: endIndex, topH, bottomH })
                }
            }
        })
    })

    visibleBlockKeys.value = newMonthKeys
    visibleDayRanges.value = newDayRanges
}

// Throttle scroll updates
const handleScroll = useDebounceFn(() => {
    updateVisibleBlocks()
    
    // Update active date based on first visible block
    if (visibleBlocksList.value.length > 0) {
        const center = scrollTop.value + viewportHeight.value / 2
        const current = visibleBlocksList.value.find(b => {
             return (b.top <= center) && (b.top + b.height >= center)
        }) || visibleBlocksList.value[0]

        const dateStr = `${current.year}年${String(current.month).padStart(2, '0')}月`
        if (props.activeDate !== dateStr) {
            emit('update:activeDate', dateStr)
        }
    }
}, 50, { maxWait: 100 }) // More aggressive update for row virtualization

watch(scrollTop, handleScroll)

// Resize Observer for Container Width
let resizeObserver: ResizeObserver | null = null
onMounted(() => {
    if (galleryEl.value) {
        containerWidth.value = galleryEl.value.clientWidth
        resizeObserver = new ResizeObserver((entries) => {
            const entry = entries[0]
            if (entry) {
                containerWidth.value = entry.contentRect.width
                recalculateLayout()
                updateVisibleBlocks()
            }
        })
        resizeObserver.observe(galleryEl.value)
    }
    viewportHeight.value = window.innerHeight
    window.addEventListener('resize', () => { viewportHeight.value = window.innerHeight })
    
    // Initial calculation
    updateVisibleBlocks()
})

onUnmounted(() => {
    if (resizeObserver) resizeObserver.disconnect()
})

// --- Data Fetching Logic ---
const checkAndLoadVisibleMonths = () => {
    const context = store.currentContext
    const albumId = context.type === 'album' ? context.id : undefined
    
    visibleBlocksList.value.forEach(block => {
        const key = `${block.year}-${block.month}`
        // Check if we have photos for this month
        // store uses "YYYY-MM" format in loadPhotosByMonth
        // Note: hasPhotos(key) checks props.photos. 
        if (!hasPhotosForMonth(key)) {
             store.loadPhotosByMonth(block.year, block.month, albumId)
        }
    })
}

watch(visibleBlockKeys, () => {
    checkAndLoadVisibleMonths()
}, { deep: true, immediate: true })


// --- Photo Grouping ---
const groupedPhotos = computed(() => {
    const map = new Map<string, AlbumImage[]>()
    // Group by Day Key: YYYY-MM-DD
    props.photos.forEach(p => {
        const d = new Date(p.timestamp)
        const dayKey = `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`
        if (!map.has(dayKey)) map.set(dayKey, [])
        map.get(dayKey)!.push(p)
    })
    return map
})

const hasPhotosForMonth = (monthKey: string) => {
    const block = monthBlocks.value.find(b => b.key === monthKey)
    if (!block || block.count === 0) return true // No need to load
    
    // Check if we have at least one photo for this month
    return props.photos.some(p => {
        const d = new Date(p.timestamp)
        return `${d.getFullYear()}-${d.getMonth() + 1}` === monthKey
    })
}

const getPhotos = (dayKey: string) => {
    return groupedPhotos.value.get(dayKey) || []
}

// --- Interaction Helpers ---
const scrollToDate = (date: string) => {
    // date format "YYYY年MM月" or "YYYY-MM-DD"
    const match = date.match(/(\d+)年(\d+)月/) || date.match(/(\d+)-(\d+)/)
    if (match) {
        const year = parseInt(match[1])
        const month = parseInt(match[2])
        const block = monthBlocks.value.find(b => b.year === year && b.month === month)
        if (block) {
            window.scrollTo({ top: block.top + 60, behavior: 'smooth' }) // + offset for header
        }
    }
}

const formatTime = (ts: number) => format(new Date(ts), 'yyyy-MM-dd HH:mm')

// Selection Helpers
const enterSelectionMode = (photo?: AlbumImage) => {
  // if (photo) localSelectedIds.value.add(photo.id) // Hover doesn't select automatically usually
  // But legacy code did. Let's keep manual selection.
}

const exitSelectionMode = () => {
  isSelectionMode.value = false
  localSelectedIds.value.clear()
}

const toggleSelection = (photo: AlbumImage) => {
  if (localSelectedIds.value.has(photo.id)) {
    localSelectedIds.value.delete(photo.id)
  } else {
    localSelectedIds.value.add(photo.id)
    isSelectionMode.value = true
  }
}

const toggleMonthSelection = (monthKey: string) => {
    // Select all photos in this month
    const block = monthBlocks.value.find(b => b.key === monthKey)
    if (!block) return

    let allPhotos: AlbumImage[] = []
    block.days.forEach(day => {
        allPhotos.push(...getPhotos(day.key))
    })
    
    const allSelected = allPhotos.every(p => localSelectedIds.value.has(p.id))
    
    if (allSelected) {
        allPhotos.forEach(p => localSelectedIds.value.delete(p.id))
    } else {
        allPhotos.forEach(p => localSelectedIds.value.add(p.id))
        isSelectionMode.value = true
    }
}

const handlePhotoClick = (photo: AlbumImage) => {
  if (isSelectionMode.value) {
    toggleSelection(photo)
  } else {
    emit('click-photo', photo)
  }
}

const handleDelete = () => {
    if (localSelectedIds.value.size === 0) return
    emit('batch-delete', Array.from(localSelectedIds.value))
    exitSelectionMode()
}

const handleDownload = async () => {
  if (localSelectedIds.value.size === 0) return
  isDownloading.value = true
  downloadProgress.value = 0
  
  const total = localSelectedIds.value.size
  let completed = 0
  
  for (const id of localSelectedIds.value) {
    try {
      const photo = props.photos.find(p => p.id === id)
      if (!photo) continue
      
      const response = await fetch(photo.url)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      // Extract filename or default
      a.download = photo.url.split('/').pop() || `photo-${photo.id}.jpg`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      completed++
      downloadProgress.value = Math.round((completed / total) * 100)
      
      // Small delay to ensure browser registers the download
      await new Promise(resolve => setTimeout(resolve, 200))
    } catch (error) {
      console.error('Failed to download photo:', error)
    }
  }
  
  isDownloading.value = false
  // Notification could be handled here or by parent. Component-level simple alert or toast integration if available.
  // For now, just reset.
  exitSelectionMode()
}

defineExpose({
  scrollToDate,
  enterSelectionMode,
  exitSelectionMode
})
</script>

<style scoped>
/* No scrollbar style needed as we use window scroll */
</style>