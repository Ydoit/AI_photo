<template>
  <div class="container mx-auto px-4 py-1 pb-24 min-h-screen">
    <!-- Toolbar & Header -->
    <div class="sticky top-[60px] z-30 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md py-3 -mx-4 px-4 border-b border-gray-100 dark:border-gray-800 shadow-sm transition-all duration-300">
      <div class="flex flex-col md:flex-row items-center justify-between gap-4 max-w-7xl mx-auto">
        
        <!-- Back & Title -->
        <div class="flex items-center gap-3 w-full md:w-auto">
          <button @click="router.back()" class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <ArrowLeft class="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
          <div>
            <h1 class="text-lg font-bold text-gray-900 dark:text-white leading-tight">所有照片</h1>
            <p class="text-xs text-gray-500">{{ images.length }} 张照片</p>
          </div>
        </div>

        <!-- Controls -->
        <div class="flex items-center gap-4 ml-auto animate-in fade-in slide-in-from-right-4 duration-300">
          
          <!-- View Size -->
          <div class="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button 
              @click="viewSize = 'sm'" 
              class="p-1.5 rounded hover:bg-white dark:hover:bg-gray-700 transition-colors"
              :class="{ 'text-primary-500 bg-white dark:bg-gray-700 shadow-sm': viewSize === 'sm', 'text-gray-500': viewSize !== 'sm' }"
              title="小图"
            >
              <Grid3x3 class="w-4 h-4" />
            </button>
            <button 
              @click="viewSize = 'md'" 
              class="p-1.5 rounded hover:bg-white dark:hover:bg-gray-700 transition-colors"
              :class="{ 'text-primary-500 bg-white dark:bg-gray-700 shadow-sm': viewSize === 'md', 'text-gray-500': viewSize !== 'md' }"
              title="中图"
            >
              <Grid2x2 class="w-4 h-4" />
            </button>
            <button 
              @click="viewSize = 'lg'" 
              class="p-1.5 rounded hover:bg-white dark:hover:bg-gray-700 transition-colors"
              :class="{ 'text-primary-500 bg-white dark:bg-gray-700 shadow-sm': viewSize === 'lg', 'text-gray-500': viewSize !== 'lg' }"
              title="大图"
            >
              <Maximize class="w-4 h-4" />
            </button>
          </div>

          <div class="w-px h-6 bg-gray-200 dark:bg-gray-700"></div>

          <!-- Layout Mode -->
          <div class="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button 
              @click="layoutMode = 'masonry'" 
              class="p-1.5 rounded hover:bg-white dark:hover:bg-gray-700 transition-colors flex items-center gap-2 px-3"
              :class="{ 'text-primary-500 bg-white dark:bg-gray-700 shadow-sm': layoutMode === 'masonry', 'text-gray-500': layoutMode !== 'masonry' }"
            >
              <LayoutDashboard class="w-4 h-4" />
              <span class="text-xs font-medium hidden sm:inline">瀑布流</span>
            </button>
            <button 
              @click="layoutMode = 'grid'" 
              class="p-1.5 rounded hover:bg-white dark:hover:bg-gray-700 transition-colors flex items-center gap-2 px-3"
              :class="{ 'text-primary-500 bg-white dark:bg-gray-700 shadow-sm': layoutMode === 'grid', 'text-gray-500': layoutMode !== 'grid' }"
            >
              <LayoutGrid class="w-4 h-4" />
              <span class="text-xs font-medium hidden sm:inline">正方形</span>
            </button>
            <button 
              @click="layoutMode = 'list'" 
              class="p-1.5 rounded hover:bg-white dark:hover:bg-gray-700 transition-colors flex items-center gap-2 px-3"
              :class="{ 'text-primary-500 bg-white dark:bg-gray-700 shadow-sm': layoutMode === 'list', 'text-gray-500': layoutMode !== 'list' }"
            >
              <LayoutList class="w-4 h-4" />
              <span class="text-xs font-medium hidden sm:inline">列表</span>
            </button>
          </div>

          <!-- Upload Button -->
          <button 
            @click="triggerUpload"
            class="bg-primary-500 hover:bg-primary-600 text-white px-4 py-1.5 rounded-lg flex items-center gap-2 text-sm font-medium transition-all active:scale-95 shadow-md shadow-primary-500/20"
          >
            <UploadCloud class="w-4 h-4" />
            <span class="hidden sm:inline">上传</span>
          </button>
          <input type="file" ref="fileInput" class="hidden" accept="image/*" @change="handleUpload" />

        </div>
      </div>
    </div>

    <!-- Timeline Navigation Sidebar (Right Sticky) -->
    <AlbumTimeline
      :dates="Object.keys(groupedImages)"
      :active-date="activeDate"
      @select="scrollToDate"
    />

    <!-- Main Content Area -->
    <div class="mt-6 relative min-h-[500px]">
      
      <!-- Timeline View -->
      <div class="space-y-8">
        <div 
          v-for="(group, date) in groupedImages" 
          :key="date" 
          :id="`group-${date}`"
          class="scroll-mt-32 group-container"
        >
          <!-- Date Header -->
          <div class="flex items-center mb-4 sticky top-[130px] z-20 py-2 transition-opacity duration-300">
            <h3 class="text-sm font-bold text-gray-800 dark:text-gray-200 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm px-4 py-1.5 rounded-full shadow-sm border border-gray-100 dark:border-gray-800 flex items-center gap-2">
              <CalendarDays class="w-4 h-4 text-primary-500" />
              {{ date }}
            </h3>
            <div class="h-px bg-gray-200 dark:bg-gray-700 flex-1 ml-4"></div>
          </div>

          <!-- Images Grid -->
          <div 
            :class="[
              'transition-all duration-300 ease-in-out',
              currentGridClass
            ]"
          >
            <div
              v-for="img in group"
              :key="img.id"
              class="group relative cursor-zoom-in overflow-hidden bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-all duration-300 break-inside-avoid"
              :class="[
                layoutMode === 'list' 
                  ? 'flex items-center gap-4 p-3 rounded-xl' 
                  : 'rounded-xl mb-4',
                layoutMode === 'grid' ? 'aspect-square mb-0' : ''
              ]"
              @click="openLightbox(img)"
            >
              <!-- List View: Thumbnail -->
              <div 
                v-if="layoutMode === 'list'"
                class="w-24 h-24 sm:w-32 sm:h-32 shrink-0 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 relative"
              >
                <img
                  v-observe-image="img.id"
                  :src="loadedImageIds.has(img.id) ? img.thumbnail : ''"
                  class="w-full h-full object-cover"
                  :class="{ 'opacity-100': loadedImageIds.has(img.id), 'opacity-0': !loadedImageIds.has(img.id) }"
                />
              </div>

              <!-- List View: Info -->
              <div v-if="layoutMode === 'list'" class="flex-1 min-w-0 py-1">
                <div class="flex items-start justify-between mb-2">
                  <div>
                    <div class="flex items-center gap-2 mb-1">
                       <span class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">IMG_{{ img.id }}</span>
                       <span v-if="img.city" class="text-[10px] px-1.5 py-0.5 bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400 rounded-full">{{ img.city }}</span>
                    </div>
                    <p class="text-xs text-gray-500 flex items-center gap-1">
                      <CalendarDays class="w-3 h-3" />
                      {{ formatTime(img.timestamp) }}
                    </p>
                    <p v-if="img.location" class="text-xs text-gray-400 mt-1 flex items-center gap-1">
                      <MapPin class="w-3 h-3" />
                      {{ img.location }}
                    </p>
                  </div>
                </div>
                
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="tag in img.tags" :key="tag" class="text-xs text-gray-500 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full">
                    {{ tag }}
                  </span>
                </div>
              </div>

              <!-- Grid/Masonry View Content -->
              <template v-else>
                <div v-if="!loadedImageIds.has(img.id)" class="absolute inset-0 flex items-center justify-center z-0">
                  <ImageIcon class="w-8 h-8 text-gray-300 dark:text-gray-600 opacity-50" />
                </div>
                <img
                  v-observe-image="img.id"
                  :src="loadedImageIds.has(img.id) ? img.thumbnail : ''"
                  :srcset="loadedImageIds.has(img.id) ? img.srcset : ''"
                  :alt="img.tags.join(', ')"
                  class="w-full h-full object-cover transform transition-transform duration-700 group-hover:scale-110 transition-opacity duration-500 relative z-10"
                  :class="{ 'opacity-100': loadedImageIds.has(img.id), 'opacity-0': !loadedImageIds.has(img.id) }"
                />
                <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300 z-20"></div>
                
                <!-- Smart Tags Overlay -->
                <div class="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/70 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 translate-y-2 group-hover:translate-y-0 z-20">
                  <div class="flex flex-wrap gap-1.5">
                    <span v-for="tag in img.tags.slice(0, 2)" :key="tag" class="text-[10px] font-medium text-white bg-white/20 px-2 py-0.5 rounded-full backdrop-blur-md border border-white/10">
                      {{ tag }}
                    </span>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Performance Monitor -->
    <div class="fixed bottom-6 left-6 z-50 bg-black/70 text-white px-3 py-1.5 rounded-full text-xs font-mono flex items-center gap-2 backdrop-blur-md border border-white/10 pointer-events-none select-none">
      <Activity class="w-3 h-3 text-green-400" />
      <span>{{ fps }} FPS</span>
      <span class="text-gray-500">|</span>
      <span :class="loadedImageIds.size >= MAX_LOADED_IMAGES ? 'text-yellow-400' : 'text-blue-400'">
        {{ loadedImageIds.size }} Loaded
      </span>
    </div>

    <!-- Upload Progress Toast -->
    <Transition name="slide-up">
      <div v-if="isUploading" class="fixed bottom-6 right-6 z-50 bg-white dark:bg-gray-800 shadow-xl rounded-xl p-4 border border-gray-100 dark:border-gray-700 w-80 flex items-center gap-4">
        <div class="relative flex items-center justify-center">
          <Loader2 class="w-8 h-8 text-primary-500 animate-spin" />
          <span class="absolute text-[10px] font-bold text-primary-600 dark:text-primary-400">{{ uploadProgress }}%</span>
        </div>
        <div class="flex-1">
          <h4 class="text-sm font-bold text-gray-800 dark:text-gray-200">正在上传照片...</h4>
          <div class="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-1.5 mt-2 overflow-hidden">
            <div class="bg-primary-500 h-full transition-all duration-300" :style="{ width: `${uploadProgress}%` }"></div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Lightbox -->
    <Transition name="fade">
      <div v-if="lightboxImage" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/95 backdrop-blur-sm" @click="closeLightbox">
        <button class="absolute top-6 right-6 text-white/70 hover:text-white p-2 rounded-full hover:bg-white/10 transition-colors z-[101]">
          <X class="w-8 h-8" />
        </button>
        
        <div class="relative max-w-7xl w-full h-full flex flex-col items-center justify-center p-4" @click.stop>
          <img
            :src="lightboxImage.url"
            class="max-w-full max-h-[85vh] object-contain shadow-2xl rounded-lg"
          />
          
          <div class="mt-6 text-center">
             <div class="flex justify-center gap-2 mb-2">
               <span v-for="tag in lightboxImage.tags" :key="tag" class="text-xs font-medium text-white bg-primary-500/80 px-3 py-1 rounded-full backdrop-blur-md">
                 {{ tag }}
               </span>
             </div>
             <p class="text-gray-400 font-mono">{{ formatTime(lightboxImage.timestamp) }}</p>
             <div v-if="lightboxImage.city || lightboxImage.location" class="text-gray-500 text-xs mt-1">
               {{ lightboxImage.location || lightboxImage.city }}
             </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAlbumStore, type AlbumImage } from '@/stores/albumStore'
