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
             <button @click.stop="handleDelete" class="w-12 h-12 flex items-center justify-center rounded-full text-white/90 hover:bg-white/10 transition-colors text-red-400 hover:text-red-300 bg-transparent p-0">
                <Trash2 class="w-6 h-6" />
            </button>
            <button @click.stop="toggleOriginal" class="w-12 h-12 flex items-center justify-center rounded-full text-white/90 hover:bg-white/10 transition-colors bg-transparent p-0" :class="{ 'text-primary-400': showOriginal }" title="查看原图">
                <ImageIcon class="w-6 h-6" />
            </button>
            <button @click.stop="toggleSidebar" class="w-12 h-12 flex items-center justify-center rounded-full text-white/90 hover:bg-white/10 transition-colors bg-transparent p-0" :class="{ 'bg-white/20 text-white': showSidebar }">
                <Info class="w-6 h-6" />
            </button>

            <div @click.stop @mousedown.stop class="flex items-center">
                <el-dropdown trigger="click" @command="handleCommand">
                    <button class="w-12 h-12 flex items-center justify-center rounded-full text-white/90 hover:bg-white/10 transition-colors bg-transparent p-0" :class="{ 'bg-white/20 text-white': showOCR }">
                        <MoreHorizontal class="w-6 h-6" />
                    </button>
                    <template #dropdown>
                        <el-dropdown-menu class="w-36">
                            <el-dropdown-item command="ocr">
                                <div class="flex items-center gap-2">
                                    <ScanText class="w-4 h-4" />
                                    <span>{{ showOCR ? '关闭识别' : '文字识别' }}</span>
                                </div>
                            </el-dropdown-item>
                            <el-dropdown-item command="addToAlbum">
                                <div class="flex items-center gap-2">
                                    <FolderPlus class="w-4 h-4" />
                                    <span>添加到相册</span>
                                </div>
                            </el-dropdown-item>
                        </el-dropdown-menu>
                    </template>
                </el-dropdown>
            </div>
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
            <div
              v-if="image && (!image.file_type || image.file_type === 'image' || image.file_type === 'live_photo')"
              class="relative w-full h-full transition-transform duration-200 ease-out origin-center select-none flex items-center justify-center"
              :style="{ transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)` }"
              @click.stop
              @mousedown="startDrag"
              @touchstart="startTouch"
            >
                <img
                    ref="imageRef"
                    :src="displayImageSrc"
                    class="block w-full h-full object-contain pointer-events-none"
                    draggable="false"
                />
                <!-- OCR Overlay -->
                <div v-if="showOCR && ocrRecords.length > 0" class="absolute inset-0 z-10">
                    <svg viewBox="0 0 1 1" class="w-full h-full pointer-events-none" preserveAspectRatio="none">
                         <polygon
                            v-for="rec in ocrRecords"
                            :key="rec.id"
                            :points="getPolygonPoints(rec.polygon)"
                            class="fill-transparent stroke-primary-500 stroke-[0.002] cursor-pointer pointer-events-auto hover:fill-primary-500/20 hover:stroke-[0.004] transition-all"
                            :class="{ 'fill-primary-500/30 stroke-[0.004]': highlightedOCR?.id === rec.id }"
                            @click.stop="handleOCRClick(rec)"
                         />
                    </svg>
                </div>
            </div>
            <div
              v-else-if="image && image.file_type === 'video'"
              class="relative w-full h-full flex items-center justify-center"
              @click.stop
            >
              <video
                ref="videoPlayer"
                class="video-js vjs-big-play-centered vjs-theme-forest"
                controls
                preload="auto"
                :poster="image.thumbnail"
                data-setup="{}"
              >
                <source :src="image.url" type="video/mp4" />
                <p class="vjs-no-js">
                  To view this video please enable JavaScript, and consider upgrading to a
                  web browser that
                  <a href="https://videojs.com/html5-video-support/" target="_blank">supports HTML5 video</a>
                </p>
              </video>
            </div>
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
            <button @click="toggleSidebar" class="p-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-200">
                <PanelRightClose v-if="showSidebar" class="w-4 h-4" />
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

            <!-- Faces -->
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
      </div>

      <!-- OCR Panel (Separate) -->
      <div
        class="fixed inset-y-0 right-0 w-80 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800 h-full overflow-y-auto transition-transform duration-300 z-[103] shadow-2xl"
        :class="{ 'translate-x-full': !showOCR, 'translate-x-0': showOCR }"
        @click.stop
      >
        <div class="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between sticky top-0 bg-white/95 dark:bg-gray-900/95 backdrop-blur z-10">
            <h3 class="font-bold text-gray-900 dark:text-white">文字识别结果</h3>
            <button @click="toggleOCR" class="p-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-200">
                <PanelRightClose class="w-4 h-4" />
            </button>
        </div>

        <div v-if="ocrLoading" class="p-8 flex justify-center">
            <Loader2 class="w-6 h-6 animate-spin text-primary-500" />
        </div>

        <div v-else-if="ocrRecords.length === 0" class="p-8 text-center text-gray-400 text-sm">
            <ScanText class="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>暂无识别结果</p>
        </div>

        <div v-else class="p-4">
             <div
                v-for="rec in ocrRecords"
                :key="rec.id"
                class="text-sm bg-gray-50 dark:bg-gray-800 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                :class="{ 'border-primary-500 ring-1 ring-primary-500 bg-primary-50 dark:bg-primary-900/20': highlightedOCR?.id === rec.id }"
                @click="handleOCRClick(rec)"
            >
                <p class="text-gray-900 dark:text-gray-200 leading-relaxed">{{ rec.text }}</p>
            </div>
        </div>
      </div>

    </div>
  </Transition>

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
import { ref, watch, reactive, computed, onUnmounted, nextTick } from 'vue'
import {
    X, CalendarDays, MapPin, Tags, Camera, PanelRightClose, PanelRightOpen,
    Loader2, Trash2, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Download, FolderPlus, Info, User,
    FileArchiveIcon,
    FilePen,
    FileArchive,
    FileBadgeIcon,
    ScanText,
    MoreHorizontal,
    Image as ImageIcon
} from 'lucide-vue-next'
import videojs from 'video.js'
import 'video.js/dist/video-js.css'
import { format } from 'date-fns'
import { albumService } from '@/api/album'
import { ocrApi, type OCRRecord } from '@/api/ocr'
import type { PhotoMetadata, AlbumImage, CoverPhotoInfo } from '@/types/album'
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

