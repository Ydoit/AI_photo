<template>
  <Transition name="fade">
    <div v-if="visible" class="fixed inset-0 z-[100] flex bg-black/95 backdrop-blur-sm" @click="close" @keydown.esc="close" tabindex="0">
      
      <!-- Main Image Area -->
      <div class="flex-1 relative flex items-center justify-center h-full overflow-hidden group">
        <!-- Close Button (Mobile/Desktop) -->
        <button 
            @click.stop="close"
            class="absolute top-4 left-4 z-[102] p-2 rounded-full bg-black/20 hover:bg-black/40 text-white/70 hover:text-white transition-colors"
        >
            <X class="w-6 h-6" />
        </button>

        <!-- Navigation (Optional placeholder) -->
        <!-- 
        <button class="absolute left-4 p-3 rounded-full bg-black/20 hover:bg-black/40 text-white opacity-0 group-hover:opacity-100 transition-all">
            <ChevronLeft class="w-8 h-8" />
        </button>
        <button class="absolute right-4 p-3 rounded-full bg-black/20 hover:bg-black/40 text-white opacity-0 group-hover:opacity-100 transition-all">
            <ChevronRight class="w-8 h-8" />
        </button> 
        -->

        <img
          v-if="image"
          :src="image.url"
          class="max-w-full max-h-full object-contain transition-transform duration-300"
          @click.stop
        />
      </div>

      <!-- Sidebar (Metadata) -->
      <div 
        class="w-80 shrink-0 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800 h-full overflow-y-auto transition-all duration-300 flex flex-col"
        :class="{ 'translate-x-full w-0': !showSidebar, 'translate-x-0': showSidebar }"
        @click.stop
      >
        <!-- Header -->
        <div class="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between sticky top-0 bg-white/95 dark:bg-gray-900/95 backdrop-blur z-10">
            <h3 class="font-bold text-gray-900 dark:text-white">详细信息</h3>
            <button @click="toggleSidebar" class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500">
                <PanelRightClose v-if="showSidebar" class="w-4 h-4" />
                <PanelRightOpen v-else class="w-4 h-4" />
            </button>
        </div>

        <div v-if="loading" class="p-8 flex justify-center">
            <Loader2 class="w-6 h-6 animate-spin text-primary-500" />
        </div>

        <div v-else-if="metadata" class="p-4 space-y-6">
            
            <!-- Date & Time -->
            <div class="space-y-1">
                <div class="flex items-center gap-2 text-gray-500 text-xs font-medium uppercase tracking-wider">
                    <CalendarDays class="w-3.5 h-3.5" />
                    <span>拍摄时间</span>
                </div>
                <p class="text-sm text-gray-900 dark:text-gray-200 font-mono">
                    {{ formatTime(image?.timestamp) }}
                </p>
            </div>

            <!-- Location -->
            <div class="space-y-2">
                <div class="flex items-center justify-between text-gray-500 text-xs font-medium uppercase tracking-wider">
                    <div class="flex items-center gap-2">
                        <MapPin class="w-3.5 h-3.5" />
                        <span>位置</span>
                    </div>
                    <button 
                        v-if="!isEditing" 
                        @click="startEdit" 
                        class="text-primary-500 hover:text-primary-600"
                    >
                        编辑
                    </button>
                </div>
                
                <div v-if="isEditing" class="space-y-2">
                    <input 
                        v-model="editForm.location"
                        type="text"
                        class="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
                        placeholder="输入位置..."
                    />
                </div>
                <p v-else class="text-sm text-gray-900 dark:text-gray-200">
                    {{ 
                        metadata.location?.formatted_address || 
                        (typeof metadata.location === 'string' ? metadata.location : 
                            (metadata.location?.latitude && metadata.location?.longitude ? 
                                `${metadata.location.latitude.toFixed(6)}, ${metadata.location.longitude.toFixed(6)}` : 
                                '无位置信息'
                            )
                        ) 
                    }}
                </p>
            </div>

            <!-- Tags -->
            <div class="space-y-2">
                <div class="flex items-center justify-between text-gray-500 text-xs font-medium uppercase tracking-wider">
                    <div class="flex items-center gap-2">
                        <Tags class="w-3.5 h-3.5" />
                        <span>标签</span>
                    </div>
                </div>

                <div v-if="isEditing" class="space-y-2">
                    <div class="flex flex-wrap gap-2 mb-2">
                        <span v-for="(tag, idx) in editForm.tags" :key="idx" class="bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300 px-2 py-1 rounded-md text-xs flex items-center gap-1">
                            {{ tag }}
                            <button @click="removeTag(idx)" class="hover:text-red-500"><X class="w-3 h-3" /></button>
                        </span>
                    </div>
                    <input 
                        v-model="newTagInput"
                        @keydown.enter.prevent="addTag"
                        type="text"
                        class="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
                        placeholder="添加标签 (回车)..."
                    />
                </div>
                <div v-else class="flex flex-wrap gap-2">
                    <span v-if="(!metadata.tags || metadata.tags.length === 0)" class="text-sm text-gray-400 italic">无标签</span>
                    <span v-for="tag in metadata.tags" :key="tag" class="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 px-2.5 py-1 rounded-full text-xs">
                        {{ tag }}
                    </span>
                </div>
            </div>

            <!-- Faces -->
            <div class="space-y-2">
                <div class="flex items-center justify-between text-gray-500 text-xs font-medium uppercase tracking-wider">
                    <div class="flex items-center gap-2">
                        <User class="w-3.5 h-3.5" />
                        <span>人脸</span>
                    </div>
                </div>
                <div class="flex flex-wrap gap-2">
                    <span v-if="(!metadata.faces || metadata.faces.length === 0)" class="text-sm text-gray-400 italic">无人脸信息</span>
                    <span v-for="(face, idx) in metadata.faces" :key="idx" class="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 px-2.5 py-1 rounded-full text-xs">
                        {{ face.name || 'Unknown' }}
                    </span>
                </div>
            </div>

            <!-- EXIF (Camera Info) -->
            <div class="space-y-1">
                <div class="flex items-center gap-2 text-gray-500 text-xs font-medium uppercase tracking-wider">
                    <Camera class="w-3.5 h-3.5" />
                    <span>相机信息</span>
                </div>
                <p class="text-sm text-gray-900 dark:text-gray-200 whitespace-pre-wrap">
                    {{ metadata.exif_info || '无相机信息' }}
                </p>
            </div>

            <!-- Actions -->
            <div v-if="isEditing" class="flex items-center gap-2 pt-4 border-t border-gray-100 dark:border-gray-800">
                <button 
                    @click="saveEdit" 
                    class="flex-1 bg-primary-500 hover:bg-primary-600 text-white py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                    :disabled="saving"
                >
                    <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
                    <span v-else>保存</span>
                </button>
                <button 
                    @click="cancelEdit" 
                    class="flex-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 py-2 rounded-lg text-sm font-medium transition-colors"
                    :disabled="saving"
                >
                    取消
                </button>
            </div>

             <div v-if="!isEditing" class="pt-4 border-t border-gray-100 dark:border-gray-800">
                <button 
                     @click="handleDelete"
                     class="w-full flex items-center justify-center gap-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 py-2 rounded-lg transition-colors text-sm"
                >
                     <Trash2 class="w-4 h-4" />
                     <span>删除照片</span>
                </button>
             </div>

        </div>
      </div>

      <!-- Toggle Sidebar Button (When closed) -->
      <button 
        v-if="!showSidebar"
        @click="toggleSidebar"
        class="absolute right-4 top-4 z-[102] p-2 rounded-full bg-black/20 hover:bg-black/40 text-white/70 hover:text-white transition-colors"
      >
        <PanelRightOpen class="w-6 h-6" />
      </button>

    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, reactive } from 'vue'
