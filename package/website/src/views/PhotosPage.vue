<template>
  <div class="container mx-auto px-4 py-1 pb-24 min-h-screen">
    <!-- Toolbar & Header -->
    <div class="sticky top-[60px] z-30 pointer-events-none">
      <div class="flex md:flex-row items-center justify-between gap-4 max-w-7xl mx-auto px-4 py-3 pointer-events-auto">
        <!-- Controls -->
        <div class="flex items-center gap-2 ml-auto animate-in fade-in slide-in-from-right-4 duration-300">
          <!-- Filter Button -->
          <button 
            ref="filterButtonRef"
            @click="showFilterPanel = !showFilterPanel"
            class="p-2 text-gray-700 dark:text-gray-200 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md hover:bg-white dark:hover:bg-gray-900 rounded-full shadow-sm border border-gray-200/50 dark:border-gray-700/50 transition-all"
            :class="{ 'bg-primary-50 text-primary-500 border-primary-200': showFilterPanel }"
            title="筛选"
          >
            <Filter class="w-5 h-5" />
          </button>

          <!-- View Options Menu -->
          <div class="relative">
            <button 
              @click="showViewOptions = !showViewOptions"
              class="p-2 text-gray-700 dark:text-gray-200 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md hover:bg-white dark:hover:bg-gray-900 rounded-full shadow-sm border border-gray-200/50 dark:border-gray-700/50 transition-all"
              title="视图设置"
            >
              <Settings2 class="w-5 h-5" />
            </button>

            <!-- Secondary Menu Dropdown -->
            <Transition
              enter-active-class="transition duration-200 ease-out"
              enter-from-class="transform scale-95 opacity-0"
              enter-to-class="transform scale-100 opacity-100"
              leave-active-class="transition duration-75 ease-in"
              leave-from-class="transform scale-100 opacity-100"
              leave-to-class="transform scale-95 opacity-0"
            >
              <div v-if="showViewOptions" 
                   ref="viewOptionsRef"
                   class="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-100 dark:border-gray-800 p-2 z-50 origin-top-right"
              >
                <div class="space-y-3 p-1">
                  <!-- View Size -->
                  <div class="space-y-2">
                    <p class="text-xs font-medium text-gray-500 px-1">图片大小</p>
                    <div class="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                      <button v-for="size in ['sm', 'md', 'lg']" :key="size"
                        @click="viewSize = size as any"
                        class="flex-1 p-1.5 rounded text-center transition-colors dark:bg-gray-800"
                        :class="{ 'bg-white dark:bg-gray-700 shadow-sm text-primary-500': viewSize === size, 'text-gray-700 dark:text-gray-300': viewSize !== size }"
                      >
                        <Grid3x3 v-if="size === 'sm'" class="w-4 h-4 mx-auto" />
                        <Grid2x2 v-if="size === 'md'" class="w-4 h-4 mx-auto" />
                        <Maximize v-if="size === 'lg'" class="w-4 h-4 mx-auto" />
                      </button>
                    </div>
                  </div>

                  <!-- Layout Mode -->
                  <div class="space-y-2">
                    <p class="text-xs font-medium text-gray-500 px-1">布局模式</p>
                    <div class="grid grid-cols-1 gap-1">
                       <button
                        @click="layoutMode = 'waterfall'"
                        class="flex items-center gap-2 px-2 py-1.5 rounded-lg transition-colors text-sm dark:bg-gray-800"
                        :class="{ 'bg-primary-50 dark:bg-primary-900/20 text-primary-600': layoutMode === 'waterfall', 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300': layoutMode !== 'waterfall' }"
                      >
                        <LayoutDashboard class="w-4 h-4" />
                        <span>瀑布流</span>
                      </button>
                      <button
                        @click="layoutMode = 'grid'"
                        class="flex items-center gap-2 px-2 py-1.5 rounded-lg transition-colors text-sm dark:bg-gray-800"
                        :class="{ 'bg-primary-50 dark:bg-primary-900/20 text-primary-600': layoutMode === 'grid', 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300': layoutMode !== 'grid' }"
                      >
                        <LayoutGrid class="w-4 h-4" />
                        <span>正方形</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <!-- Actions -->
          <button 
            @click="enterBatchMode"
            class="p-2 text-gray-700 dark:text-gray-200 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md hover:bg-white dark:hover:bg-gray-900 rounded-full shadow-sm border border-gray-200/50 dark:border-gray-700/50 transition-all"
            title="批量管理"
          >
            <CheckSquare class="w-5 h-5" />
          </button>
          
          <button
            @click="triggerUpload"
            class="bg-primary-500 hover:bg-primary-600 text-white p-2 sm:px-4 sm:py-2 rounded-full shadow-lg shadow-primary-500/30 flex items-center gap-2 text-sm font-medium transition-all active:scale-95"
          >
            <UploadCloud class="w-5 h-5" />
            <span class="hidden sm:inline">上传</span>
          </button>

        </div>
      </div>

      <!-- Filter Panel (Absolute Overlay) -->
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="transform -translate-y-2 opacity-0"
        enter-to-class="transform translate-y-0 opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="transform translate-y-0 opacity-100"
        leave-to-class="transform -translate-y-2 opacity-0"
      >
          <div v-if="showFilterPanel" class="absolute left-0 right-0 top-full mt-2 pointer-events-none px-4">
            <div class="max-w-7xl mx-auto flex justify-end">
              <div ref="filterPanelRef" class="bg-white/95 dark:bg-gray-900/95 backdrop-blur-md rounded-2xl shadow-xl border border-gray-100 dark:border-gray-800 overflow-hidden w-full max-w-md pointer-events-auto">
                 <FilterPanel />
              </div>
            </div>
          </div>
      </Transition>
    </div>

    <!-- Timeline Navigation Sidebar (Right Sticky) -->
    <AlbumTimeline
      :items="photoStore.timelineStats?.timeline || []"
      :active-date="activeDate"
      @select="scrollToDate"
    />

    <!-- Main Content Area -->
    <div class="mt-6 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <PhotoGallery
        ref="galleryRef"
        :photos="images"
        :timeline-stats="photoStore.timelineStats"
        :loading="photoStore.loading"
        :has-more="photoStore.hasMore"
        :error="photoStore.error"
        :layout-mode="layoutMode"
        :view-size="viewSize"
        v-model:active-date="activeDate"
        @load-more="photoStore.loadPhotos"
        @click-photo="openLightbox"
        @batch-delete="handleBatchDelete"
        @add-to-album="handleBatchAddToAlbum"
        @retry="photoStore.loadPhotos(true)"
      />
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
      :has-prev="hasPrev"
      :has-next="hasNext"
      @close="closeLightbox"
      @delete="handlePhotoDelete"
      @update="handlePhotoUpdate"
      @prev="handlePrev"
      @next="handleNext"
      @add-to-album="handleAddToAlbumFromLightbox"
    />

    <!-- Album Select Modal -->
    <AlbumSelector
      v-model:visible="showAlbumSelectModal"
      :photo-ids="tempSelectedIds"
      @success="closeAlbumSelectModal"
    />

    <ConfirmDialog
      v-model:visible="showDeleteConfirm"
      title="确认删除"
      message="确定要删除选中的照片吗？此操作无法撤销。"
      @confirm="confirmDelete"
    />
    <ParticleExplosion :active="showParticle" @complete="showParticle = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAlbumStore } from '@/stores/albumStore'
