<template>
  <div class="w-full">
    <!-- Upload Area -->
    <div 
      class="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-xl p-8 text-center hover:border-primary-500 dark:hover:border-primary-500 transition-colors cursor-pointer"
      @click="triggerFileInput"
      @drop.prevent="handleDrop"
      @dragover.prevent
      @dragenter.prevent
    >
      <input 
        type="file" 
        ref="fileInput" 
        class="hidden" 
        multiple 
        accept="image/*,video/*" 
        @change="handleFileSelect"
      />
      <div class="flex flex-col items-center justify-center gap-3">
        <div class="w-12 h-12 bg-primary-50 text-primary-500 rounded-full flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        </div>
        <div class="text-gray-600 dark:text-gray-300 font-medium">
          点击或拖拽上传图片/视频
        </div>
        <div class="text-xs text-gray-400">
          支持 JPG, PNG, GIF, MP4 (最大 100MB)
        </div>
      </div>
    </div>

    <!-- File List -->
    <div v-if="files.length > 0" class="mt-6 space-y-4">
      <h3 class="font-medium text-gray-900 dark:text-white">待上传列表 ({{ files.length }})</h3>
      <div class="grid grid-cols-1 gap-3">
        <div 
          v-for="(file, index) in files" 
          :key="index"
          class="bg-white dark:bg-gray-800 rounded-lg p-3 flex items-center gap-4 shadow-sm border border-gray-100 dark:border-gray-700"
        >
          <!-- Preview -->
          <div class="w-12 h-12 rounded-md overflow-hidden bg-gray-100 flex-shrink-0">
            <img v-if="file.preview" :src="file.preview" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            </div>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <div class="flex justify-between items-center mb-1">
              <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ file.raw.name }}</p>
              <button @click="removeFile(index)" class="text-gray-400 hover:text-red-500" :disabled="uploading">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
            </div>
            <!-- Progress -->
            <div class="w-full bg-gray-200 rounded-full h-1.5 dark:bg-gray-700 overflow-hidden">
              <div 
                class="bg-primary-500 h-1.5 rounded-full transition-all duration-300"
                :style="{ width: `${file.progress}%` }"
                :class="{'bg-green-500': file.status === 'success', 'bg-red-500': file.status === 'error'}"
              ></div>
            </div>
            <div class="flex justify-between mt-1">
              <span class="text-xs text-gray-500">{{ formatSize(file.raw.size) }}</span>
              <span 
                class="text-xs"
                :class="{
                  'text-gray-500': file.status === 'pending',
                  'text-primary-500': file.status === 'uploading',
                  'text-green-500': file.status === 'success',
                  'text-red-500': file.status === 'error'
                }"
              >
                {{ getStatusText(file.status) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex justify-end gap-3 mt-4">
        <button 
          @click="clearFiles" 
          class="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          :disabled="uploading"
        >
          清空
        </button>
        <button 
          @click="startUpload" 
          class="px-4 py-2 text-sm bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors shadow-lg shadow-primary-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="uploading || files.length === 0"
        >
          {{ uploading ? '上传中...' : '开始上传' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { albumService } from '@/api/album'

const props = defineProps<{
  albumId?: string
}>()

const emit = defineEmits<{
  (e: 'upload-complete'): void
}>()

interface UploadFile {
  raw: File
  preview?: string
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
}

const fileInput = ref<HTMLInputElement | null>(null)
const files = ref<UploadFile[]>([])
const uploading = ref(false)

const triggerFileInput = () => {
  if (uploading.value) return
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    addFiles(Array.from(input.files))
  }
  input.value = '' // Reset
}

const handleDrop = (event: DragEvent) => {
  if (uploading.value) return
  const droppedFiles = event.dataTransfer?.files
  if (droppedFiles) {
    addFiles(Array.from(droppedFiles))
  }
}

const addFiles = (newFiles: File[]) => {
  const MAX_SIZE = 100 * 1024 * 1024 // 100MB
  
  newFiles.forEach(file => {
    // Validate type
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
      alert(`文件 ${file.name} 格式不支持`)
      return
    }
    
    // Validate size
    if (file.size > MAX_SIZE) {
      alert(`文件 ${file.name} 超过 100MB`)
      return
    }

    // Create preview
    let preview = undefined
    if (file.type.startsWith('image/')) {
      preview = URL.createObjectURL(file)
    }

    files.value.push({
      raw: file,
      preview,
      progress: 0,
      status: 'pending'
    })
  })
}

const removeFile = (index: number) => {
  files.value.splice(index, 1)
}

const clearFiles = () => {
  files.value = []
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '等待上传'
    case 'uploading': return '上传中...'
    case 'success': return '上传成功'
    case 'error': return '上传失败'
    default: return ''
  }
}

const startUpload = async () => {
  if (files.value.length === 0) return
  uploading.value = true

  for (const file of files.value) {
    if (file.status === 'success') continue // Skip already uploaded

    file.status = 'uploading'
    file.progress = 0

    try {
      // Check if we should use chunked upload (e.g., > 5MB)
      if (file.raw.size > 5 * 1024 * 1024) {
          await uploadChunked(file)
      } else {
          await albumService.uploadPhoto(file.raw, props.albumId)
          file.progress = 100
      }
      file.status = 'success'
    } catch (error) {
      console.error(error)
      file.status = 'error'
    }
  }

  uploading.value = false
  emit('upload-complete')
}

const uploadChunked = async (file: UploadFile) => {
    const CHUNK_SIZE = 1 * 1024 * 1024; // 1MB chunks
    const totalChunks = Math.ceil(file.raw.size / CHUNK_SIZE);
    const uploadId = await albumService.initUpload();

    for (let i = 0; i < totalChunks; i++) {
        const start = i * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.raw.size);
        const chunk = file.raw.slice(start, end);
        
        await albumService.uploadChunk(uploadId, i, chunk);
        
        // Update progress
        file.progress = Math.round(((i + 1) / totalChunks) * 100);
    }

    await albumService.finishUpload(uploadId, file.raw.name, props.albumId);
}
</script>
