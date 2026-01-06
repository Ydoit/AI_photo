<template>
  <div
    class="fixed inset-y-0 right-0 w-80 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800 h-full overflow-y-auto transition-transform duration-300 z-[103] shadow-2xl"
    :class="{ 'translate-x-full': !visible, 'translate-x-0': visible }"
    @click.stop
  >
    <!-- Header -->
    <div class="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between sticky top-0 bg-white/95 dark:bg-gray-900/95 backdrop-blur z-10">
        <h3 class="font-bold text-gray-900 dark:text-white">详细信息</h3>
        <button @click="$emit('close')" class="p-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-200">
            <PanelRightClose v-if="visible" class="w-4 h-4" />
            <PanelRightOpen v-else class="w-4 h-4" />
        </button>
    </div>

    <div v-if="loading" class="p-8 flex justify-center">
        <Loader2 class="w-6 h-6 animate-spin text-primary-500" />
    </div>

    <div v-else-if="metadata" class="p-4 space-y-6">
        <!-- File Name & Info -->
        <div class="space-y-1">
            <div class="flex items-center gap-2 text-gray-500 text-xs font-medium uppercase tracking-wider">
                <Info class="w-3.5 h-3.5" />
                <span>基本信息</span>
            </div>
            <!-- 文件名过长时自动换行 -->
            <p class="text-sm text-gray-900 dark:text-gray-200 font-mono break-all font-bold">
                {{ image?.filename || '无文件名' }}
            </p>
             <div class="text-xs text-gray-500 flex gap-2">
                <span v-if="image?.width && image?.height">{{ image.width }} x {{ image.height }}</span>
                <span>{{ formatSize(image?.size) }}</span>
            </div>
            <button @click="showExifDialog = true" class="text-xs text-primary-500 hover:text-primary-400 hover:underline pt-1">
                查看文件 EXIF 信息
            </button>
        </div>
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
                    <span>地理位置</span>
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
                    metadata.address || '无位置信息'
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
                        {{ tag.tag_name }}
                        <button @click="removeTag(idx, tag.id)" class="hover:text-red-500"><X class="w-3 h-3" /></button>
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
                <a  target="_blank" :href="`/classification/${tag.tag_name}`" v-for="tag in metadata.tags" :key="tag.id" class="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 px-2.5 py-1 rounded-full text-xs">
                    {{ tag.tag_name }}
                </a>
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
                <span v-if="(!metadata.faces_identities || metadata.faces_identities.length === 0)" class="text-sm text-gray-400 italic">无人脸信息</span>
                <a target="_blank" :href="`/people/${face.id}`" v-for="(face, idx) in metadata.faces_identities" :key="idx" class="text-gray-600 dark:text-gray-300 rounded-full text-xs flex flex-col items-center transition-colors">
                    <div
                    class="relative w-12 aspect-square rounded-full overflow-hidden border-2 transition-all duration-300 bg-gray-100 dark:bg-gray-800"
                    :class="['border-transparent group-hover:border-gray-300 dark:group-hover:border-gray-600']"
                    >
                        <img
                            v-if="face.cover_photo"
                            :src="getPhotoUrl(face.cover_photo.photo_id)"
                            class="absolute max-w-none transition-transform duration-500 group-hover:scale-110"
                            :style="getFaceCropStyle(face.cover_photo)"
                            loading="lazy"
                        />
                        <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                            <UserIcon class="w-1/2 h-1/2" />
                        </div>
                    </div>
                    <span class="font-medium">{{ face.identity_name || 'Unknown' }}</span>
                </a>
            </div>
        </div>

        <!-- Albums -->
        <div class="space-y-2">
            <div class="flex items-center justify-between text-gray-500 text-xs font-medium uppercase tracking-wider">
                <div class="flex items-center gap-2">
                    <User class="w-3.5 h-3.5" />
                    <span>相册</span>
                </div>
            </div>
            <div class="flex flex-wrap gap-2">
                <span v-if="(!metadata.albums || metadata.albums.length === 0)" class="text-sm text-gray-400 italic">无相册信息</span>
                <a v-for="(album, idx) in metadata.albums" target="_blank" :key="idx" :href="`/album/${album.id}`" class="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 px-2.5 py-1 rounded-full text-xs">
                    {{ album.name || 'Unknown' }}
                </a>
            </div>
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
    <div v-else-if="!metadata">
         <span class="text-sm text-gray-400 italic">无元数据信息，请等待元数据处理完成之后再试</span>
         <a href='/settings#task-management'  class="text-sm text-primary-500 hover:underline">点击查看任务管理</a>
    </div>
  </div>

  <!-- EXIF Dialog -->
  <el-dialog
    v-model="showExifDialog"
    title="EXIF 详细信息"
    width="500px"
    align-center
  >
    <div v-if="parsedExif.length > 0" class="max-h-[60vh] overflow-y-auto border border-gray-100 dark:border-gray-800 rounded-lg">
        <table class="w-full text-sm text-left">
            <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                <tr v-for="(item, index) in parsedExif" :key="index" class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td class="px-4 py-3 font-medium text-gray-500 bg-gray-50/50 dark:bg-gray-900/50 w-1/3">{{ item.label }}</td>
                    <td class="px-4 py-3 text-gray-900 dark:text-gray-200 font-mono break-all">{{ item.value }}</td>
                </tr>
            </tbody>
        </table>
    </div>
    <div v-else class="text-center text-gray-500 py-8">
        暂无 EXIF 信息
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import {
    X, CalendarDays, MapPin, Tags, PanelRightClose, PanelRightOpen,
    Loader2, Trash2, Info, User,
    User as UserIcon
} from 'lucide-vue-next'
import { format } from 'date-fns'
import { albumService } from '@/api/album'
import type { PhotoMetadata, AlbumImage, CoverPhotoInfo, Tag } from '@/types/album'
import { ElMessageBox, ElMessage } from 'element-plus'

