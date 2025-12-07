<template>
  <div class="photo-gallery relative min-h-[500px]">
    <!-- Batch Action Bar -->
    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="transform -translate-y-full opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="transform translate-y-0 opacity-100"
      leave-to-class="transform -translate-y-full opacity-0"
    >
      <div v-if="isSelectionMode" class="fixed bottom-[70px] left-0 right-0 z-40 flex justify-center pointer-events-none">
        <div class="bg-white/90 dark:bg-gray-900/90 backdrop-blur-md border border-gray-200 dark:border-gray-700 shadow-lg rounded-full px-6 py-3 flex items-center gap-6 pointer-events-auto min-w-[320px]">
          <div class="flex items-center gap-3">
            <button @click="exitSelectionMode" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors" title="取消选择">
              <X class="w-5 h-5 text-gray-600 dark:text-gray-300" />
            </button>
            <span class="font-medium text-gray-900 dark:text-white whitespace-nowrap">
              已选择 {{ localSelectedIds.size }} 张
            </span>
          </div>

          <div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>

          <div class="flex items-center gap-2">
            <button @click="toggleSelectAll" class="px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
              {{ isAllSelected ? '取消全选' : '全选' }}
            </button>
            
            <!-- Custom Batch Actions Slot -->
            <slot name="batch-actions" :selected-ids="localSelectedIds" :clear-selection="exitSelectionMode"></slot>

            <!-- Download Action -->
            <button 
              @click="handleDownload" 
              :disabled="localSelectedIds.size === 0 || isDownloading"
              class="p-2 text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed relative group"
              title="保存到本地"
            >
              <Loader2 v-if="isDownloading" class="w-5 h-5 animate-spin" />
              <Download v-else class="w-5 h-5" />
              <!-- Progress Tooltip -->
              <div v-if="isDownloading" class="absolute -bottom-8 left-1/2 -translate-x-1/2 bg-black/80 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                {{ downloadProgress }}%
              </div>
            </button>

            <!-- Delete/Remove Action -->
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

    <!-- Timeline View (Grouped by Date) -->
    <div v-if="groupByDate" class="space-y-8">
      <div 
        v-for="(group, date) in groupedImages" 
        :key="date" 
        :id="`group-${date}`"
        class="scroll-mt-32 group-container"
      >
        <!-- Date Header -->
        <div class="flex items-center mb-4 sticky top-[130px] z-20 py-2 transition-opacity duration-300 pointer-events-none">
          <h3 class="text-sm font-bold text-gray-800 dark:text-gray-200 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm px-4 py-1.5 rounded-full shadow-sm border border-gray-100 dark:border-gray-800 flex items-center gap-2 pointer-events-auto cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
              @click="toggleGroupSelection(group)">
            <CalendarDays class="w-4 h-4 text-primary-500" />
            {{ date }}
            <span v-if="isSelectionMode" class="ml-2 text-xs font-normal text-gray-500">
              (点击{{ isGroupSelected(group) ? '取消' : '全选' }})
            </span>
          </h3>
          <div class="h-px bg-gray-200 dark:bg-gray-700 flex-1 ml-4"></div>
        </div>

        <!-- Images Grid -->
        <div :class="['transition-all duration-300 ease-in-out', currentGridClass]">
          <div
            v-for="img in group"
            :key="img.id"
            class="group relative bg-gray-100 dark:bg-gray-800 overflow-hidden rounded-xl shadow-sm hover:shadow-md transition-all duration-300 select-none"
            :class="{
              'aspect-square': layoutMode === 'grid',
              'mb-4': layoutMode === 'masonry',
              'ring-4 ring-primary-500 ring-offset-2 dark:ring-offset-gray-900': localSelectedIds.has(img.id)
            }"
            @click="handlePhotoClick(img)"
            @longpress="enterSelectionMode(img)"
          >
            <!-- List View Content -->
            <div v-if="layoutMode === 'list'" class="flex gap-4 p-3">
              <div class="w-24 h-24 flex-shrink-0 bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden relative">
                 <img 
                    v-observe-image="img.id"
                    :src="loadedImageIds.has(img.id) ? img.thumbnail : ''" 
                    class="w-full h-full object-cover transition-opacity duration-300"
                    :class="{ 'opacity-100': loadedImageIds.has(img.id), 'opacity-0': !loadedImageIds.has(img.id) }"
                  />
                  <!-- Selection Overlay for List -->
                  <div v-if="isSelectionMode" class="absolute inset-0 bg-black/20 flex items-center justify-center">
                    <div class="w-6 h-6 rounded-full border-2 border-white flex items-center justify-center"
                      :class="{ 'bg-primary-500 border-primary-500': localSelectedIds.has(img.id) }">
                      <Check v-if="localSelectedIds.has(img.id)" class="w-4 h-4 text-white" />
                    </div>
                  </div>
                  <!-- Video Indicator (List View) -->
                  <div v-if="img.file_type === 'video'" class="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
                    <PlayCircle class="w-8 h-8 text-white drop-shadow-md opacity-90" />
                  </div>
              </div>
              <div class="flex-1 py-1">
                 <div class="flex justify-between items-start">
                   <p class="text-sm font-medium text-gray-900 dark:text-gray-100 line-clamp-2">{{ img.location || '未知地点' }}</p>
                   <span v-if="img.city" class="text-[10px] px-1.5 py-0.5 bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400 rounded-full">{{ img.city }}</span>
                 </div>
                 <p class="text-xs text-gray-500 flex items-center gap-1 mt-1">
                   <CalendarDays class="w-3 h-3" />
                   {{ formatTime(img.timestamp) }}
                 </p>
              </div>
            </div>

            <!-- Grid/Masonry View Content -->
            <template v-else>
              <div v-if="!loadedImageIds.has(img.id)" class="absolute inset-0 flex items-center justify-center z-0">
                <ImageIcon class="w-8 h-8 text-gray-300 dark:text-gray-600 opacity-50" />
              </div>
              
              <!-- Image with Lazy Load & LRU Cache -->
              <img
                v-observe-image="img.id"
                :src="loadedImageIds.has(img.id) ? img.thumbnail : ''"
                :srcset="loadedImageIds.has(img.id) ? img.srcset : ''"
                alt="photo"
                class="w-full h-full object-cover transform transition-transform duration-700 group-hover:scale-110 transition-opacity duration-500 relative z-10"
                :class="{ 'opacity-100': loadedImageIds.has(img.id), 'opacity-0': !loadedImageIds.has(img.id) }"
                loading="lazy"
              />
              
              <!-- Video Indicator -->
              <div v-if="img.file_type === 'video'" class="absolute inset-0 flex items-center justify-center pointer-events-none z-20">
                <div class="bg-black/20 backdrop-blur-[2px] rounded-full p-3 group-hover:bg-black/40 transition-colors">
                  <PlayCircle class="w-8 h-8 text-white opacity-90" />
                </div>
              </div>

              <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300 z-20"></div>
              
              <!-- Selection Checkbox -->
              <div 
                class="absolute top-2 left-2 z-30 transition-all duration-200"
                :class="{ 
                  'opacity-100 scale-100': isSelectionMode || localSelectedIds.has(img.id),
                  'opacity-0 scale-90 group-hover:opacity-100 group-hover:scale-100': !isSelectionMode && !localSelectedIds.has(img.id)
                }"
                @click.stop="toggleSelection(img)"
              >
                <div class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all shadow-sm"
                  :class="localSelectedIds.has(img.id) ? 'bg-primary-500 border-primary-500' : 'bg-black/20 border-white/70 hover:bg-black/40 backdrop-blur-sm'"
                >
                  <Check v-if="localSelectedIds.has(img.id)" class="w-3.5 h-3.5 text-white" />
                </div>
              </div>

              <!-- Overlay Actions Slot (Only show when not in selection mode) -->
              <div v-if="!isSelectionMode" class="absolute top-2 right-2 z-30 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <slot name="overlay-actions" :photo="img"></slot>
              </div>
              
              <!-- Bottom Info Gradient -->
              <div v-if="!isSelectionMode" class="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/60 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-20">
                <p class="text-white text-xs font-medium truncate flex items-center gap-1">
                  <MapPin v-if="img.location" class="w-3 h-3 text-white/80" />
                  {{ img.location || formatTime(img.timestamp) }}
                </p>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Flat View (No Date Grouping) -->
    <div v-else :class="['transition-all duration-300 ease-in-out', currentGridClass]">
      <!-- ... similar update for flat view ... -->
      <div
        v-for="img in photos"
        :key="img.id"
        class="group relative bg-gray-100 dark:bg-gray-800 overflow-hidden rounded-xl shadow-sm hover:shadow-md transition-all duration-300 select-none"
        :class="{
          'aspect-square': layoutMode === 'grid',
          'mb-4': layoutMode === 'masonry',
          'ring-4 ring-primary-500 ring-offset-2 dark:ring-offset-gray-900': localSelectedIds.has(img.id)
        }"
        @click="handlePhotoClick(img)"
      >
        <!-- Simplified for brevity, assuming similar structure to grouped view -->
         <div v-if="!loadedImageIds.has(img.id)" class="absolute inset-0 flex items-center justify-center z-0">
            <ImageIcon class="w-8 h-8 text-gray-300 dark:text-gray-600 opacity-50" />
          </div>
          <img
            v-observe-image="img.id"
            :src="loadedImageIds.has(img.id) ? img.thumbnail : ''"
            class="w-full h-full object-cover transform transition-transform duration-700 group-hover:scale-110 transition-opacity duration-500 relative z-10"
            :class="{ 'opacity-100': loadedImageIds.has(img.id), 'opacity-0': !loadedImageIds.has(img.id) }"
          />
          
          <!-- Video Indicator -->
          <div v-if="img.file_type === 'video'" class="absolute inset-0 flex items-center justify-center pointer-events-none z-20">
            <div class="bg-black/20 backdrop-blur-[2px] rounded-full p-3 group-hover:bg-black/40 transition-colors">
              <PlayCircle class="w-8 h-8 text-white opacity-90" />
            </div>
          </div>

           <!-- Selection Checkbox -->
          <div 
            class="absolute top-2 left-2 z-30 transition-all duration-200"
            :class="{ 
              'opacity-100 scale-100': isSelectionMode || localSelectedIds.has(img.id),
              'opacity-0 scale-90 group-hover:opacity-100 group-hover:scale-100': !isSelectionMode && !localSelectedIds.has(img.id)
            }"
            @click.stop="toggleSelection(img)"
          >
            <div class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all shadow-sm"
              :class="localSelectedIds.has(img.id) ? 'bg-primary-500 border-primary-500' : 'bg-black/20 border-white/70 hover:bg-black/40 backdrop-blur-sm'"
            >
              <Check v-if="localSelectedIds.has(img.id)" class="w-3.5 h-3.5 text-white" />
            </div>
          </div>
      </div>
    </div>

    <!-- Sentinel / Loading -->
    <div ref="sentinel" class="h-10 w-full flex justify-center items-center py-4 mt-4">
       <slot name="footer">
         <div v-if="loading" class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500"></div>
         <span v-else-if="!hasMore && photos.length > 0" class="text-gray-400 text-xs">没有更多照片了</span>
         <span v-else-if="!hasMore && photos.length === 0" class="text-gray-400 text-xs">暂无照片</span>
       </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch, reactive } from 'vue'