import { usePhotoStore } from '@/stores/photoStore'
import type { AlbumImage } from '@/types/album'
import {
  X, Maximize, Grid3x3, Grid2x2, LayoutDashboard, LayoutGrid, LayoutList,
  UploadCloud, CheckSquare, FolderInput, Folder, Settings2, Loader2, Check, Filter
} from 'lucide-vue-next'
import { onClickOutside } from '@vueuse/core'
import AlbumTimeline from '@/components/AlbumTimeline.vue'
import PhotoLightbox from '@/components/PhotoLightbox.vue'
import MultiFileUpload from '@/components/MultiFileUpload.vue'
import PhotoGallery from '@/components/PhotoGallery.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import ParticleExplosion from '@/components/ParticleExplosion.vue'
import FilterPanel from '@/components/FilterPanel.vue'
import AlbumSelector from '@/components/AlbumSelector.vue'
import { format } from 'date-fns'
import { ElMessage } from 'element-plus'
import { watch } from 'fs'

const store = useAlbumStore()
const photoStore = usePhotoStore()

// State
const images = computed(() => photoStore.images)
const viewSize = ref<'sm' | 'md' | 'lg'>('md')
const layoutMode = ref<'masonry' | 'grid' | 'list' | 'waterfall'>('grid')
const activeDate = ref('')
const showUploadModal = ref(false)
const lightboxImage = ref<AlbumImage | null>(null)
const showViewOptions = ref(false)
const showFilterPanel = ref(false)
const viewOptionsRef = ref<HTMLElement | null>(null)
const filterButtonRef = ref<HTMLElement | null>(null)
const filterPanelRef = ref<HTMLElement | null>(null)

