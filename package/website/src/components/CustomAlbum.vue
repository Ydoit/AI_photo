<template>
  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6 animate-in fade-in duration-500">
    <!-- Create New Card -->
    <div 
      @click="createNewAlbum"
      class="group cursor-pointer flex flex-col items-center justify-center aspect-square rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-500 transition-colors bg-gray-50/50 dark:bg-gray-800/50"
    >
      <div class="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-700 group-hover:bg-primary-50 dark:group-hover:bg-primary-900/20 flex items-center justify-center transition-colors mb-3">
        <Plus class="w-6 h-6 text-gray-400 group-hover:text-primary-500 transition-colors" />
      </div>
      <span class="text-sm font-medium text-gray-500 group-hover:text-primary-500 transition-colors">新建相册</span>
    </div>

    <!-- Album Cards -->
    <div
      v-for="album in userAlbums"
      :key="album.id"
      class="group cursor-pointer relative"
      @click="navigateToAlbum(album.id)"
    >
      <div class="aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 relative shadow-sm group-hover:shadow-md transition-all duration-300 mb-3 border border-gray-100 dark:border-gray-800">
        <img
          :src="album.cover"
          class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
        <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors"></div>
        
        <!-- Delete Button -->
        <div class="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <button 
            @click.stop="handleDelete(album.id, album.title)"
            class="p-1.5 bg-red-500/80 hover:bg-red-600 backdrop-blur-sm text-white rounded-full transition-colors shadow-sm"
            title="删除相册"
          >
            <Trash2 class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      
      <h3 class="font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-primary-500 transition-colors">{{ album.title }}</h3>
      <p class="text-sm text-gray-500 dark:text-gray-400">{{ album.count }} 张照片</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAlbumStore } from '@/stores/albumStore'
import { Plus, Trash2 } from 'lucide-vue-next'

const router = useRouter()
const store = useAlbumStore()

const userAlbums = computed(() => store.userAlbums)

const navigateToAlbum = (id: string) => {
  router.push(`/album/${id}`)
}

const createNewAlbum = () => {
  const title = prompt('请输入相册名称')
  if (title) {
    store.createCustomAlbum(title)
  }
}

const handleDelete = (id: string, title: string) => {
  if (confirm(`确定要删除相册 "${title}" 吗？此操作不可恢复。`)) {
    store.deleteCustomAlbum(id)
  }
}
</script>
