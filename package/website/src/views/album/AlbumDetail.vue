<template>
  <UnifiedPhotoPage
    :title="album?.title || '相册详情'"
    :subtitle="`${album?.count || 0} 个项目`"
    :loading="photoStore.loading"
    :photos="images"
    :timeline-stats="photoStore.timelineStats"
    :timeline-items="timelineItems"
    :allow-upload="album?.type === 'custom'"
    :delete-label="album?.type === 'custom' ? '从相册中移除' : '删除'"
    :pending-remove-ids="pendingRemoveIds"
    :has-more="photoStore.hasMore"
    @back="router.back()"
    @upload="triggerUpload"
    @load-more="loadMorePhotos"
    @retry="photoStore.loadAlbumPhotos(albumId, true)"
    @confirm-delete="handleConfirmDelete"
    @remove-from-album="handleBatchRemoveFromAlbum"
    @add-to-album="handleAddToAlbumFromLightbox"
    @photo-update="handlePhotoUpdate"
    @set-cover="setCover"
  >
    <template #extra-modals>
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
                v-for="album in albums"
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
    </template>
  </UnifiedPhotoPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAlbumStore } from '@/stores/albumStore'
import { usePhotoStore } from '@/stores/photoStore'
import { albumService } from '@/api/album'
import { X, Folder, Loader2, Check } from 'lucide-vue-next'
import UnifiedPhotoPage from '@/components/UnifiedPhotoPage.vue'
import MultiFileUpload from '@/components/MultiFileUpload.vue'
import { format } from 'date-fns'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const albumStore = useAlbumStore()
const photoStore = usePhotoStore()
const albumId = route.params.id as string

// State
const album = computed(() => albumStore.getAlbumDetails(albumId))
const images = computed(() => photoStore.images)
const albums = computed(() => albumStore.allAlbums)

// UI State
const showUploadModal = ref(false)
const showAlbumSelectModal = ref(false)
const tempSelectedIds = ref<string[]>([])
const pendingRemoveIds = ref(new Set<string>())

// Album Add Animation
const loadingAlbumId = ref<string | null>(null)
const successAlbumId = ref<string | null>(null)
const errorAlbumId = ref<string | null>(null)

// Used by UnifiedPhotoPage for sidebar
const timelineItems = computed(() => photoStore.timelineStats?.timeline || [])

// Actions
const triggerUpload = () => {
    showUploadModal.value = true
}

const handleUploadComplete = () => {
    showUploadModal.value = false
    photoStore.loadAlbumPhotos(albumId, true)
}

const loadMorePhotos = () => {
    photoStore.loadAlbumPhotos(albumId)
}

const handleAddToAlbumFromLightbox = (id: string) => {
    tempSelectedIds.value = [id]
    showAlbumSelectModal.value = true
}

const handlePhotoUpdate = (event: { id: string, location?: string, tags?: string[] }) => {
    const img = photoStore.images.find(i => i.id === event.id)
}

const setCover = async (ids: string[]) => {
  try {
    await albumService.setAlbumCover(albumId, ids[0])
    ElMessage.success('封面已更新')
  } catch (e) {
    ElMessage.error('封面更新失败')
  }
}

const handleConfirmDelete = async (ids: string[], callback: (success: boolean) => void) => {
    try {
        if (album.value?.type === 'custom') {
             // Should not happen as custom albums use 'remove-from-album' event usually
             // But if it does, we treat it as remove
             await albumStore.removePhotosFromAlbum(albumId, ids)
        } else {
            await photoStore.deletePhotos(ids)
        }
        photoStore.loadAlbumPhotos(albumId, true)
        callback(true)
    } catch (e) {
        console.error(e)
        ElMessage.error('操作失败')
        callback(false)
    }
}

const handleBatchRemoveFromAlbum = async (ids: string[]) => {
    if (ids.length === 0) return
    
    // Optimistic UI: Mark as pending remove (shrink animation)
    ids.forEach(id => pendingRemoveIds.value.add(id))

    // Timeout Promise (3s)
    const timeout = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Timeout')), 3000)
    )

    try {
        await Promise.race([
            albumStore.removePhotosFromAlbum(albumId, ids),
            timeout
        ])
        
        photoStore.loadAlbumPhotos(albumId, true)
        ElMessage.success('已移出相册')
        
        // Clear pending IDs after successful removal and reload
        // We delay slightly to ensure the list update has processed
        setTimeout(() => {
             ids.forEach(id => pendingRemoveIds.value.delete(id))
        }, 500)
    } catch (e: any) {
        if (e.message === 'Timeout') {
            ElMessage.warning('操作超时，标记为待删除')
            // Keep in pendingRemoveIds to maintain visual state
        } else {
            ElMessage.error('移出失败')
            // Revert optimistic update on error
            ids.forEach(id => pendingRemoveIds.value.delete(id))
        }
    }
}

const closeAlbumSelectModal = () => {
  showAlbumSelectModal.value = false
  tempSelectedIds.value = []
}

const confirmAddToAlbum = async (targetAlbumId: string) => {
  if (loadingAlbumId.value) return
  
  loadingAlbumId.value = targetAlbumId
  errorAlbumId.value = null

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

onMounted(() => {
    photoStore.resetAll()
    albumStore.fetchAlbums()
    photoStore.loadAlbumPhotos(albumId, true)
})

onUnmounted(() => {
    photoStore.resetAll()
})

</script>
