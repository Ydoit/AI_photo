<template>
  <div class="unified-photo-page mx-auto px-4 py-1 pb-24 min-h-screen">
    <!-- Toolbar & Header -->
    <div class="sticky top-[60px] z-30 pointer-events-none">
      <div class="flex md:flex-row items-center justify-between gap-4 max-w-7xl mx-auto px-4 py-3 pointer-events-auto">
        
        <!-- Back & Title -->
        <div class="flex items-center gap-3 w-full max-w-full md:w-auto bg-white/80 dark:bg-gray-900/80 backdrop-blur-md px-3 py-1.5 rounded-full shadow-sm border border-gray-200/50 dark:border-gray-700/50">
          <button @click="$emit('back')" class="p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors bg-white dark:bg-gray-900">
            <ArrowLeft class="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
          <div class="pr-2 min-w-0" v-if="!loadingTitle">
            <h1 class="max-w-[140px] md:max-w-[300px] text-sm md:text-lg font-bold text-gray-900 dark:text-white leading-tight flex items-center gap-2 truncate">
              <span class="truncate">{{ title }}</span>
              <slot name="title-extra"></slot>
            </h1>
            <p class="text-xs text-gray-500 truncate">{{ subtitle }}</p>
          </div>
          <div v-else class="pr-2 animate-pulse">
            <div class="h-6 w-32 bg-gray-200 dark:bg-gray-800 rounded"></div>
          </div>
        </div>

        <!-- Controls -->
        <div class="flex items-center gap-2 ml-auto animate-in fade-in slide-in-from-right-4 duration-300">
          
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

          <!-- Batch Select -->
          <button 
            @click="enterBatchMode"
            class="p-2 text-gray-700 dark:text-gray-200 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md hover:bg-white dark:hover:bg-gray-900 rounded-full shadow-sm border border-gray-200/50 dark:border-gray-700/50 transition-all"
            title="批量选择"
          >
            <CheckSquare class="w-5 h-5" />
          </button>

          <!-- Header Actions Slot -->
          <slot name="header-actions"></slot>

          <!-- Upload Button -->
          <template v-if="allowUpload">
            <button 
              @click="$emit('upload')"
              class="bg-primary-500 hover:bg-primary-600 text-white p-2 sm:px-4 sm:py-2 rounded-full shadow-lg shadow-primary-500/30 flex items-center gap-2 text-sm font-medium transition-all active:scale-95"
            >
              <UploadCloud class="w-5 h-5" />
              <span class="hidden sm:inline">上传</span>
            </button>
          </template>

        </div>
      </div>
    </div>

    <!-- Timeline Navigation Sidebar (Right Sticky) -->
    <AlbumTimeline
      :items="timelineItems"
      :active-date="activeDate"
      @select="scrollToDate"
    />

    <!-- Main Content Area -->
    <div class="mt-6 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <slot name="intro"></slot>
      <PhotoGallery
        ref="galleryRef"
        :store="props.store"
        :photos="photos"
        :timeline-stats="timelineStats"
        :loading="loading"
        :has-more="hasMore"
        :error="error"
        :layout-mode="layoutMode"
        :view-size="viewSize"
        :group-by-date="true"
        :delete-label="deleteLabel"
        :pending-remove-ids="pendingRemoveIds"
        v-model:active-date="activeDate"
        @click-photo="openLightbox"
        @load-more="$emit('load-more')"
        @load-range="(offset) => $emit('load-range', offset)"
        @batch-delete="handleBatchDelete"
        @remove-from-album="handleBatchRemoveFromAlbum"
        @add-to-album="handleBatchAddToAlbum"
        @set-album-cover="(ids) => $emit('set-cover', ids)"
        @retry="$emit('retry')"
      >
        <template #batch-actions="{ selectedIds, clearSelection }">
            <slot name="batch-actions" :selected-ids="selectedIds" :clear-selection="clearSelection"></slot>
        </template>
        
        <template #overlay-actions="{ photo }">
            <slot name="overlay-actions" :photo="photo"></slot>
        </template>
      </PhotoGallery>
    </div>

    <!-- Lightbox -->
    <PhotoLightbox
      :visible="!!lightboxImage"
      :image="lightboxImage"
      :has-prev="hasPrev"
      :has-next="hasNext"
      :delete-title="deleteLabel"
      @close="closeLightbox"
      @delete="handlePhotoDelete"
      @update="(e) => $emit('photo-update', e)"
      @prev="handlePrev"
      @next="handleNext"
      @add-to-album="handleAddToAlbumFromLightbox"
    />

    <!-- Delete Confirmation -->
    <ConfirmDialog
      v-model:visible="showDeleteConfirm"
      title="确认操作"
      :message="confirmMessage"
      confirm-text="确定"
      cancel-text="取消"
      type="danger"
      @confirm="confirmDelete"
    />

    <!-- Particle Effect -->
    <ParticleExplosion
      v-if="showParticle"
      :active="showParticle"
      @complete="showParticle = false"
    />
    <!-- Album Select Modal -->
    <div v-if="showAlbumSelectModal" class="z-[1000] fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="closeAlbumSelectModal">
      <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div class="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white">选择相册</h3>
          <button @click="closeAlbumSelectModal" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors bg-transparent">
            <X class="w-5 h-5 text-gray-500" />
          </button>
        </div>
        <div class="p-4 max-h-[60vh] overflow-y-auto">
          <div v-if="albums.length === 0" class="text-center py-8 text-gray-500">
            暂无相册
          </div>
          <div v-else class="space-y-2">
            <button
              v-for="album in albums.filter(a => a.type === 'user')"
              :key="album.id"
              @click="confirmAddToAlbum(album.id)"
              class="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-900/80 backdrop-blur-md rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors text-left group relative overflow-hidden"
              :class="{ 'shake-animation border border-red-500': errorAlbumId === album.id }"
            >
              <div class="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-500 group-hover:scale-110 transition-transform">
                <Loader2 v-if="loadingAlbumId === album.id" class="w-5 h-5 animate-spin" />
                <Check v-else-if="successAlbumId === album.id" class="w-5 h-5 animate-in zoom-in duration-300" />
                <Folder v-else class="w-5 h-5" />
              </div>
              <div>
                <h4 class="font-medium text-gray-900 dark:text-white">{{ album.title }}</h4>
                <p class="text-xs text-gray-500">{{ album.count }} 张照片</p>
              </div>
              <!-- Success Fade Overlay -->
              <div v-if="successAlbumId === album.id" class="absolute inset-0 bg-green-500/10 animate-in fade-in duration-300 pointer-events-none"></div>
            </button>
          </div>
        </div>
      </div>
    </div>
    <!-- Extra Modals Slot -->
    <slot name="extra-modals"></slot>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onClickOutside } from '@vueuse/core'