import { CalendarDays, Image as ImageIcon, MapPin, Check, X, Download, Trash2, FolderMinus, Loader2, PlayCircle } from 'lucide-vue-next'
import { format } from 'date-fns'
import type { AlbumImage } from '@/stores/albumStore'

// Props
interface Props {
  photos: AlbumImage[]
  loading?: boolean
  hasMore?: boolean
  layoutMode?: 'grid' | 'masonry' | 'list'
  viewSize?: 'sm' | 'md' | 'lg'
  groupByDate?: boolean
  // Batch Actions Config
  deleteLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  hasMore: false,
  layoutMode: 'masonry',
  viewSize: 'md',
  groupByDate: true,
  deleteLabel: '删除'
})

// Emits
const emit = defineEmits<{
  (e: 'load-more'): void
  (e: 'click-photo', photo: AlbumImage): void
  (e: 'update:active-date', date: string): void
  (e: 'batch-delete', ids: string[]): void
}>()

// --- Selection Logic ---
const isSelectionMode = ref(false)
const localSelectedIds = reactive(new Set<string>())


// --- Logic from PhotosPage.vue ---

// Performance & Cache Config
const MAX_LOADED_IMAGES = 80 // Increased slightly
const loadedImageIds = reactive(new Set<string>())
const visibleImageIds = new Set<string>()
const imageCache = new Map<string, number>()
let imageObserver: IntersectionObserver | null = null
const pendingImages = new Set<HTMLElement>()
const sentinel = ref<HTMLElement | null>(null)
let scrollObserver: IntersectionObserver | null = null
let groupObserver: IntersectionObserver | null = null

