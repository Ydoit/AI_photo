<template>
  <div class="container mx-auto people-list py-6">
    <div class="mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div class="flex items-center gap-3 w-full md:w-auto bg-white/80 dark:bg-gray-900/80 backdrop-blur-md px-3 py-1.5 rounded-full shadow-sm border border-gray-200/50 dark:border-gray-700/50">
        <button @click="router.back()" class="p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors bg-white dark:bg-gray-900">
              <ArrowLeft class="w-5 h-5 text-gray-600 dark:text-gray-300" />
        </button>
        <h1 class="text-xl md:text-2xl font-bold text-gray-800 dark:text-white">人物</h1>
      </div>

      <div class="flex items-center gap-3 flex-wrap justify-end">
        <el-popover
          v-if="!isMergeMode" 
          placement="bottom-end"
          :width="200"
          trigger="click"
        >
          <template #reference>
            <button class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
              <FilterIcon class="w-5 h-5 text-gray-600 dark:text-gray-300" />
            </button>
          </template>
          
          <div class="flex flex-col gap-2">
            <div class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1 px-1">筛选显示</div>
            <el-checkbox-group v-model="filterOptions" @change="handleFilterChange" class="flex flex-col gap-2">
              <el-checkbox label="named">已添加姓名</el-checkbox>
              <el-checkbox label="unnamed">未添加姓名</el-checkbox>
              <el-checkbox label="hidden">隐藏人物</el-checkbox>
            </el-checkbox-group>
          </div>
        </el-popover>

        <template v-if="isMergeMode">
          <button 
            @click="confirmMerge"
            :disabled="selectedIds.length < 2"
            class="px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-1.5 shadow-sm text-sm"
          >
            <MergeIcon class="w-4 h-4" />
            <span>合并 ({{ selectedIds.length }})</span>
          </button>
          
          <button 
            @click="handleBulkHide"
            :disabled="selectedIds.length === 0"
            class="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 transition-all flex items-center gap-1.5 shadow-sm text-sm border border-gray-200 dark:border-gray-700"
          >
            <EyeOffIcon class="w-4 h-4" />
            <span>隐藏</span>
          </button>

          <button 
            @click="handleBulkShow"
            :disabled="selectedIds.length === 0"
            class="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 transition-all flex items-center gap-1.5 shadow-sm text-sm border border-gray-200 dark:border-gray-700"
          >
            <EyeIcon class="w-4 h-4" />
            <span>显示</span>
          </button>
        </template>
        
        <button 
          @click="toggleMergeMode"
          :class="[
            'px-4 py-2 rounded-lg border transition-all flex items-center gap-2 text-sm font-medium shadow-sm',
            isMergeMode 
              ? 'bg-gray-200 dark:bg-gray-800 border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200' 
              : 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
          ]"
        >
          <CheckSquareIcon class="w-4 h-4" />
          <span>{{ isMergeMode ? '取消' : '批量' }}</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="flow-grid">
      <div v-for="i in 15" :key="i" class="flex flex-col items-center">
        <div class="w-full aspect-square bg-gray-200 dark:bg-gray-800 rounded-full animate-pulse"></div>
        <div class="mt-3 w-16 h-3 bg-gray-200 dark:bg-gray-800 rounded animate-pulse"></div>
      </div>
    </div>

    <div v-else-if="identities.length === 0" class="flex flex-col items-center justify-center h-[60vh] text-gray-500">
      <div class="p-6 rounded-full bg-gray-100 dark:bg-gray-900 mb-4">
        <UserIcon class="w-12 h-12 opacity-20" />
      </div>
      <p class="text-lg font-medium">暂无识别到的人物</p>
      <p class="text-sm opacity-60">上传包含人脸的照片后会自动显示在此处</p>
    </div>

    <div v-else class="flow-grid">
      <div
        v-for="person in identities"
        :key="person.id"
        class="group flex flex-col items-center cursor-pointer transition-transform active:scale-95"
        :class="{ 'opacity-60': person.is_hidden }"
        @click="handleCardClick(person)"
      >
        <div
          class="relative w-full aspect-square rounded-full overflow-hidden border-2 transition-all duration-300 bg-gray-100 dark:bg-gray-800"
          :class="[
            selectedIds.includes(person.id)
              ? 'border-blue-500 ring-4 ring-blue-500/20'
              : (person.is_hidden ? 'border-dashed border-gray-400' : 'border-transparent group-hover:border-gray-300 dark:group-hover:border-gray-600')
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
            <UserIcon class="w-1/2 h-1/2" />
          </div>

          <div v-if="person.is_hidden && !isMergeMode" class="absolute inset-0 flex items-center justify-center bg-black/10">
             <EyeOffIcon class="w-8 h-8 text-white drop-shadow-md opacity-80" />
          </div>

          <div v-if="isMergeMode" class="absolute inset-0 bg-blue-500/10 flex items-center justify-center transition-opacity">
            <div
              class="w-7 h-7 rounded-full border-2 flex items-center justify-center shadow-lg"
              :class="selectedIds.includes(person.id) ? 'bg-blue-600 border-blue-600' : 'bg-white/80 border-white'"
            >
              <CheckIcon v-if="selectedIds.includes(person.id)" class="w-4 h-4 text-white" />
            </div>
          </div>
        </div>

        <div class="mt-3 text-center w-full px-1">
          <div class="flex items-center justify-center gap-1 group/name">
            <span class="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
              {{ person.identity_name }}
            </span>

            <el-dropdown v-if="!isMergeMode" trigger="click" @command="(cmd: string) => handleCommand(cmd, person)">
              <div class="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors cursor-pointer" @click.stop>
                <MoreVerticalIcon class="w-3.5 h-3.5 text-gray-400 group-hover/name:text-gray-600" />
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">编辑人物信息</el-dropdown-item>
                  <el-dropdown-item command="rescan">重新扫描人脸</el-dropdown-item>
                  <el-dropdown-item v-if="person.is_hidden" command="show">显示人物</el-dropdown-item>
                  <el-dropdown-item v-else command="hide" divided class="text-orange-500">隐藏人物</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <p class="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
            {{ person.face_count }} 个项目
          </p>
        </div>
      </div>
    </div>

    <IdentityEditDialog
      v-model:visible="editDialogVisible"
      :identity="currentEditingIdentity"
      @saved="handleEditSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { faceApi } from '@/api/face'