onClickOutside(viewOptionsRef, () => {
  showViewOptions.value = false
})

onClickOutside(filterPanelRef, () => {
  showFilterPanel.value = false
}, {
  ignore: [filterButtonRef]
})

// Batch Actions State
const showAlbumSelectModal = ref(false)
const tempSelectedIds = ref<string[]>([])

// Delete Confirmation & Animation
const showDeleteConfirm = ref(false)
const showParticle = ref(false)
const idsToDelete = ref<string[]>([])

// Gallery Ref
const galleryRef = ref<InstanceType<typeof PhotoGallery> | null>(null)


// Methods
const handleUploadComplete = () => {
  showUploadModal.value = false
  photoStore.loadPhotos(true)
  photoStore.fetchTimelineStats()
}

const triggerUpload = () => {
  showUploadModal.value = true
}

const enterBatchMode = () => {
galleryRef.value?.enterSelectionMode()
}

const handleBatchDelete = async (ids: string[]) => {
  if (ids.length === 0) return
  idsToDelete.value = ids
  showDeleteConfirm.value = true
}

const confirmDelete = async () => {
  try {
    await photoStore.deletePhotos(idsToDelete.value)
    galleryRef.value?.exitSelectionMode()
    photoStore.loadPhotos(true)
    
    // Play particle animation
    showParticle.value = true
  } catch (e) {
    console.error(e)
    ElMessage.error('删除失败')
  }
}

const handleBatchAddToAlbum = (ids: string[]) => {
  if (ids.length === 0) return
  tempSelectedIds.value = ids
  showAlbumSelectModal.value = true
}

const closeAlbumSelectModal = () => {
  showAlbumSelectModal.value = false
  tempSelectedIds.value = []
  galleryRef.value?.exitSelectionMode()
}

const scrollToDate = (date: string) => {
  console.log('Scroll to date:', date)
  galleryRef.value?.scrollToDate(date)
  activeDate.value = date
}

// Lightbox Navigation
const lightboxIndex = computed(() => {
  if (!lightboxImage.value) return -1
  return images.value.findIndex(img => img.id === lightboxImage.value?.id)
})

const hasPrev = computed(() => lightboxIndex.value > 0)
const hasNext = computed(() => lightboxIndex.value < images.value.length - 1 && lightboxIndex.value !== -1)

const handlePrev = () => {
  if (hasPrev.value) {
    lightboxImage.value = images.value[lightboxIndex.value - 1]
  }
}

const handleNext = () => {
  if (hasNext.value) {
    lightboxImage.value = images.value[lightboxIndex.value + 1]
  }
}

const handleAddToAlbumFromLightbox = (img: AlbumImage) => {
    tempSelectedIds.value = [img.id]
    showAlbumSelectModal.value = true
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
  await photoStore.deletePhoto(id)
  closeLightbox()
}

const handlePhotoUpdate = (event: { id: string, location?: string, tags?: string[] }) => {
  console.log('Update photo:', event)
}

onMounted(() => {
  photoStore.resetAll()
  // Initial Load
  photoStore.fetchAvailableFilters()
  store.fetchAlbums()
  photoStore.fetchTimelineStats()
  photoStore.loadPhotos(true)
})
onUnmounted(() => {
  photoStore.resetAll()
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(20px); opacity: 0; }

.shake-animation {
  animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
}

@keyframes shake {
  10%, 90% { transform: translate3d(-1px, 0, 0); }
  20%, 80% { transform: translate3d(2px, 0, 0); }
  30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
  40%, 60% { transform: translate3d(4px, 0, 0); }
}

@media (prefers-reduced-motion: reduce) {
  .shake-animation {
    animation: none;
    border: 2px solid red; /* Visual cue instead of motion */
  }
}
</style>