import { 
  X, Maximize2, Grid3x3, Grid2x2, Maximize, LayoutDashboard, LayoutGrid, LayoutList,
  UploadCloud, Loader2, CalendarDays, ArrowLeft, Image as ImageIcon, Activity, MapPin
} from 'lucide-vue-next'
import AlbumTimeline from '@/components/AlbumTimeline.vue'
import { format } from 'date-fns'

const router = useRouter()
const store = useAlbumStore()

// State
const images = computed(() => store.images)

// Performance & Cache Config
const MAX_LOADED_IMAGES = 60
const loadedImageIds = reactive(new Set<number>())
const visibleImageIds = new Set<number>()
const imageCache = new Map<number, number>()
let imageObserver: IntersectionObserver | null = null
const pendingImages = new Set<HTMLElement>()

// FPS Monitoring
const fps = ref(60)
let frameCount = 0
let lastTime = performance.now()
let rafId: number | null = null

const updateFps = () => {
  const now = performance.now()
  frameCount++
  if (now - lastTime >= 1000) {
    fps.value = Math.round((frameCount * 1000) / (now - lastTime))
    frameCount = 0
    lastTime = now
  }
  rafId = requestAnimationFrame(updateFps)
}

// Image LRU Cache Logic
const loadImage = (id: number) => {
  if (!loadedImageIds.has(id)) {
    loadedImageIds.add(id)
  }
  imageCache.set(id, Date.now())
  pruneCache()
}