// Image LRU Cache Logic
const loadImage = (id: string) => {
  if (!loadedImageIds.has(id)) {
    loadedImageIds.add(id)
  }
  imageCache.set(id, Date.now())
  pruneCache()
}

const pruneCache = () => {
  if (loadedImageIds.size <= MAX_LOADED_IMAGES) return
  const candidates = Array.from(loadedImageIds).filter(id => !visibleImageIds.has(id))
  candidates.sort((a, b) => (imageCache.get(a) || 0) - (imageCache.get(b) || 0))
  const removeCount = loadedImageIds.size - MAX_LOADED_IMAGES
  for (let i = 0; i < removeCount && i < candidates.length; i++) {
    const idToRemove = candidates[i]
    loadedImageIds.delete(idToRemove)
    imageCache.delete(idToRemove)
  }
}

// Directive
const vObserveImage = {
  mounted: (el: HTMLElement, binding: any) => {
    el.dataset.id = String(binding.value)
    if (imageObserver) {
      imageObserver.observe(el)
    } else {
      pendingImages.add(el)
    }
  },
  unmounted: (el: HTMLElement) => {
    if (imageObserver) imageObserver.unobserve(el)
    pendingImages.delete(el)
  }
}

// Computed Groups
const groupedImages = computed(() => {
  if (!props.groupByDate) return {}
  const groups: Record<string, AlbumImage[]> = {}
  const sorted = [...props.photos].sort((a, b) => b.timestamp - a.timestamp)
  sorted.forEach(img => {
    const date = format(new Date(img.timestamp), 'yyyy年MM月')
    if (!groups[date]) groups[date] = []
    groups[date].push(img)
  })
  return groups
})