import {
  ArrowLeft, Grid3x3, Grid2x2, Maximize, LayoutDashboard, LayoutGrid,
  UploadCloud, CheckSquare, Settings2
} from 'lucide-vue-next'
import { ElMessage } from 'element-plus'

import PhotoGallery from '@/components/PhotoGallery.vue'
import AlbumTimeline from '@/components/AlbumTimeline.vue'
import PhotoLightbox from '@/components/PhotoLightbox.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import ParticleExplosion from '@/components/ParticleExplosion.vue'
import type { AlbumImage } from '@/types/album'

import { useAlbumStore } from '@/stores/albumStore'
import { usePhotoStore } from '@/stores/photoStore'

const props = withDefaults(defineProps<{
  title?: string
  subtitle?: string
  loading?: boolean
  loadingTitle?: boolean
  error?: string | null
  photos?: AlbumImage[]
  timelineItems?: any[]
  allowUpload?: boolean
  deleteLabel?: string
  hasMore?: boolean
  timelineStats?: any
  confirmRemove?: boolean
  pendingRemoveIds?: Set<string>
  store?: any
}>(), {
  title: '',
  subtitle: '',
  loading: false,
  loadingTitle: false,
  error: null,
  photos: () => [],
  timelineItems: () => [],
  allowUpload: false,
  deleteLabel: '删除',
  hasMore: false,
  timelineStats: null,
  confirmRemove: false,
  pendingRemoveIds: () => new Set()
})

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'upload'): void
  (e: 'delete', ids: string[]): void // General delete/remove event
  (e: 'load-more'): void
  (e: 'load-range', offset: number): void
  (e: 'retry'): void
  (e: 'set-cover', ids: string[]): void
  (e: 'add-to-album', id: string): void
  (e: 'photo-update', event: any): void
  (e: 'remove-from-album', ids: string[]): void // General delete/remove event
  (e: 'confirm-delete', ids: string[], callback: (success: boolean) => void): void
}>()

// UI State
const viewSize = ref<'sm' | 'md' | 'lg'>('md')
const layoutMode = ref<'masonry' | 'grid' | 'list' | 'waterfall'>('grid')
const activeDate = ref('')
const lightboxImage = ref<AlbumImage | null>(null)
const showViewOptions = ref(false)
const viewOptionsRef = ref<HTMLElement | null>(null)
const galleryRef = ref<InstanceType<typeof PhotoGallery> | null>(null)
const isMobile = ref(window.innerWidth < 768)