interface Props {
  visible: boolean
  image: AlbumImage | null
  metadata: PhotoMetadata | null
  loading: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'delete', 'update'])

// State
const showExifDialog = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const newTagInput = ref('')

const editForm = reactive({
    location: '',
    tags: [] as Tag[]
})

// Computed
const parsedExif = computed(() => {
    if (!props.metadata?.exif_info) return []
    const info = props.metadata.exif_info
    
    // Attempt to parse as JSON first
    try {
        if (info.trim().startsWith('{')) {
             const obj = JSON.parse(info)
             return Object.entries(obj).map(([k, v]) => ({ label: k, value: String(v) }))
        }
    } catch (e) {
        // Ignore JSON error
    }

    // Fallback to line-based parsing
    return info.split('\n')
        .map(line => {
            const idx = line.indexOf(':')
            if (idx === -1) return null
            return {
                label: line.slice(0, idx).trim(),
                value: line.slice(idx + 1).trim()
            }
        })
        .filter((item): item is { label: string, value: string } => item !== null && item.label !== '' && item.value !== '')
})

// Methods
const formatTime = (ts?: number) => {
    if (!ts) return '--'
    return format(new Date(ts), 'yyyy-MM-dd HH:mm:ss')
}

const formatSize = (bytes?: number) => {
    if (bytes === undefined) return '--'
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getPhotoUrl = (photoId: string) => {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
  return `${API_BASE_URL}/api/medias/${photoId}/thumbnail`
}

/**
 * 核心算法：计算人脸裁切样式
 */
const getFaceCropStyle = (cover: CoverPhotoInfo) => {
  if (!cover.face_rect || !cover.width || !cover.height) {
    return {}
  }

  // face_rect: [x1, y1, x2, y2]
  const [x1, y1, x2, y2] = cover.face_rect
  const faceW = x2 - x1
  const faceH = y2 - y1

  // 1. 确定裁切基准（取人脸宽高的最大值，并增加 60% 的留白防止太挤）
  const cropSize = Math.max(faceW, faceH) * 1.6

  // 2. 计算缩放比例：容器宽度 / 裁切目标在原图中的宽度
  // 这里直接用百分比：(原图宽 / 裁切宽) * 100%
  const widthPct = (cover.width / cropSize) * 100
  const heightPct = (cover.height / cropSize) * 100

  // 3. 计算人脸中心点坐标（百分比）
  const centerX = (x1 + x2) / 2
  const centerY = (y1 + y2) / 2
  const leftPct = (centerX / cover.width) * 100
  const topPct = (centerY / cover.height) * 100

  return {
    width: `${widthPct.toFixed(2)}%`,
    height: `${heightPct.toFixed(2)}%`,
    left: '50%',
    top: '50%',
    // 将图片中心移动到容器中心，再根据人脸中心点进行偏移
    transform: `translate(-${leftPct.toFixed(2)}%, -${topPct.toFixed(2)}%)`,
  }
}

const startEdit = () => {
    if (!props.metadata) return
    editForm.location = typeof props.metadata.location === 'string' ? props.metadata.location : (props.metadata.location?.formatted_address || '')
    editForm.tags = Array.isArray(props.metadata.tags) ? [...props.metadata.tags] : []
    isEditing.value = true
}

const cancelEdit = () => {
    isEditing.value = false
    newTagInput.value = ''
}

const addTag = async () => {
    const tag = newTagInput.value.trim()
    if (!tag || !props.image) return
    
    // Check if tag already exists in current edit form
    if (editForm.tags.some(t => t.tag_name === tag)) {
        ElMessage.warning('标签已存在')
        return
    }

    try {
        const newTag = await albumService.addPhotoTag(props.image.id, tag, 1.0)
        
        // Update local state
        if (!editForm.tags.find(t => t.id === newTag.id)) {
            editForm.tags.push(newTag)
        }
        
        // Emit update to parent to keep sync (optional, but good for consistency)
        // Since we are editing, we don't necessarily update parent metadata until save, 
        // BUT for tags, the API is called immediately. So we SHOULD update parent.
        // We construct a new metadata object with updated tags.
        if (props.metadata) {
             const updatedTags = props.metadata.tags ? [...props.metadata.tags] : []
             if (!updatedTags.find(t => t.id === newTag.id)) {
                 updatedTags.push(newTag)
             }
             emit('update', { id: props.image.id, tags: updatedTags })
        }
        
        newTagInput.value = ''
        ElMessage.success('标签添加成功')
    } catch (error) {
        console.error("Failed to add tag", error)
        ElMessage.error('添加标签失败')
    }
}

const removeTag = async (index: number, tagId: string) => {
    if (!props.image) return
    try {
        await albumService.deletePhotoTag(props.image.id, tagId)
        
        editForm.tags = editForm.tags.filter(t => t.id !== tagId)
        
        if (props.metadata && props.metadata.tags) {
             const updatedTags = props.metadata.tags.filter(t => t.id !== tagId)
             emit('update', { id: props.image.id, tags: updatedTags })
        }
        ElMessage.success('标签删除成功')
    } catch (error) {
        console.error("Failed to delete tag", error)
        ElMessage.error('删除标签失败')
    }
}

const saveEdit = async () => {
    if (!props.image || !props.metadata) return
    saving.value = true
    try {
        const updates: Partial<PhotoMetadata> = {
            location: editForm.location,
            // Tags are handled separately via immediate API calls
        }
        const updated = await albumService.updateMetadata(undefined, props.image.id, updates)
        
        // Construct the full metadata object to pass back
        // We use the updated metadata from server (which has location) and our local tags
        const newMetadata = { ...updated, tags: editForm.tags } 
        
        isEditing.value = false
        // Emit update with the new metadata
        emit('update', { id: props.image.id, ...newMetadata })
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
        }
    })
}
</script>