// Grid Classes
const getGridClass = (size: string, mode: string) => {
  if (mode === 'list') return 'flex flex-col gap-3'
  if (mode === 'grid') {
    const base = 'grid '
    switch (size) {
      case 'sm': return base + 'grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-12 gap-2'
      case 'md': return base + 'grid-cols-3 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 gap-2'
      case 'lg': return base + 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4'
    }
  } else {
    // Masonry
    const base = 'block '
    switch (size) {
      case 'sm': return base + 'columns-4 sm:columns-6 md:columns-8 lg:columns-12 gap-2 space-y-2'
      case 'md': return base + 'columns-3 sm:columns-5 md:columns-6 lg:columns-8 gap-2 space-y-2'
      case 'lg': return base + 'columns-2 sm:columns-3 md:columns-4 lg:columns-6 gap-4 space-y-4'
    }
  }
  return ''
}
const currentGridClass = computed(() => getGridClass(props.viewSize, props.layoutMode))

// Helpers
const formatTime = (ts: number) => format(new Date(ts), 'yyyy-MM-dd HH:mm')


const enterSelectionMode = (photo?: AlbumImage) => {
  isSelectionMode.value = true
  if (photo) localSelectedIds.add(photo.id)
}

const exitSelectionMode = () => {
  isSelectionMode.value = false
  localSelectedIds.clear()
}

const toggleSelection = (photo: AlbumImage) => {
  if (localSelectedIds.has(photo.id)) {
    localSelectedIds.delete(photo.id)
    if (localSelectedIds.size === 0 && !isSelectionMode.value) {
      // If triggered from hover state without explicit mode
    }
  } else {
    localSelectedIds.add(photo.id)
    if (!isSelectionMode.value) isSelectionMode.value = true
  }
}

const handlePhotoClick = (photo: AlbumImage) => {
  if (isSelectionMode.value) {
    toggleSelection(photo)
  } else {
    emit('click-photo', photo)
  }
}