// Add a resize listener to update isMobile
window.addEventListener('resize', () => {
  isMobile.value = window.innerWidth < 768
})

const albumStore = useAlbumStore()
const photoStore = usePhotoStore()
const store = computed(() => props.store || photoStore)
const albums = computed(() => albumStore.allAlbums)

// Delete/Remove State
const showDeleteConfirm = ref(false)
const showAlbumSelectModal = ref(false)
const idsToDelete = ref<string[]>([])
const showParticle = ref(false)
const pendingRemoveIds = ref(new Set<string>())
// UI State
const showUploadModal = ref(false)
const tempSelectedIds = ref<string[]>([])

// Album Add Animation
const loadingAlbumId = ref<string | null>(null)
const successAlbumId = ref<string | null>(null)
const errorAlbumId = ref<string | null>(null)

onClickOutside(viewOptionsRef, () => {
  showViewOptions.value = false
})

const scrollToDate = (date: string) => {
  galleryRef.value?.scrollToDate(date)
  activeDate.value = date
}

const enterBatchMode = () => {
  galleryRef.value?.enterSelectionMode()
}

// Lightbox
const lightboxIndex = computed(() => {
  if (!lightboxImage.value) return -1
  return props.photos.findIndex(img => img.id === lightboxImage.value?.id)
})

const hasPrev = computed(() => lightboxIndex.value > 0)
const hasNext = computed(() => lightboxIndex.value < props.photos.length - 1 && lightboxIndex.value !== -1)

const openLightbox = (img: AlbumImage) => {
  lightboxImage.value = img
  document.body.style.overflow = 'hidden'
}

const closeLightbox = () => {
  lightboxImage.value = null
  document.body.style.overflow = ''
}

const handlePrev = () => {
  if (hasPrev.value) {
    lightboxImage.value = props.photos[lightboxIndex.value - 1]
  }
}

const handleNext = () => {
  if (hasNext.value) {
    lightboxImage.value = props.photos[lightboxIndex.value + 1]
  }
}

// Delete Logic
const handleBatchDelete = (ids: string[]) => {
  if (ids.length === 0) return
  idsToDelete.value = ids
  showDeleteConfirm.value = true
}

// Reuse for remove-from-album which is essentially a delete from this view
const handleBatchRemoveFromAlbum = (ids: string[]) => {
    if (props.confirmRemove) {
        handleBatchDelete(ids)
    } else {
        emit('remove-from-album', ids)
    }
}

const handlePhotoDelete = (id: string) => {
    handleBatchDelete([id])
    closeLightbox()
}

const confirmMessage = computed(() => {
    return `确定要${props.deleteLabel}选中的 ${idsToDelete.value.length} 张照片吗？`
})

const confirmDelete = () => {
    emit('confirm-delete', idsToDelete.value, (success: boolean) => {
        if (success) {
            // Show particle if needed (usually for permanent delete)
            if (props.deleteLabel === '删除') {
                showParticle.value = true
            }
            galleryRef.value?.exitSelectionMode()
        }
    })
}

const closeAlbumSelectModal = () => {
  showAlbumSelectModal.value = false
  tempSelectedIds.value = []
}

const handleAddToAlbumFromLightbox = (img: AlbumImage) => {
    tempSelectedIds.value = [img.id]
    showAlbumSelectModal.value = true
}

const handleBatchAddToAlbum = (ids: string[]) => {
  if (ids.length === 0) return
  tempSelectedIds.value = ids
  showAlbumSelectModal.value = true
  console.log('handleBatchAddToAlbum', ids)
}

const confirmAddToAlbum = async (targetAlbumId: string) => {
  if (loadingAlbumId.value) return

  loadingAlbumId.value = targetAlbumId
  errorAlbumId.value = null
  console.log('confirmAddToAlbum', tempSelectedIds.value, targetAlbumId)
  try {
    await albumStore.addPhotosToAlbum(tempSelectedIds.value, 'add_to_album', targetAlbumId)

    loadingAlbumId.value = null
    successAlbumId.value = targetAlbumId

    // Play success animation (300ms)
    setTimeout(() => {
        closeAlbumSelectModal()
        ElMessage.success(`成功添加到相册`)
        successAlbumId.value = null
    }, 300)
  } catch (error) {
    console.error('Batch add failed:', error)
    loadingAlbumId.value = null
    errorAlbumId.value = targetAlbumId
    
    // Reset error state after shake animation
    setTimeout(() => {
        errorAlbumId.value = null
    }, 500)
  }
}

// Expose pendingRemoveIds to parent if needed, or methods to manipulate it
defineExpose({
    galleryRef,
    pendingRemoveIds
})
</script>

<style scoped>
/* Scoped styles if necessary */
</style>
