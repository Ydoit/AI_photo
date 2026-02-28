<template>
  <div v-if="visible" class="z-[1000] fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="close">
    <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
      <div class="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white">选择相册</h3>
        <button @click="close" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors bg-transparent">
          <X class="w-5 h-5 text-gray-500" />
        </button>
      </div>
      <div class="p-4 max-h-[60vh] overflow-y-auto">
        <div v-if="albums.filter(a => a.type === 'user').length === 0" class="text-center py-8 text-gray-500">
          暂无普通相册
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { X, Loader2, Check, Folder } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import { useAlbumStore } from '@/stores/albumStore'

const props = defineProps<{
  visible: boolean
  photoIds: string[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'success', albumId: string): void
}>()

const albumStore = useAlbumStore()
const albums = computed(() => albumStore.allAlbums)

const loadingAlbumId = ref<string | null>(null)
const successAlbumId = ref<string | null>(null)
const errorAlbumId = ref<string | null>(null)

const close = () => {
  emit('update:visible', false)
}

const confirmAddToAlbum = async (targetAlbumId: string) => {
  if (loadingAlbumId.value) return

  loadingAlbumId.value = targetAlbumId
  errorAlbumId.value = null
  try {
    await albumStore.addPhotosToAlbum(props.photoIds, 'add_to_album', targetAlbumId)

    loadingAlbumId.value = null
    successAlbumId.value = targetAlbumId

    // Play success animation (300ms)
    setTimeout(() => {
        close()
        ElMessage.success(`成功添加到相册`)
        successAlbumId.value = null
        emit('success', targetAlbumId)
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


</script>

<style scoped>
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}
.shake-animation {
  animation: shake 0.3s cubic-bezier(.36,.07,.19,.97) both;
}
</style>
