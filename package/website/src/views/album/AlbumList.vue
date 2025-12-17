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

    <!-- Smart Albums Section -->
    <div class="mb-10">
      <h2 class="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-4 flex items-center gap-2">
        <Sparkles class="w-5 h-5 text-yellow-500" />
        智能相册
      </h2>
      <div class="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 gap-6">
        <div 
          v-for="album in smartAlbums" 
          :key="album.id"
          class="group cursor-pointer relative"
          @click="navigateToSmartAlbum(album)"
        >
          <!-- Cover -->
          <div class="aspect-square rounded-xl overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 relative shadow-sm group-hover:shadow-md transition-all duration-300 mb-3 border border-gray-100 dark:border-gray-800 flex items-center justify-center">
             <!-- Icon/Cover Content -->
             <component :is="album.icon" class="w-12 h-12 text-gray-400 group-hover:text-primary-500 transition-colors duration-300" stroke-width="1.5" />
             
             <!-- Overlay -->
             <div class="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors"></div>
          </div>
          <!-- Info -->
          <div class="mt-2">
             <h3 class="font-bold text-gray-900 dark:text-white truncate">{{ album.title }}</h3>
             <p class="text-xs text-gray-500 dark:text-gray-400">{{ album.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Custom Albums Section -->
    <div>
      <h2 class="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-4 flex items-center gap-2">
        <FolderHeart class="w-5 h-5 text-primary-500" />
        自定义相册
      </h2>
      
      <div v-if="store.allAlbums.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
        <div
          v-for="album in store.allAlbums"
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
               <span v-if="album.type === 'smart' || album.type === 'conditional'" class="bg-black/50 backdrop-blur-sm text-white text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1">
                 <Sparkles class="w-3 h-3 text-yellow-400" /> 智能
               </span>
            </div>

            <!-- Actions (Only for User Albums) -->
            <div v-if="album.type === 'user'" class="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
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
          <div class="mt-2">
            <h3 class="font-bold text-gray-900 dark:text-white truncate">{{ album.title }}</h3>
            <div class="flex justify-between items-center mt-1">
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ album.count }} 个项目</p>
              <p class="text-xs text-gray-400">{{ formatDate(album.createdAt) }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Empty State for Custom Albums -->
      <div v-else class="flex flex-col items-center justify-center py-20 text-gray-400 bg-gray-50 dark:bg-gray-800/50 rounded-xl border-dashed border-2 border-gray-200 dark:border-gray-800">
        <div class="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
          <FolderOpen class="w-8 h-8 text-gray-300 dark:text-gray-600" />
        </div>
        <p>暂无自定义相册</p>
        <button @click="openCreateModal" class="mt-4 text-primary-500 hover:underline">创建一个？</button>
      </div>
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAlbumStore, Album } from '@/stores/albumStore'
import { Plus, Sparkles, Edit2, Trash2, Clock, Users, MapPin, FolderHeart, FolderOpen } from 'lucide-vue-next'
import { albumService } from '@/api/album'
import { ElMessage, ElMessageBox } from 'element-plus'
import { format } from 'date-fns'

const router = useRouter()
const store = useAlbumStore()

const formatDate = (timestamp: number) => {
  return format(new Date(timestamp), 'yyyy-MM-dd')
}

// Smart Albums Configuration
const smartAlbums = [
  {
    id: 'recent',
    title: '最近照片',
    description: '按时间排序',
    icon: Clock,
    route: '/photos'
  },
  {
    id: 'people',
    title: '人物相册',
    description: '智能人脸识别',
    icon: Users,
    route: '/people'
  },
  {
    id: 'location',
    title: '位置',
    description: '地图视图',
    icon: MapPin,
    route: '' // Placeholder
  }
]

const navigateToSmartAlbum = (album: any) => {
  if (album.route) {
    router.push(album.route)
  } else {
    ElMessage.info('功能开发中，敬请期待')
  }
}

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
  form.name = album.title 
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
    ElMessage.error("操作失败")
  } finally {
    loading.value = false
  }
}

const confirmDelete = async (album: Album) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除相册 "${album.title}" 吗？里面的照片也会被删除。`,
      '删除相册',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await store.deleteAlbum(album.id)
    ElMessage.success('相册已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error("Delete failed", error)
      ElMessage.error("删除失败")
    }
  }
}

onMounted(async () => {
  await store.fetchAlbums()
})

</script>
