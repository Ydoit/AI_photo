<template>
  <div class="container mx-auto px-4 py-1 pb-24 min-h-screen">
    <!-- Toolbar & Tabs Area -->
    <div class="sticky top-[60px] z-30 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md py-3 -mx-4 px-4 border-b border-gray-100 dark:border-gray-800 shadow-sm transition-all duration-300">
      <div class="flex flex-col md:flex-row items-center justify-between gap-4 max-w-7xl mx-auto">
        
        <!-- Mode Tabs -->
        <div class="bg-gray-100 dark:bg-gray-800 p-1 rounded-lg flex space-x-1">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="currentTab = tab.id"
            :class="[
              'px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-200 flex items-center gap-2',
              currentTab === tab.id
                ? 'bg-white dark:bg-gray-700 text-primary-500 shadow-sm'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            ]"
          >
            <component :is="tab.icon" class="w-4 h-4" />
            {{ tab.name }}
          </button>
        </div>

        <!-- Controls (Only visible in Timeline mode) -->
        <div v-if="currentTab === 'timeline'" class="flex items-center gap-4 animate-in fade-in slide-in-from-right-4 duration-300">
          
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
      v-if="currentTab === 'timeline'"
      :dates="Object.keys(groupedImages)"
      :active-date="activeDate"
      @select="scrollToDate"
    />

    <!-- Main Content Area -->
    <div class="mt-6 relative min-h-[500px]">
      
      <!-- Timeline View -->
      <div v-if="currentTab === 'timeline'" class="space-y-8">
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
              'transition-all duration-500 ease-in-out',
              layoutMode === 'grid' ? 'grid' : 'block',
              currentGridClass
            ]"
          >
            <div
              v-for="img in group"
              :key="img.id"
              class="group relative cursor-zoom-in overflow-hidden rounded-xl bg-gray-100 dark:bg-gray-800 shadow-sm hover:shadow-md transition-all duration-300 mb-4 break-inside-avoid"
              :class="{ 'aspect-square': layoutMode === 'grid' }"
              @click="openLightbox(img)"
            >
              <img
                :src="img.thumbnail"
                :alt="img.tags.join(', ')"
                loading="lazy"
                class="w-full h-full object-cover transform transition-transform duration-700 group-hover:scale-110"
              />
              <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300"></div>
              
              <!-- Smart Tags Overlay -->
              <div class="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/70 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 translate-y-2 group-hover:translate-y-0">
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="tag in img.tags.slice(0, 2)" :key="tag" class="text-[10px] font-medium text-white bg-white/20 px-2 py-0.5 rounded-full backdrop-blur-md border border-white/10">
                    {{ tag }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Category View -->
      <div v-else class="space-y-10 animate-in slide-in-from-bottom-4 duration-500">
        <div v-for="(group, category) in categoryImages" :key="category">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-bold text-gray-800 dark:text-gray-200 flex items-center">
              <span class="w-1.5 h-6 bg-primary-500 rounded-full mr-3"></span>
              {{ category }}
              <span class="ml-2 text-sm font-normal text-gray-400">({{ group.length }})</span>
            </h3>
            <button class="text-sm text-primary-500 hover:text-primary-600 font-medium flex items-center gap-1">
              查看全部 <ChevronRight class="w-4 h-4" />
            </button>
          </div>
          
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            <div
              v-for="img in group"
              :key="img.id"
              class="aspect-square relative cursor-zoom-in overflow-hidden rounded-xl group bg-gray-100 dark:bg-gray-800 shadow-sm hover:shadow-md transition-all"
               @click="openLightbox(img)"
            >
               <img
                :src="img.thumbnail"
                loading="lazy"
                class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
              />
              <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors"></div>
              <div class="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                 <div class="bg-black/50 backdrop-blur-sm p-1.5 rounded-full text-white">
                   <Maximize2 class="w-4 h-4" />
                 </div>
              </div>
            </div>
          </div>
        </div>
      </div>
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
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { 
  X, Maximize2, Grid3x3, Grid2x2, Maximize, LayoutDashboard, LayoutGrid, 
  UploadCloud, Loader2, CalendarDays, Clock, Tags, ChevronRight 
} from 'lucide-vue-next'
import AlbumTimeline from '@/components/AlbumTimeline.vue'
import { format } from 'date-fns'

// Types
interface AlbumImage {
  id: number
  url: string
  thumbnail: string
  timestamp: number
  category: string
  tags: string[]
}

// State
const currentTab = ref('timeline')
const viewSize = ref<'sm' | 'md' | 'lg'>('md')
const layoutMode = ref<'masonry' | 'grid'>('masonry')
const isUploading = ref(false)
const uploadProgress = ref(0)
const activeDate = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const tabs = [
  { id: 'timeline', name: '时光轴', icon: Clock },
  { id: 'smart', name: '智能分类', icon: Tags }
]

// Mock Data
const categories = ['人物', '风景', '证件', '美食', '建筑', '宠物']
const tagsPool = ['AI识别', '高清', '夜景', '人像', '自然', '街拍', '旅行', '快乐']

const generateImages = (count: number): AlbumImage[] => {
  return Array.from({ length: count }).map((_, i) => {
    const id = i + 1
    const category = categories[Math.floor(Math.random() * categories.length)]
    const randomTags = [category, tagsPool[Math.floor(Math.random() * tagsPool.length)]]
    return {
      id,
      url: `https://picsum.photos/id/${id + 10}/1200/800`,
      thumbnail: `https://picsum.photos/id/${id + 10}/400/300`,
      timestamp: Date.now() - Math.floor(Math.random() * 100000000000),
      category,
      tags: [...new Set(randomTags)]
    }
  })
}

const images = ref<AlbumImage[]>(generateImages(300))
const lightboxImage = ref<AlbumImage | null>(null)

// Computed Data
const groupedImages = computed(() => {
  const groups: Record<string, AlbumImage[]> = {}
  const sorted = [...images.value].sort((a, b) => b.timestamp - a.timestamp)
  sorted.forEach(img => {
    const date = format(new Date(img.timestamp), 'yyyy年MM月')
    if (!groups[date]) groups[date] = []
    groups[date].push(img)
  })
  return groups
})

const categoryImages = computed(() => {
  const groups: Record<string, AlbumImage[]> = {}
  images.value.forEach(img => {
    if (!groups[img.category]) groups[img.category] = []
    groups[img.category].push(img)
  })
  return groups
})

// Layout Logic
// Dynamic Layout Classes
// We need to inject these into the DOM. Since Tailwind doesn't support dynamic class interpolation like `grid-cols-${cols}`,
// we must return full class names.
const getGridClass = (size: string, mode: string) => {
  if (mode === 'grid') {
    switch (size) {
      case 'sm': return 'grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2'
      case 'md': return 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4'
      case 'lg': return 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6'
    }
  } else {
    // Masonry (Columns)
    switch (size) {
      case 'sm': return 'columns-3 sm:columns-4 md:columns-5 lg:columns-6 gap-2 space-y-2'
      case 'md': return 'columns-2 sm:columns-3 md:columns-4 lg:columns-5 gap-4 space-y-4'
      case 'lg': return 'columns-1 sm:columns-2 md:columns-3 lg:columns-4 gap-6 space-y-6'
    }
  }
  return ''
}

// Update the template to use this function directly or via a computed property per group
// But wait, we are inside a v-for. So we can just bind :class="getGridClass(viewSize, layoutMode)"
// We need to make `getGridClass` available to template or use a computed that returns the current class string.
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
            timestamp: Date.now(),
            category: '上传',
            tags: ['新照片', '本地上传']
          }
          images.value.unshift(newImage)
          
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
    // Offset for sticky headers
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
  // Update `currentGridClass` usage in template:
  // I will replace the `:style` binding in the template with `:class="currentGridClass"`
  
  // Setup Observer
  const options = {
    root: null,
    rootMargin: '-20% 0px -70% 0px', // Focus area
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

watch([groupedImages, currentTab], () => {
  nextTick(() => {
    observeGroups()
  })
})

const observeGroups = () => {
  if (!observer) return
  observer.disconnect()
  const groups = document.querySelectorAll('.group-container')
  groups.forEach(group => observer?.observe(group))
  
  // Set initial active date if not set
  if (!activeDate.value && Object.keys(groupedImages.value).length > 0) {
    activeDate.value = Object.keys(groupedImages.value)[0]
  }
}

onUnmounted(() => {
  if (observer) observer.disconnect()
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