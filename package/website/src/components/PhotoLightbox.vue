<template>
  <Transition name="fade">
    <div v-if="visible" class="fixed inset-0 z-[100] flex bg-black/95 backdrop-blur-sm" @click="close" @keydown.esc="close" tabindex="0">
      
      <!-- Top Toolbar (Mobile Adapted) -->
      <div class="fixed top-0 left-0 right-0 z-[102] p-2 flex items-center justify-between bg-gradient-to-b from-black/80 to-transparent pointer-events-none">
         <button 
            @click.stop="close"
            class="pointer-events-auto w-12 h-12 flex items-center justify-center rounded-full text-white/90 hover:bg-white/10 transition-colors bg-transparent p-0"
        >
            <X class="w-6 h-6" />
        </button>

        <div class="flex items-center gap-1 pointer-events-auto p-0">
            <!-- Zoom Controls -->
            <button @click.stop="zoomOut" class="w-12 h-12 flex items-center justify-center rounded-full text-white/90 hover:bg-white/10 transition-colors bg-transparent p-0">
                <ZoomOut class="w-6 h-6" />
            </button>
            <button @click.stop="zoomIn" class="w-12 h-12 flex items-center justify-center rounded-full text-white/90 hover:bg-white/10 transition-colors bg-transparent p-0">
                <ZoomIn class="w-6 h-6" />
            </button>
            
            <!-- Actions -->
            <button @click.stop="downloadImage" class="w-12 h-12 flex items-center justify-center rounded-full text-white/90 hover:bg-white/10 transition-colors bg-transparent p-0">
                <Download class="w-6 h-6" />
            </button>
            <button @click.stop="emit('add-to-album', image)" class="w-12 h-12 flex items-center justify-center rounded-full text-white/90 hover:bg-white/10 transition-colors bg-transparent p-0">
                <FolderPlus class="w-6 h-6" />
            </button>
             <button @click.stop="handleDelete" class="w-12 h-12 flex items-center justify-center rounded-full text-white/90 hover:bg-white/10 transition-colors text-red-400 hover:text-red-300 bg-transparent p-0">
                <Trash2 class="w-6 h-6" />
            </button>
            <button @click.stop="toggleSidebar" class="w-12 h-12 flex items-center justify-center rounded-full text-white/90 hover:bg-white/10 transition-colors bg-transparent p-0" :class="{ 'bg-white/20 text-white': showSidebar }">
                <Info class="w-6 h-6" />
            </button>
        </div>
      </div>

      <!-- Main Image Area -->
      <div class="flex-1 relative flex items-center justify-center h-full overflow-hidden group">
        
        <!-- Navigation -->
        <button 
            v-if="hasPrev"
            @click.stop="prev"
            class="absolute left-4 z-[101] w-12 h-12 flex items-center justify-center rounded-full hover:bg-black/40 text-white/90 transition-all p-0 bg-transparent"
        >
            <ChevronLeft class="w-8 h-8" />
        </button>
        <button 
            v-if="hasNext"
            @click.stop="next"
            class="absolute right-4 z-[101] w-12 h-12 flex items-center justify-center rounded-full hover:bg-black/40 text-white/90 transition-all p-0 bg-transparent"
        >
            <ChevronRight class="w-8 h-8" />
        </button>


        <div class="relative w-full h-full flex items-center justify-center overflow-hidden" @wheel.prevent="handleWheel">
            <img
              v-if="image"
              :src="image.url"
              class="max-w-full max-h-full object-contain transition-transform duration-200 ease-out origin-center select-none"
              :style="{ transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)` }"
              @click.stop
              @mousedown="startDrag"
              @touchstart="startTouch"
            />
        </div>
      </div>

      <!-- Sidebar (Metadata) -->
      <div 
        class="fixed inset-y-0 right-0 w-80 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800 h-full overflow-y-auto transition-transform duration-300 z-[103] shadow-2xl"
        :class="{ 'translate-x-full': !showSidebar, 'translate-x-0': showSidebar }"
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
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch, reactive, computed } from 'vue'
import { 
    X, CalendarDays, MapPin, Tags, Camera, PanelRightClose, PanelRightOpen,
    Loader2, Trash2, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Download, FolderPlus, Info
} from 'lucide-vue-next'
import { format } from 'date-fns'
import { albumService } from '@/api/album'
import type { AlbumImage } from '@/stores/albumStore'
import type { PhotoMetadata } from '@/types/album'
import { ElMessageBox, ElMessage } from 'element-plus'


interface Props {
  visible: boolean
  image: AlbumImage | null
  hasPrev?: boolean
  hasNext?: boolean
  deleteTitle?: string
  deleteMessage?: string
}

const props = withDefaults(defineProps<Props>(), {
  deleteTitle: '删除确认',
  deleteMessage: '确定要删除这张照片吗？此操作不可恢复。'
})