// Exposed Method for Timeline Scrolling
const scrollToDate = (date: string) => {
  const el = document.getElementById(`group-${date}`)
  if (el) {
    const offset = 180
    const bodyRect = document.body.getBoundingClientRect().top
    const elementRect = el.getBoundingClientRect().top
    const elementPosition = elementRect - bodyRect
    const offsetPosition = elementPosition - offset

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    })
    emit('update:active-date', date)
  }
}

// Observers Setup
onMounted(() => {
  // Image Observer
  imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const id = entry.target.getAttribute('data-id')
      if (!id) return
      if (entry.isIntersecting) {
        visibleImageIds.add(id)
        loadImage(id)
      } else {
        visibleImageIds.delete(id)
      }
    })
  }, { rootMargin: '50% 0px 50% 0px', threshold: 0 })

  if (pendingImages.size > 0) {
    pendingImages.forEach(el => imageObserver!.observe(el))
    pendingImages.clear()
  }

  // Infinite Scroll Observer
  scrollObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && props.hasMore && !props.loading) {
      emit('load-more')
    }
  }, { rootMargin: '200px', threshold: 0.1 })
  
  if (sentinel.value) scrollObserver.observe(sentinel.value)

  // Group Observer (for Active Date)
  if (props.groupByDate) {
    setupGroupObserver()
  }
})

const setupGroupObserver = () => {
  if (groupObserver) groupObserver.disconnect()
  
  groupObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id
        if (id) {
          emit('update:active-date', id.replace('group-', ''))
        }
      }
    })
  }, { rootMargin: '-20% 0px -70% 0px', threshold: 0 })

  nextTick(() => {
    document.querySelectorAll('.group-container').forEach(el => groupObserver?.observe(el))
  })
}

// Watchers
watch(groupedImages, () => {
  if (props.groupByDate) {
    nextTick(setupGroupObserver)
  }
}, { deep: true })

watch(() => props.groupByDate, (val) => {
  if (val) nextTick(setupGroupObserver)
  else groupObserver?.disconnect()
})

onUnmounted(() => {
  imageObserver?.disconnect()
  scrollObserver?.disconnect()
  groupObserver?.disconnect()
})

const isAllSelected = computed(() => {
  return props.photos.length > 0 && localSelectedIds.size === props.photos.length
})

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    localSelectedIds.clear()
  } else {
    props.photos.forEach(p => localSelectedIds.add(p.id))
  }
}

const toggleGroupSelection = (groupPhotos: AlbumImage[]) => {
  if (!isSelectionMode.value) isSelectionMode.value = true
  
  const allSelected = groupPhotos.every(p => localSelectedIds.has(p.id))
  if (allSelected) {
    groupPhotos.forEach(p => localSelectedIds.delete(p.id))
  } else {
    groupPhotos.forEach(p => localSelectedIds.add(p.id))
  }
}

const isGroupSelected = (groupPhotos: AlbumImage[]) => {
  return groupPhotos.length > 0 && groupPhotos.every(p => localSelectedIds.has(p.id))
}

// --- Batch Actions ---

const handleDelete = () => {
  emit('batch-delete', Array.from(localSelectedIds))
  exitSelectionMode()
}

// Download Logic
const isDownloading = ref(false)
const downloadProgress = ref(0)

const handleDownload = async () => {
  if (localSelectedIds.size === 0) return
  
  isDownloading.value = true
  downloadProgress.value = 0
  
  const selectedPhotos = props.photos.filter(p => localSelectedIds.has(p.id))
  const total = selectedPhotos.length
  let completed = 0

  // Sequential download to avoid browser throttling/blocking
  for (const photo of selectedPhotos) {
    try {
      const response = await fetch(photo.url)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
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
      console.error('Failed to download photo:', photo.id, error)
    }
  }
  
  isDownloading.value = false
  // Notification could be handled here or by parent. Component-level simple alert or toast integration if available.
  // For now, just reset.
  exitSelectionMode()
}

// Expose methods
defineExpose({
  scrollToDate,
  enterSelectionMode,
  exitSelectionMode
})

// --- Existing Logic (Preserved) ---

</script>

<style scoped>
/* Reuse scrollbar hiding if needed, or rely on global CSS */
</style>
