<template>
  <div class="container mx-auto px-4 py-1 pb-24 min-h-screen">
    <!-- Toolbar & Header -->
    <div class="sticky top-[60px] z-30 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md py-3 -mx-4 px-4 border-b border-gray-100 dark:border-gray-800 shadow-sm transition-all duration-300">
      <div class="flex flex-col md:flex-row items-center justify-between gap-4 max-w-7xl mx-auto">
        <!-- Default Title -->
        <div class="flex items-center gap-2 w-full md:w-auto">
          <h1 class="text-lg font-bold text-gray-900 dark:text-white leading-tight">全部照片</h1>
          <span class="text-xs text-gray-500 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">{{ images.length }}</span>
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

          <div class="w-px h-6 bg-gray-200 dark:bg-gray-700"></div>

          <!-- Actions -->
          <button 
            @click="enterBatchMode"
            class="p-2 text-gray-500 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
            title="批量管理"
          >
            <CheckSquare class="w-5 h-5" />
          </button>
          
          <button 
            @click="triggerUpload"
            class="bg-primary-500 hover:bg-primary-600 text-white px-4 py-1.5 rounded-lg flex items-center gap-2 text-sm font-medium transition-all active:scale-95 shadow-md shadow-primary-500/20"
          >
            <UploadCloud class="w-4 h-4" />
            <span class="hidden sm:inline">上传</span>
          </button>

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
        delete-label="删除"
        @click-photo="openLightbox"
        @load-more="store.loadPhotos"
        @update:active-date="activeDate = $event"
        @batch-delete="handleBatchDelete"
      >
        <template #batch-actions="{ selectedIds, clearSelection }">
          <button 
            @click="prepareAddToAlbum(selectedIds, clearSelection)"
            class="p-2 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors flex items-center gap-2"
            title="添加到相册"
          >
            <FolderInput class="w-5 h-5" />
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
            <MultiFileUpload :albumId="undefined" @upload-complete="handleUploadComplete" />
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

    <!-- Album Select Modal -->
    <div v-if="showAlbumSelectModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="closeAlbumSelectModal">
      <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div class="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white">选择相册</h3>
          <button @click="closeAlbumSelectModal" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors">
            <X class="w-5 h-5 text-gray-500" />
          </button>
        </div>
        <div class="p-4 max-h-[60vh] overflow-y-auto">
          <div v-if="albums.length === 0" class="text-center py-8 text-gray-500">
            暂无相册
          </div>
          <div v-else class="space-y-2">
            <button 
              v-for="album in albums" 
              :key="album.id"
              @click="confirmAddToAlbum(album.id)"
              class="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors text-left group"
            >
              <div class="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-500 group-hover:scale-110 transition-transform">
                <Folder class="w-5 h-5" />
              </div>
              <div>
                <h4 class="font-medium text-gray-900 dark:text-white">{{ album.title }}</h4>
                <p class="text-xs text-gray-500">{{ album.count }} 张照片</p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAlbumStore, type AlbumImage } from '@/stores/albumStore'
import { 
  X, Maximize, Grid3x3, Grid2x2, LayoutDashboard, LayoutGrid, LayoutList,
  UploadCloud, CheckSquare, FolderInput, Folder
} from 'lucide-vue-next'
import AlbumTimeline from '@/components/AlbumTimeline.vue'
import PhotoLightbox from '@/components/PhotoLightbox.vue'
import MultiFileUpload from '@/components/MultiFileUpload.vue'
import PhotoGallery from '@/components/PhotoGallery.vue'
import { format } from 'date-fns'
import { ElMessage } from 'element-plus'

const store = useAlbumStore()

// State
const images = computed(() => store.images)
const albums = computed(() => store.allAlbums)
const viewSize = ref<'sm' | 'md' | 'lg'>('md')
const layoutMode = ref<'masonry' | 'grid' | 'list'>('masonry')
const activeDate = ref('')
const showUploadModal = ref(false)
const lightboxImage = ref<AlbumImage | null>(null)

// Batch Actions State
const showAlbumSelectModal = ref(false)
const tempSelectedIds = ref<string[]>([])
let clearSelectionCallback: (() => void) | null = null

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

// Methods
const handleUploadComplete = () => {
  showUploadModal.value = false
  store.loadPhotos(true)
}

const triggerUpload = () => {
  showUploadModal.value = true
}

const enterBatchMode = () => {
  galleryRef.value?.enterSelectionMode()
}

const handleBatchDelete = async (ids: string[]) => {
  if (ids.length === 0) return
  if (confirm(`确定要删除选中的 ${ids.length} 张照片吗？`)) {
    for (const id of ids) {
      await store.deletePhoto(id)
    }
    ElMessage.success('删除成功')
  }
}

const prepareAddToAlbum = (selectedIds: Set<string>, clearCallback: () => void) => {
  if (selectedIds.size === 0) return
  tempSelectedIds.value = Array.from(selectedIds)
  clearSelectionCallback = clearCallback
  showAlbumSelectModal.value = true
}

const closeAlbumSelectModal = () => {
  showAlbumSelectModal.value = false
  tempSelectedIds.value = []
  clearSelectionCallback = null
}

const confirmAddToAlbum = async (targetAlbumId: string) => {
  try {
    await store.addPhotosToAlbum(tempSelectedIds.value, 'add_to_album', targetAlbumId)
    closeAlbumSelectModal()
    if (clearSelectionCallback) clearSelectionCallback()
    store.loadPhotos(true) // Reload
    ElMessage.success(`成功添加 ${tempSelectedIds.value.length} 张照片到相册`)
  } catch (error) {
    console.error('Batch add failed:', error)
    ElMessage.error('添加失败')
  }
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

onMounted(() => {
  store.fetchAlbums()
  store.loadPhotos(true)
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(20px); opacity: 0; }
</style>