const emit = defineEmits(['close', 'delete', 'update', 'prev', 'next', 'add-to-album'])

// State
const showSidebar = ref(false)
const loading = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const metadata = ref<PhotoMetadata | null>(null)

// Zoom & Pan State
const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)
const isDragging = ref(false)
const startX = ref(0)
const startY = ref(0)
const initialDistance = ref(0)

// Edit Form
const editForm = reactive({
    location: '',
    tags: [] as string[]
})
const newTagInput = ref('')

// Watchers
watch(() => props.image, async (newImg) => {
    if (newImg && props.visible) {
        resetZoom()
        await fetchMetadata(undefined, newImg.id)
    }
})

watch(() => props.visible, async (newVal) => {
    if (newVal && props.image) {
        document.body.style.overflow = 'hidden'
        resetZoom()
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

// Zoom & Pan Methods
const resetZoom = () => {
    scale.value = 1
    translateX.value = 0
    translateY.value = 0
    isDragging.value = false
}

const zoomIn = () => {
    scale.value = Math.min(scale.value + 0.5, 5)
}

const zoomOut = () => {
    scale.value = Math.max(scale.value - 0.5, 1)
    if (scale.value === 1) {
        translateX.value = 0
        translateY.value = 0
    }
}

const handleWheel = (e: WheelEvent) => {
    const delta = e.deltaY > 0 ? -0.1 : 0.1
    const newScale = Math.max(1, Math.min(5, scale.value + delta))
    scale.value = newScale
    if (scale.value === 1) {
        translateX.value = 0
        translateY.value = 0
    }
}

const startDrag = (e: MouseEvent) => {
    if (scale.value > 1) {
        isDragging.value = true
        startX.value = e.clientX - translateX.value
        startY.value = e.clientY - translateY.value
        window.addEventListener('mousemove', onDrag)
        window.addEventListener('mouseup', stopDrag)
    }
}

const onDrag = (e: MouseEvent) => {
    if (isDragging.value) {
        e.preventDefault()
        translateX.value = e.clientX - startX.value
        translateY.value = e.clientY - startY.value
    }
}

const stopDrag = () => {
    isDragging.value = false
    window.removeEventListener('mousemove', onDrag)
    window.removeEventListener('mouseup', stopDrag)
}

// Touch Support (Pinch & Drag)
const startTouch = (e: TouchEvent) => {
    if (e.touches.length === 2) {
        // Pinch start
        const touch1 = e.touches[0]
        const touch2 = e.touches[1]
        initialDistance.value = Math.hypot(touch2.clientX - touch1.clientX, touch2.clientY - touch1.clientY)
    } else if (e.touches.length === 1 && scale.value > 1) {
        // Drag start
        isDragging.value = true
        startX.value = e.touches[0].clientX - translateX.value
        startY.value = e.touches[0].clientY - translateY.value
    }
    window.addEventListener('touchmove', onTouchMove, { passive: false })
    window.addEventListener('touchend', stopTouch)
}

const onTouchMove = (e: TouchEvent) => {
    if (e.touches.length === 2) {
        // Pinch move
        e.preventDefault()
        const touch1 = e.touches[0]
        const touch2 = e.touches[1]
        const currentDistance = Math.hypot(touch2.clientX - touch1.clientX, touch2.clientY - touch1.clientY)
        if (initialDistance.value > 0) {
            const delta = currentDistance / initialDistance.value
            // Smooth zoom adjustment
            const newScale = scale.value * delta
            scale.value = Math.max(1, Math.min(5, newScale))
            initialDistance.value = currentDistance // Reset for continuous zoom
        }
    } else if (e.touches.length === 1 && isDragging.value) {
        // Drag move
        e.preventDefault()
        translateX.value = e.touches[0].clientX - startX.value
        translateY.value = e.touches[0].clientY - startY.value
    }
}

const stopTouch = () => {
    isDragging.value = false
    initialDistance.value = 0
    window.removeEventListener('touchmove', onTouchMove)
    window.removeEventListener('touchend', stopTouch)
}

const downloadImage = async () => {
    if (!props.image) return
    try {
        const response = await fetch(props.image.url)
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `photo_${props.image.id}.jpg` // Simple filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        ElMessage.success('下载开始')
    } catch (e) {
        console.error('Download failed', e)
        ElMessage.error('下载失败')
    }
}

const prev = () => emit('prev')
const next = () => emit('next')

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
    if (!props.image) return
    ElMessageBox.confirm(
        '确定要删除这张照片吗？此操作不可恢复。',
        '删除确认',
        {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning',
        }
    )
    .then(() => {
        if (props.image) {
             emit('delete', props.image.id)
             close() // Close after delete, or let parent handle if it switches to next
        }
    })
    .catch(() => {
        // Cancelled
    })
}

</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>