<template>
  <div class="people-list p-6 min-h-screen bg-gray-50 dark:bg-gray-950">
    <div class="mb-6 flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">人物相册</h1>
      
      <!-- Merge Mode Toggle -->
      <div class="flex items-center gap-4">
        <button 
          v-if="isMergeMode"
          @click="confirmMerge"
          :disabled="selectedIds.length < 2"
          class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
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

    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
      <div v-for="i in 12" :key="i" class="aspect-[3/4] bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="identities.length === 0" class="flex flex-col items-center justify-center h-[60vh] text-gray-500">
      <UserIcon class="w-16 h-16 mb-4 opacity-20" />
      <p>暂无识别到的人物</p>
      <p class="text-sm mt-2">请先上传照片并运行人脸识别任务</p>
    </div>

    <!-- List -->
    <div v-else class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
      <div 
        v-for="person in identities" 
        :key="person.id"
        class="group relative bg-white dark:bg-gray-900 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden border border-transparent hover:border-gray-200 dark:hover:border-gray-700 cursor-pointer"
        :class="{ 'ring-2 ring-primary-500': selectedIds.includes(person.id) }"
        @click="handleCardClick(person)"
      >
        <!-- Selection Checkbox -->
        <div v-if="isMergeMode" class="absolute top-2 right-2 z-10">
          <div class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors"
            :class="selectedIds.includes(person.id) ? 'bg-primary-500 border-primary-500' : 'bg-white/50 border-white'"
          >
            <CheckIcon v-if="selectedIds.includes(person.id)" class="w-4 h-4 text-white" />
          </div>
        </div>

        <!-- Cover Image -->
        <div class="aspect-square relative overflow-hidden bg-gray-100 dark:bg-gray-800">
          <img 
            v-if="person.cover_photo" 
            :src="getPhotoUrl(person.cover_photo)" 
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
          <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
            <UserIcon class="w-12 h-12" />
          </div>
          
          <!-- Face Count Badge -->
          <div class="absolute bottom-2 right-2 bg-black/60 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
            <ImageIcon class="w-3 h-3" />
            <span>{{ person.face_count }}</span>
          </div>
        </div>

        <!-- Info -->
        <div class="p-4">
          <div class="flex items-center justify-between mb-1">
            <h3 class="font-medium text-gray-900 dark:text-white truncate flex-1" :title="person.identity_name">
              {{ person.identity_name }}
            </h3>
            
            <!-- Actions Dropdown -->
            <div class="relative" v-if="!isMergeMode" @click.stop>
                <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, person)">
                    <button class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
                        <MoreVerticalIcon class="w-4 h-4" />
                    </button>
                    <template #dropdown>
                        <el-dropdown-menu>
                            <el-dropdown-item command="rename">重命名</el-dropdown-item>
                            <el-dropdown-item command="delete" divided class="text-red-500">删除</el-dropdown-item>
                        </el-dropdown-menu>
                    </template>
                </el-dropdown>
            </div>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400">
             {{ person.face_count }} 张照片
          </p>
        </div>
      </div>
    </div>
    
    <!-- Rename Dialog -->
    <el-dialog v-model="renameDialogVisible" title="重命名" width="400px">
        <el-input v-model="newName" placeholder="请输入新名称" @keyup.enter="submitRename" />
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="renameDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="submitRename">确定</el-button>
            </span>
        </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { faceApi, type FaceIdentity } from '@/api/face'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  User as UserIcon, 
  Image as ImageIcon, 
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

// Rename state
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

const getPhotoUrl = (photoId: string) => {
    // Assuming backend serves thumbnails at this path
    // Or we can use the photo store utility if available
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
        ElMessageBox.confirm(
            '确定要删除这个人物吗？照片不会被删除，但人脸信息将丢失。',
            '删除确认',
            { type: 'warning' }
        ).then(async () => {
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
    
    // Use the first selected as target (or let user choose?)
    // For simplicity, let's pick the one with most faces as target? 
    // Or just the first one. Let's pick the first one as target for now.
    // Better UX: Show a dialog to choose the target name.
    
    const targetId = selectedIds.value[0]
    const target = identities.value.find(i => i.id === targetId)
    
    try {
        await ElMessageBox.confirm(
            `确定要将选中的 ${selectedIds.value.length} 个人物合并为 "${target?.identity_name}" 吗？`,
            '合并确认',
            { type: 'info' }
        )
        
        await faceApi.mergeIdentities(targetId, selectedIds.value)
        ElMessage.success('合并成功')
        isMergeMode.value = false
        selectedIds.value = []
        fetchIdentities()
    } catch (e) {
        if (e !== 'cancel') ElMessage.error('合并失败')
    }
}

onMounted(() => {
  fetchIdentities()
})
</script>