import { 
    X, CalendarDays, MapPin, Tags, Camera, PanelRightClose, PanelRightOpen, 
    Loader2, Trash2, ChevronLeft, ChevronRight 
} from 'lucide-vue-next'
import { format } from 'date-fns'
import { albumService } from '@/api/album'
import type { AlbumImage } from '@/stores/albumStore'
import type { PhotoMetadata } from '@/types/album'

const props = defineProps<{
  visible: boolean
  image: AlbumImage | null
}>()

const emit = defineEmits(['close', 'delete', 'update'])

// State
const showSidebar = ref(true)
const loading = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const metadata = ref<PhotoMetadata | null>(null)

// Edit Form
const editForm = reactive({
    location: '',
    tags: [] as string[]
})
const newTagInput = ref('')

// Watchers
watch(() => props.image, async (newImg) => {
    if (newImg && props.visible) {
        await fetchMetadata(undefined, newImg.id)
    }
})

watch(() => props.visible, async (newVal) => {
    if (newVal && props.image) {
        document.body.style.overflow = 'hidden'
        if (!metadata.value || metadata.value.photo_id !== props.image.id) {
            await fetchMetadata(undefined, props.image.id)
        }
    } else {
        document.body.style.overflow = ''
        isEditing.value = false
    }
})

// Methods
const close = () => {
    emit('close')
}

const toggleSidebar = () => {
    showSidebar.value = !showSidebar.value
}

const formatTime = (ts?: number) => {
    if (!ts) return '--'
    return format(new Date(ts), 'yyyy-MM-dd HH:mm:ss')
}

const fetchMetadata = async (albumId: string | undefined, photoId: string) => {
    loading.value = true
    try {
        const data = await albumService.getMetadata(albumId, photoId)
        metadata.value = data
        // Initialize edit form
        editForm.location = typeof data.location === 'string' ? data.location : (data.location?.formatted_address || '')
        editForm.tags = Array.isArray(data.tags) ? [...data.tags] : []
    } catch (error) {
        console.error("Failed to fetch metadata", error)
    } finally {
        loading.value = false
    }
}

const startEdit = () => {
    if (!metadata.value) return
    editForm.location = typeof metadata.value.location === 'string' ? metadata.value.location : (metadata.value.location?.formatted_address || '')
    editForm.tags = Array.isArray(metadata.value.tags) ? [...metadata.value.tags] : []
    isEditing.value = true
}

const cancelEdit = () => {
    isEditing.value = false
    newTagInput.value = ''
}

const addTag = () => {
    const tag = newTagInput.value.trim()
    if (tag && !editForm.tags.includes(tag)) {
        editForm.tags.push(tag)
    }
    newTagInput.value = ''
}

const removeTag = (index: number) => {
    editForm.tags.splice(index, 1)
}

const saveEdit = async () => {
    if (!props.image || !metadata.value) return
    saving.value = true
    try {
        const updates: Partial<PhotoMetadata> = {
            location: editForm.location,
            tags: editForm.tags
        }
        const updated = await albumService.updateMetadata(undefined, props.image.id, updates)
        metadata.value = updated
        isEditing.value = false
        emit('update', { id: props.image.id, ...updates })
    } catch (error) {
        console.error("Failed to update metadata", error)
    } finally {
        saving.value = false
    }
}

const handleDelete = () => {
    if (props.image) {
        if (confirm('确定要删除这张照片吗？此操作不可恢复。')) {
            emit('delete', props.image.id)
            close()
        }
    }
}

</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>