<template>
  <div class="container mx-auto px-4 py-6 min-h-screen">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">我的相册</h1>
      <button 
        @click="createNewAlbum"
        class="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors shadow-lg shadow-primary-500/20 active:scale-95"
      >
        <Plus class="w-5 h-5" />
        <span>新建相册</span>
      </button>
    </div>

    <!-- Tabs -->
    <div class="flex space-x-6 border-b border-gray-200 dark:border-gray-700 mb-8">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="pb-3 px-1 text-sm font-medium transition-colors relative"
        :class="activeTab === tab.id ? 'text-primary-500' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
      >
        {{ tab.name }}
        <div v-if="activeTab === tab.id" class="absolute bottom-0 left-0 w-full h-0.5 bg-primary-500 rounded-t-full"></div>
      </button>
    </div>

    <!-- Album Grid/Components -->
    <div v-if="activeTab === 'smart'">
      <ConditionalAlbum />
    </div>

    <div v-else-if="activeTab === 'custom'">
      <CustomAlbum />
    </div>

    <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
      <div
        v-for="album in filteredAlbums"
        :key="album.id"
        class="group cursor-pointer animate-in fade-in slide-in-from-bottom-4 duration-500"
        @click="navigateToAlbum(album.id)"
      >
        <!-- Cover -->
        <div class="aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 relative shadow-sm group-hover:shadow-md transition-all duration-300 mb-3 border border-gray-100 dark:border-gray-800">
          <img
            :src="album.cover"
            class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
          <!-- Overlay -->
          <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors"></div>
          
          <!-- Type Badge -->
          <div class="absolute top-2 right-2">
             <span v-if="album.type === 'conditional'" class="bg-black/50 backdrop-blur-sm text-white text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1">
               <Sparkles class="w-3 h-3 text-yellow-400" /> 智能
             </span>
          </div>
        </div>
        
        <!-- Info -->
        <h3 class="font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-primary-500 transition-colors">{{ album.title }}</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ album.count }} 张照片</p>
      </div>
    </div>
    
    <!-- Empty State -->
    <div v-if="filteredAlbums.length === 0" class="flex flex-col items-center justify-center py-20 text-gray-400">
      <div class="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
        <Sparkles class="w-8 h-8 text-gray-300 dark:text-gray-600" />
      </div>
      <p>暂无相册</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAlbumStore } from '@/stores/albumStore'
import { Plus, Sparkles } from 'lucide-vue-next'
import ConditionalAlbum from '@/components/ConditionalAlbum.vue'
import CustomAlbum from '@/components/CustomAlbum.vue'

const router = useRouter()
const store = useAlbumStore()

const activeTab = ref('all')
const tabs = [
  { id: 'all', name: '全部' },
  { id: 'smart', name: '智能相册' },
  { id: 'custom', name: '我的相册' }
]

const filteredAlbums = computed(() => {
  switch (activeTab.value) {
    case 'smart': return store.conditionalAlbums
    case 'custom': return store.userAlbums
    default: return store.allAlbums
  }
})

const navigateToAlbum = (id: string) => {
  router.push(`/album/${id}`)
}

const createNewAlbum = () => {
  const title = prompt('请输入相册名称')
  if (title) {
    store.createCustomAlbum(title)
    activeTab.value = 'custom' // Switch to custom tab to see it
  }
}
</script>
