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
            <h1 class="text-lg font-bold text-gray-900 dark:text-white leading-tight">{{ album?.title || '相册详情' }}</h1>
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

          <!-- Batch Select -->
          <button 
            @click="enterBatchMode"
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-600 dark:text-gray-300"
            title="批量选择"
          >
            <CheckSquare class="w-5 h-5" />
          </button>

          <!-- Upload Button (Only for Custom Albums) -->
          <template v-if="album?.type === 'custom'">
            <button 
              @click="triggerUpload"
              class="bg-primary-500 hover:bg-primary-600 text-white px-4 py-1.5 rounded-lg flex items-center gap-2 text-sm font-medium transition-all active:scale-95 shadow-md shadow-primary-500/20"
            >
              <UploadCloud class="w-4 h-4" />
              <span class="hidden sm:inline">上传</span>
            </button>
          </template>

        </div>
      </div>
    </div>

    <!-- Timeline Navigation Sidebar (Right Sticky) -->
    <AlbumTimeline
      :dates="timelineDates"
      :active-date="activeDate"
      @select="scrollToDate"
    />

    <!-- Main Content Area -->
    <div class="mt-6">
      <PhotoGallery
        ref="galleryRef"
        :photos="images"
        :loading="store.loading"
        :has-more="store.hasMore"
        :layout-mode="layoutMode"
        :view-size="viewSize"
        :group-by-date="true"
        :delete-label="album?.type === 'custom' ? '从相册中移除' : '删除'"
        @click-photo="openLightbox"
        @load-more="loadMorePhotos"
        @update:active-date="activeDate = $event"
        @batch-delete="handleBatchDelete"
      >
        <template #overlay-actions="{ photo }">
           <button 
             v-if="album?.type === 'custom'"
             @click.stop="deletePhotoFromAlbum(photo.id)"
             class="bg-red-500/80 hover:bg-red-600 text-white p-1.5 rounded-full backdrop-blur-md transition-colors"
             title="移出相册"
           >
             <Trash2 class="w-4 h-4" />
           </button>
        </template>
      </PhotoGallery>
    </div>

    <!-- Upload Progress Toast -->
    <Transition name="slide-up">
      <div v-if="showUploadModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
        <div class="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200">
          <div class="p-4 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
            <h3 class="font-bold text-lg text-gray-900 dark:text-white">上传照片</h3>
            <button @click="showUploadModal = false" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"><X class="w-5 h-5" /></button>
          </div>
          <div class="p-6 overflow-y-auto">
            <MultiFileUpload :albumId="albumId" @upload-complete="handleUploadComplete" />
          </div>

         </div>
      </div>
    </Transition>
    
    <!-- Lightbox -->
    <PhotoLightbox
      :visible="!!lightboxImage"
      :image="lightboxImage"
      :album-images="images"
      @close="closeLightbox"
      @delete="handlePhotoDelete"
      @update="handlePhotoUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAlbumStore, type AlbumImage } from '@/stores/albumStore'
import { 
  ArrowLeft, Grid3x3, Grid2x2, Maximize, LayoutDashboard, LayoutGrid, LayoutList,
  UploadCloud, Trash2, X, CheckSquare
} from 'lucide-vue-next'
import AlbumTimeline from '@/components/AlbumTimeline.vue'
import PhotoLightbox from '@/components/PhotoLightbox.vue'
import MultiFileUpload from '@/components/MultiFileUpload.vue'
import PhotoGallery from '@/components/PhotoGallery.vue'
import { format } from 'date-fns'

const route = useRoute()
const router = useRouter()
const store = useAlbumStore()
const albumId = route.params.id as string

// State
const album = computed(() => store.getAlbumDetails(albumId))
const images = computed(() => store.images)

// UI State
const viewSize = ref<'sm' | 'md' | 'lg'>('md')
const layoutMode = ref<'masonry' | 'grid' | 'list'>('masonry')
const activeDate = ref('')
const lightboxImage = ref<AlbumImage | null>(null)
const showUploadModal = ref(false)

// Gallery Ref
const galleryRef = ref<InstanceType<typeof PhotoGallery> | null>(null)

// Timeline Dates
const timelineDates = computed(() => {
  const dates = new Set<string>()
  const sorted = [...images.value].sort((a, b) => b.timestamp - a.timestamp)
  sorted.forEach(img => {
    dates.add(format(new Date(img.timestamp), 'yyyy年MM月'))
  })
  return Array.from(dates)
})

// Actions
const triggerUpload = () => {
    showUploadModal.value = true
}

const handleUploadComplete = () => {
    showUploadModal.value = false
    store.loadAlbumPhotos(albumId, true)
}

const loadMorePhotos = () => {
    store.loadAlbumPhotos(albumId)
}

const scrollToDate = (date: string) => {
  galleryRef.value?.scrollToDate(date)
  activeDate.value = date
}

const openLightbox = (img: AlbumImage) => {
  lightboxImage.value = img
  document.body.style.overflow = 'hidden'
}

const closeLightbox = () => {
  lightboxImage.value = null
  document.body.style.overflow = ''
}

const deletePhotoFromAlbum = async (id: string) => {
    if (confirm('确定要将这张照片移出相册吗？')) {
        await store.removePhotoFromAlbum(albumId, id)
    }
}

const handlePhotoDelete = async (id: string) => {
    await store.deletePhoto(id)
    closeLightbox()
}

const handlePhotoUpdate = (event: { id: string, location?: string, tags?: string[] }) => {
    const img = store.images.find(i => i.id === event.id)
    if (img) {
        if (event.location !== undefined) img.location = event.location
        if (event.tags !== undefined) img.tags = event.tags
    }
}

const enterBatchMode = () => {
  galleryRef.value?.enterSelectionMode()
}

const handleBatchDelete = async (ids: string[]) => {
    if (album.value?.type === 'custom') {
        if (confirm(`确定要将这 ${ids.length} 张照片从相册中移除吗？`)) {
            await store.removePhotosFromAlbum(albumId, ids)
        }
    } else {
        if (confirm(`确定要永久删除这 ${ids.length} 张照片吗？此操作无法撤销。`)) {
            await store.deletePhotos(ids)
        }
    }
}

onMounted(() => {
  store.fetchAlbums()
  store.loadAlbumPhotos(albumId, true)
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(20px); opacity: 0; }
</style>