import type { FaceIdentity, CoverPhotoInfo } from '@/types/album'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User as UserIcon,
  MoreVertical as MoreVerticalIcon,
  CheckSquare as CheckSquareIcon,
  Check as CheckIcon,
  Merge as MergeIcon,
  ArrowLeft,
  Eye as EyeIcon,
  EyeOff as EyeOffIcon,
  RefreshCw as RefreshCwIcon,
  Filter as FilterIcon
} from 'lucide-vue-next'
import IdentityEditDialog from '@/components/IdentityEditDialog.vue'

const router = useRouter()
const loading = ref(true)
const identities = ref<FaceIdentity[]>([])
const isMergeMode = ref(false)
const selectedIds = ref<string[]>([])

// Filter
const filterOptions = ref<string[]>(['named', 'unnamed'])
try {
  const saved = localStorage.getItem('people_filter')
  if (saved) {
    filterOptions.value = JSON.parse(saved)
  }
} catch (e) {
  console.error('Failed to load filter options', e)
}

const editDialogVisible = ref(false)
const currentEditingIdentity = ref<FaceIdentity | null>(null)

const fetchIdentities = async () => {
  loading.value = true
  try {
    identities.value = await faceApi.listIdentities(1, 100, filterOptions.value)
    console.log(filterOptions.value)
  } catch (e) {
    console.error(e)
    ElMessage.error('获取人物列表失败')
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  localStorage.setItem('people_filter', JSON.stringify(filterOptions.value))
  fetchIdentities()
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
  return `${API_BASE_URL}/api/medias/${photoId}/thumbnail?size=medium`
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
    currentEditingIdentity.value = person
    editDialogVisible.value = true
  } else if (cmd === 'hide') {
    ElMessageBox.confirm('确定要隐藏这个人物吗？隐藏后将不再显示在列表中，除非在筛选中选中“隐藏”。', '提示', { type: 'warning' }).then(async () => {
      try {
        await faceApi.updateIdentity(person.id, { is_hidden: true })
        ElMessage.success('隐藏成功')
        fetchIdentities()
      } catch (e) {
        ElMessage.error('隐藏失败')
      }
    })
  } else if (cmd === 'show') {
    try {
      faceApi.updateIdentity(person.id, { is_hidden: false }).then(() => {
        ElMessage.success('显示成功')
        fetchIdentities()
      })
    } catch (e) {
      ElMessage.error('显示失败')
    }
  } else if (cmd === 'rescan') {
    ElMessage.info('正在重新扫描...')
    faceApi.rescanIdentity(person.id).then((res: any) => {
      if (res.status === 'success') {
        ElMessage.success(`重新扫描完成，关联了 ${res.count} 张人脸`)
        fetchIdentities()
      } else {
        ElMessage.error('重新扫描失败')
      }
    }).catch(() => {
      ElMessage.error('重新扫描失败')
    })
  }
}

const handleEditSaved = async () => {
  if (!currentEditingIdentity.value?.identity_name?.trim()) return
  try {
    ElMessage.success('重命名成功')
    editDialogVisible.value = false
    fetchIdentities()
  } catch (e) {
    ElMessage.error('重命名失败')
  }
}

const handleBulkHide = async () => {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确定要隐藏这 ${selectedIds.value.length} 个人物吗？`, '隐藏确认', { type: 'warning' })
    for (const id of selectedIds.value) {
      await faceApi.updateIdentity(id, { is_hidden: true })
    }
    ElMessage.success('隐藏成功')
    isMergeMode.value = false
    selectedIds.value = []
    fetchIdentities()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('隐藏失败')
  }
}

const handleBulkShow = async () => {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确定要显示这 ${selectedIds.value.length} 个人物吗？`, '显示确认', { type: 'info' })
    for (const id of selectedIds.value) {
      await faceApi.updateIdentity(id, { is_hidden: false })
    }
    ElMessage.success('显示成功')
    isMergeMode.value = false
    selectedIds.value = []
    fetchIdentities()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('显示失败')
  }
}

const confirmMerge = async () => {
  if (selectedIds.value.length < 2) return
  const targetId = selectedIds.value[0]
  const target = identities.value.find(i => i.id === targetId)
  // 取选中人物中第一个非“未命名”的人物名称
  const targetName = selectedIds.value
    .map(id => identities.value.find(i => i.id === id))
    .find(i => i?.identity_name !== '未命名')?.identity_name || target?.identity_name || '合并人物'
  try {
    await ElMessageBox.confirm(`确定合并为 "${targetName}" 吗？`, '合并确认')
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

/* 流式布局核心 CSS */
.flow-grid {
  display: grid;
  /* 关键点：自动填充，每个项最小 80px (手机)，最大 140px (PC) */
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 1.5rem; /* 对应 gap-6 */
}

/* 针对平板及以上屏幕优化尺寸 */
@media (min-width: 640px) {
  .flow-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 2rem;
  }
}

/* 针对大屏幕进一步增加尺寸 */
@media (min-width: 1280px) {
  .flow-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
}

.max-w-none {
  max-width: none !important;
}
</style>