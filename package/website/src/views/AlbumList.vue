<template>
  <div class="container mx-auto px-4 py-6 min-h-screen">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">我的相册</h1>
      <button 
        @click="openCreateModal"
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
        class="group cursor-pointer animate-in fade-in slide-in-from-bottom-4 duration-500 relative"
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
          <div class="absolute top-2 right-2 flex gap-1">
             <span v-if="album.type === 'conditional'" class="bg-black/50 backdrop-blur-sm text-white text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1">
               <Sparkles class="w-3 h-3 text-yellow-400" /> 智能
             </span>
          </div>

          <!-- Actions (Only for Custom Albums) -->
          <div v-if="album.type === 'custom'" class="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
             <button 
               @click.stop="openEditModal(album)"
               class="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-full text-gray-600 dark:text-gray-300 hover:text-primary-500 shadow-sm backdrop-blur-sm"
               title="编辑"
             >
               <Edit2 class="w-4 h-4" />
             </button>
             <button 
               @click.stop="confirmDelete(album)"
               class="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-full text-gray-600 dark:text-gray-300 hover:text-red-500 shadow-sm backdrop-blur-sm"
               title="删除"
             >
               <Trash2 class="w-4 h-4" />
             </button>
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

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div class="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
        <div class="p-6">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4">
            {{ isEditing ? '编辑相册' : '新建相册' }}
          </h3>
          
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">相册名称</label>
              <input 
                v-model="form.name"
                type="text" 
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 outline-none transition-all"
                placeholder="请输入相册名称"
                @keyup.enter="submitForm"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述 (可选)</label>
              <textarea 
                v-model="form.description"
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 outline-none transition-all resize-none"
                placeholder="相册描述..."
              ></textarea>
            </div>
          </div>

          <div class="flex justify-end gap-3 mt-6">
            <button 
              @click="closeModal" 
              class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              取消
            </button>
            <button 
              @click="submitForm" 
              class="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg shadow-lg shadow-primary-500/20 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!form.name.trim() || loading"
            >
              {{ loading ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAlbumStore, Album } from '@/stores/albumStore'
import { Plus, Sparkles, Edit2, Trash2 } from 'lucide-vue-next'
import ConditionalAlbum from '@/components/ConditionalAlbum.vue'
import CustomAlbum from '@/components/CustomAlbum.vue'
import { albumService } from '@/api/album'

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

// Modal Logic
const showModal = ref(false)
const isEditing = ref(false)
const loading = ref(false)
const currentAlbumId = ref<string | null>(null)
const form = reactive({
  name: '',
  description: ''
})

const openCreateModal = () => {
  isEditing.value = false
  currentAlbumId.value = null
  form.name = ''
  form.description = ''
  showModal.value = true
}

const openEditModal = (album: any) => {
  isEditing.value = true
  currentAlbumId.value = album.id
  form.name = album.title // Note: Store maps 'name' to 'title' in some places, check store
  form.description = album.description || ''
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const submitForm = async () => {
  if (!form.name.trim()) return
  
  loading.value = true
  try {
    if (isEditing.value && currentAlbumId.value) {
      // Update
      // Note: Store might not have update method, we can call service directly or add to store.
      // For now, call service and refresh store
      await albumService.updateAlbum(currentAlbumId.value, {
          name: form.name,
          description: form.description
      })
      // Refresh list
      await store.fetchAlbums()
    } else {
      // Create
      await store.createCustomAlbum(form.name, form.description)
    }
    closeModal()
  } catch (error) {
    console.error("Operation failed", error)
    alert("操作失败")
  } finally {
    loading.value = false
  }
}

const confirmDelete = async (album: Album) => {
  if (confirm(`确定要删除相册 "${album.title}" 吗？里面的照片也会被删除。`)) {
    try {
      await store.deleteAlbum(album.id)
    } catch (error) {
      console.error("Delete failed", error)
      alert("删除失败")
    }
  }
}
</script>
