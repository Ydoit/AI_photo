<template>
  <div class="people-list p-6 min-h-screen bg-gray-50 dark:bg-gray-950">
    <div class="mb-6 flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">人物相册</h1>
      
      <div class="flex items-center gap-4">
        <button 
          v-if="isMergeMode"
          @click="confirmMerge"
          :disabled="selectedIds.length < 2"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          <MergeIcon class="w-4 h-4" />
          <span>合并所选 ({{ selectedIds.length }})</span>
        </button>
        
        <button 
          @click="toggleMergeMode"
          :class="[
            'px-4 py-2 rounded-lg border transition-colors flex items-center gap-2',
            isMergeMode 
              ? 'bg-gray-200 dark:bg-gray-800 border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200' 
              : 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
          ]"
        >
          <CheckSquareIcon class="w-4 h-4" />
          <span>{{ isMergeMode ? '取消选择' : '批量管理' }}</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-6">
      <div v-for="i in 12" :key="i" class="aspect-square bg-gray-200 dark:bg-gray-800 rounded-full animate-pulse"></div>
    </div>

    <div v-else-if="identities.length === 0" class="flex flex-col items-center justify-center h-[60vh] text-gray-500">
      <UserIcon class="w-16 h-16 mb-4 opacity-20" />
      <p>暂无识别到的人物</p>
    </div>

    <div v-else class="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-6">
      <div
        v-for="person in identities" 
        :key="person.id"
        class="group flex flex-col items-center cursor-pointer"
        @click="handleCardClick(person)"
      >
        <div 
          class="relative w-full aspect-square rounded-full overflow-hidden border-2 transition-all duration-300 bg-gray-100 dark:bg-gray-800"
          :class="[
            selectedIds.includes(person.id) ? 'border-blue-500 ring-4 ring-blue-500/20' : 'border-transparent group-hover:border-gray-300 dark:group-hover:border-gray-600'
          ]"
        >
          <img
            v-if="person.cover_photo"
            :src="getPhotoUrl(person.cover_photo.photo_id)"
            class="absolute max-w-none transition-transform duration-500 group-hover:scale-110"
            :style="getFaceCropStyle(person.cover_photo)"
            loading="lazy"
          />
          <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
            <UserIcon class="w-12 h-12" />
          </div>

          <div v-if="isMergeMode" class="absolute inset-0 bg-black/10 flex items-center justify-center">
            <div 
              class="w-6 h-6 rounded-full border-2 flex items-center justify-center"
              :class="selectedIds.includes(person.id) ? 'bg-blue-500 border-blue-500' : 'bg-white/50 border-white'"
            >
              <CheckIcon v-if="selectedIds.includes(person.id)" class="w-4 h-4 text-white" />
            </div>
          </div>
        </div>

        <div class="mt-3 text-center w-full px-2">
          <div class="flex items-center justify-center gap-1">
            <span class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate max-w-[80%]">
              {{ person.identity_name }}
            </span>
            <el-dropdown v-if="!isMergeMode" trigger="click" @command="(cmd: string) => handleCommand(cmd, person)">
              <MoreVerticalIcon class="w-3 h-3 text-gray-400 hover:text-gray-600 cursor-pointer" @click.stop />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">重命名</el-dropdown-item>
                  <el-dropdown-item command="delete" divided class="text-red-500">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div class="backdrop-blur-sm text-[10px] px-1.5 py-0.5 rounded-full">
            {{ person.face_count }}个项目
          </div>
        </div>
      </div>
    </div>
    
    <el-dialog v-model="renameDialogVisible" title="重命名" width="400px">
      <el-input v-model="newName" placeholder="请输入新名称" @keyup.enter="submitRename" />
      <template #footer>
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRename">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { faceApi, type FaceIdentity, type CoverPhotoInfo } from '@/api/face'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User as UserIcon,
  MoreVertical as MoreVerticalIcon,
  CheckSquare as CheckSquareIcon,
  Check as CheckIcon,
  Merge as MergeIcon
} from 'lucide-vue-next'

const router = useRouter()
const loading = ref(true)
const identities = ref<FaceIdentity[]>([])
const isMergeMode = ref(false)
const selectedIds = ref<string[]>([])

const renameDialogVisible = ref(false)
const newName = ref('')
const currentEditingId = ref<string | null>(null)

const fetchIdentities = async () => {
  loading.value = true
  try {
    identities.value = await faceApi.listIdentities(1, 100)
  } catch (e) {
    ElMessage.error('获取人物列表失败')
  } finally {
    loading.value = false
  }
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

const toggleMergeMode = () => {
  isMergeMode.value = !isMergeMode.value
  selectedIds.value = []
}

const handleCardClick = (person: FaceIdentity) => {
  if (isMergeMode.value) {
    const idx = selectedIds.value.indexOf(person.id)
    if (idx > -1) {
      selectedIds.value.splice(idx, 1)
    } else {
      selectedIds.value.push(person.id)
    }
  } else {
    router.push(`/people/${person.id}`)
  }
}

const handleCommand = (cmd: string, person: FaceIdentity) => {
  if (cmd === 'rename') {
    currentEditingId.value = person.id
    newName.value = person.identity_name
    renameDialogVisible.value = true
  } else if (cmd === 'delete') {
    ElMessageBox.confirm('确定要删除这个人物吗？', '提示', { type: 'warning' }).then(async () => {
      try {
        await faceApi.deleteIdentity(person.id)
        ElMessage.success('删除成功')
        fetchIdentities()
      } catch (e) {
        ElMessage.error('删除失败')
      }
    })
  }
}

const submitRename = async () => {
  if (!newName.value.trim() || !currentEditingId.value) return
  try {
    await faceApi.renameIdentity(currentEditingId.value, newName.value)
    ElMessage.success('重命名成功')
    renameDialogVisible.value = false
    fetchIdentities()
  } catch (e) {
    ElMessage.error('重命名失败')
  }
}

const confirmMerge = async () => {
  if (selectedIds.value.length < 2) return
  const targetId = selectedIds.value[0]
  const target = identities.value.find(i => i.id === targetId)
  
  try {
    await ElMessageBox.confirm(`确定合并为 "${target?.identity_name}" 吗？`, '合并确认')
    await faceApi.mergeIdentities(targetId, selectedIds.value)
    ElMessage.success('合并成功')
    isMergeMode.value = false
    selectedIds.value = []
    fetchIdentities()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('合并失败')
  }
}

onMounted(fetchIdentities)
</script>

<style scoped>
/* 确保图片不会被全局样式限制 */
.max-w-none {
  max-width: none !important;
}
</style>