const pruneCache = () => {
  if (loadedImageIds.size <= MAX_LOADED_IMAGES) return
  
  // Find candidates (loaded but NOT visible)
  const candidates = Array.from(loadedImageIds).filter(id => !visibleImageIds.has(id))
  
  // Sort by LRU (oldest usage time first)
  candidates.sort((a, b) => (imageCache.get(a) || 0) - (imageCache.get(b) || 0))
  
  // Remove oldest
  const removeCount = loadedImageIds.size - MAX_LOADED_IMAGES
  for (let i = 0; i < removeCount && i < candidates.length; i++) {
    const idToRemove = candidates[i]
    loadedImageIds.delete(idToRemove)
    imageCache.delete(idToRemove)
  }
}

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

// UI State
const viewSize = ref<'sm' | 'md' | 'lg'>('md')
const layoutMode = ref<'masonry' | 'grid' | 'list'>('masonry')
const isUploading = ref(false)
const uploadProgress = ref(0)
const activeDate = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const lightboxImage = ref<AlbumImage | null>(null)

// Computed Data
const groupedImages = computed(() => {
  const groups: Record<string, AlbumImage[]> = {}
  // Use store images
  const sorted = [...images.value].sort((a, b) => b.timestamp - a.timestamp)
  sorted.forEach(img => {
    const date = format(new Date(img.timestamp), 'yyyy年MM月')
    if (!groups[date]) groups[date] = []
    groups[date].push(img)
  })
  return groups
})