const showOriginal = ref(false)

const displayImageSrc = computed(() => {
    if (!props.image) return ''
    if (showOriginal.value) return props.image.url
    return props.image.preview || props.image.url
})

watch(() => props.image, () => {
    showOriginal.value = false
})

const toggleOriginal = () => {
    showOriginal.value = !showOriginal.value
}

/**
 * 核心算法：计算人脸裁切样式
 * 原理：通过 absolute 定位和百分比控制，使人脸区域充满圆形容器
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

const getPhotoUrl = (photoId: string) => {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
  return `${API_BASE_URL}/api/medias/${photoId}/thumbnail`
}

const emit = defineEmits(['close', 'delete', 'update', 'prev', 'next', 'add-to-album'])

// State
const showSidebar = ref(false)
const showExifDialog = ref(false)
const loading = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const metadata = ref<PhotoMetadata | null>(null)

const parsedExif = computed(() => {
    if (!metadata.value?.exif_info) return []
    const info = metadata.value.exif_info
    
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


// OCR State
const showOCR = ref(false)
const ocrLoading = ref(false)
const ocrRecords = ref<OCRRecord[]>([])
const highlightedOCR = ref<OCRRecord | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)

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

// Video Player State
const videoPlayer = ref<HTMLElement | null>(null)
const player = ref<any>(null)

const initPlayer = () => {
    if (videoPlayer.value && !player.value) {
        player.value = videojs(videoPlayer.value, {
            controls: true,
            autoplay: true,
            preload: 'auto',
            fluid: false, // Responsive
            fill: true,
            controlBar: {
                children: [
                    'playToggle',
                    'volumePanel',
                    'currentTimeDisplay',
                    'timeDivider',
                    'durationDisplay',
                    'progressControl',
                    'fullscreenToggle',
                ]
            }
        })
    }
}

const disposePlayer = () => {
    if (player.value) {
        player.value.dispose()
        player.value = null
    }
}

onUnmounted(() => {
    disposePlayer()
})

// Watchers
watch(() => props.image, async (newImg, oldImg) => {
    if (newImg && props.visible) {
        resetZoom()
        highlightedOCR.value = null
        if (showOCR.value) {
            await fetchOCR(newImg.id)
        } else {
            ocrRecords.value = []
        }
        
        // Dispose old player if switching from video
        if (oldImg?.file_type === 'video') {
            disposePlayer()
        }
        
        // Init new player if switching to video
        if (newImg.file_type === 'video') {
            await nextTick()
            initPlayer()
        }
        
        await fetchMetadata(undefined, newImg.id)
        await fetchOCR(newImg.id)
    } else {
        // If image is null (closed or cleared), dispose
        disposePlayer()
    }
})

watch(() => props.visible, async (newVal) => {
    if (newVal && props.image) {
        document.body.style.overflow = 'hidden'
        resetZoom()
        
        if (props.image.file_type === 'video') {
            await nextTick()
            initPlayer()
        }
        
        if (!metadata.value || metadata.value.photo_id !== props.image.id) {
            await fetchMetadata(undefined, props.image.id)
        }
    } else {
        document.body.style.overflow = ''
        isEditing.value = false
        disposePlayer()
    }
})

// Methods
const close = () => {
    emit('close')
}


const toggleSidebar = () => {
    showSidebar.value = !showSidebar.value
    if (showSidebar.value) {
        showOCR.value = false // Close OCR if Sidebar opens
    }
}

const handleCommand = (command: string) => {
    if (command === 'ocr') {
        toggleOCR()
    } else if (command === 'addToAlbum') {
        emit('add-to-album', props.image)
    }
}

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

// OCR Methods
const toggleOCR = async () => {
    showOCR.value = !showOCR.value
    if (showOCR.value) {
        showSidebar.value = false // Close Sidebar if OCR opens
        if (props.image) {
            await fetchOCR(props.image.id)
        }
    }
}

const fetchOCR = async (photoId: string) => {
    ocrLoading.value = true
    try {
        const res = await ocrApi.getOCR(photoId)
        ocrRecords.value = res.records
    } catch (error) {
        console.error("Failed to fetch OCR records", error)
        ElMessage.error("获取OCR记录失败")
    } finally {
        ocrLoading.value = false
    }
}

const getPolygonPoints = (polygon: number[][]) => {
    return polygon.map(p => p.join(',')).join(' ')
}

const handleOCRClick = (record: OCRRecord) => {
    highlightedOCR.value = record
    if (!showSidebar.value) {
        showSidebar.value = true
    }

    // 复制到剪贴板（带完整容错+降级）
    if (record?.text) { // 先判断record.text是否存在
        const text = record.text.trim()
        if (!text) return ElMessage.warning('无可复制的文本')

        // 方案1：优先使用原生 Clipboard API（现代浏览器）
        if (navigator?.clipboard) { // 双层判断：navigator和clipboard都存在
            try {
                navigator.clipboard.writeText(text)
                ElMessage.success('复制成功')
            } catch (err) {
                // API调用失败，降级到方案2
                fallbackCopyToClipboard(text)
            }
        } 
        // 方案2：降级到document.execCommand（兼容旧浏览器/非安全上下文）
        else {
            fallbackCopyToClipboard(text)
        }
    }
}

// 降级复制方法（无依赖，兼容所有浏览器）
const fallbackCopyToClipboard = (text: string) => {
    // 创建隐藏的文本框
    const textArea = document.createElement('textarea')
    textArea.value = text
    // 避免滚动条/页面闪烁
    textArea.style.position = 'fixed'
    textArea.style.top = '-9999px'
    textArea.style.left = '-9999px'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)

    // 选中文本并复制
    textArea.select()
    textArea.setSelectionRange(0, text.length) // 兼容移动设备

    try {
        const isSuccess = document.execCommand('copy')
        if (isSuccess) {
            ElMessage.success('复制成功')
        } else {
            ElMessage.warning('复制失败，请手动选中文本复制')
        }
    } catch (err) {
        ElMessage.error('复制失败，请手动选中文本复制')
    } finally {
        // 无论成败，都移除临时文本框
        document.body.removeChild(textArea)
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
        a.download = `${props.image.filename}` || `photo_${props.image.id}.jpg` // Simple filename
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
:deep(.video-js .vjs-tech) {
  object-fit: contain;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>