// Layout Logic
const getGridClass = (size: string, mode: string) => {
  if (mode === 'list') return 'flex flex-col gap-3'
  
  if (mode === 'grid') {
    const base = 'grid '
    switch (size) {
      case 'sm': return base + 'grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 gap-2'
      case 'md': return base + 'grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2'
      case 'lg': return base + 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4'
    }
  } else {
    // Masonry (Columns)
    const base = 'block '
    switch (size) {
      case 'sm': return base + 'columns-4 sm:columns-5 md:columns-6 lg:columns-8 gap-2 space-y-2'
      case 'md': return base + 'columns-3 sm:columns-4 md:columns-5 lg:columns-6 gap-2 space-y-2'
      case 'lg': return base + 'columns-2 sm:columns-3 md:columns-4 lg:columns-5 gap-4 space-y-4'
    }
  }
  return ''
}

const currentGridClass = computed(() => getGridClass(viewSize.value, layoutMode.value))

// Actions
const triggerUpload = () => fileInput.value?.click()

const handleUpload = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    isUploading.value = true
    uploadProgress.value = 0
    
    // Simulate upload
    const interval = setInterval(() => {
      uploadProgress.value += 5 + Math.random() * 10
      if (uploadProgress.value >= 100) {
        uploadProgress.value = 100
        clearInterval(interval)
        
        // Process file locally
        const reader = new FileReader()
        reader.onload = (e) => {
          const newImage: AlbumImage = {
            id: Date.now(),
            url: e.target?.result as string,
            thumbnail: e.target?.result as string,
            srcset: '',
            timestamp: Date.now(),
            category: '上传',
            tags: ['新照片', '本地上传'],
            city: '本地',
            location: '本地上传'
          }
          
          // Add to store only (not a custom album)
          store.addPhoto(newImage)
          
          setTimeout(() => {
            isUploading.value = false
            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' })
          }, 500)
        }
        reader.readAsDataURL(file)
      }
    }, 200)
  }
}

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
    activeDate.value = date
  }
}

const openLightbox = (img: AlbumImage) => {
  lightboxImage.value = img
  document.body.style.overflow = 'hidden'
}

const closeLightbox = () => {
  lightboxImage.value = null
  document.body.style.overflow = ''
}

const formatTime = (ts: number) => format(new Date(ts), 'yyyy-MM-dd HH:mm')

// Intersection Observer for Timeline
let observer: IntersectionObserver | null = null

onMounted(() => {
  // Start FPS Monitor
  updateFps()

  // Setup Image Observer
  imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const id = Number(entry.target.getAttribute('data-id'))
      if (!id) return

      if (entry.isIntersecting) {
        visibleImageIds.add(id)
        loadImage(id)
      } else {
        visibleImageIds.delete(id)
      }
    })
  }, {
    rootMargin: '50% 0px 50% 0px',
    threshold: 0
  })

  // Process pending images
  if (pendingImages.size > 0) {
    pendingImages.forEach(el => imageObserver!.observe(el))
    pendingImages.clear()
  }

  // Setup Group Observer
  const options = {
    root: null,
    rootMargin: '-20% 0px -70% 0px',
    threshold: 0
  }
  
  observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id
        if (id) {
          activeDate.value = id.replace('group-', '')
        }
      }
    })
  }, options)

  nextTick(() => {
    observeGroups()
  })
})

watch(groupedImages, () => {
  nextTick(() => {
    observeGroups()
  })
})

const observeGroups = () => {
  if (!observer) return
  observer.disconnect()
  const groups = document.querySelectorAll('.group-container')
  groups.forEach(group => observer?.observe(group))
  
  // Set initial active date
  if (!activeDate.value && Object.keys(groupedImages.value).length > 0) {
    activeDate.value = Object.keys(groupedImages.value)[0]
  }
}

onUnmounted(() => {
  if (observer) observer.disconnect()
  if (imageObserver) imageObserver.disconnect()
  if (rafId) cancelAnimationFrame(rafId)
})

</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(20px); opacity: 0; }

/* Hide Scrollbar */
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>