<template>
  <div>
    <div class="mb-8 p-6 bg-white rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
      <h2 class="text-lg font-semibold mb-4 border-b pb-2 dark:text-white">主存储设置</h2>
      <el-form :model="form" label-width="140px" class="max-w-3xl">
        <el-form-item label="图片存储根目录">
          <div class="flex gap-2 w-full">
            <el-input v-model="form.storageRoot" placeholder="例如 C:/TrailSnap/uploads" />
            <el-button type="primary" @click="validatePath" class="bg-primary-600 text-white">验证路径</el-button>
            <el-button @click="saveRoot">保存</el-button>
          </div>
          <p class="text-sm mt-2 text-gray-500">主目录用于存储上传的照片和所有缩略图。</p>
          <p class="text-sm mt-1" :class="pathStatusClass">{{ pathStatusText }}</p>
        </el-form-item>
      </el-form>
    </div>

    <div class="mb-8 p-6 bg-white rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
      <h2 class="text-lg font-semibold mb-4 border-b pb-2 dark:text-white">索引维护</h2>
      <el-form label-width="140px" class="max-w-3xl">
        <el-form-item label="重建索引">
          <el-button type="danger" @click="rebuildIndex" :disabled="indexStatus.running">立即重建索引</el-button>
          <div class="mt-4 w-full" v-if="indexStatus.running || indexStatus.progress > 0">
            <div class="flex justify-between text-sm mb-1">
              <span>进度: {{ Math.round(indexStatus.progress*100) }}%</span>
              <span v-if="indexStatus.running" class="text-blue-600 animate-pulse">正在扫描... {{ indexStatus.message }}</span>
            </div>
            <div v-if="indexStatus.current_task" class="text-xs text-gray-500 mb-1">当前任务: {{ indexStatus.current_task }}</div>
            <el-progress :percentage="Math.round(indexStatus.progress*100)" :status="indexStatus.running ? undefined : 'success'" :stroke-width="15" />
            <div class="grid grid-cols-3 gap-4 mt-2 text-sm text-center bg-gray-50 p-2 rounded">
              <div class="text-green-600">新增: {{ indexStatus.added }}</div>
              <div class="text-red-600">删除: {{ indexStatus.deleted }}</div>
              <div class="text-orange-600">错误: {{ indexStatus.errors }}</div>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="索引日志">
           <div class="w-full bg-gray-900 text-gray-100 p-4 rounded h-64 overflow-y-auto font-mono text-xs">
              <div v-for="(log, i) in logs" :key="i" class="mb-1">
                 <span class="text-gray-500">[{{ new Date(log.created_at).toLocaleTimeString() }}]</span>
                 <span :class="{'text-green-400': log.action==='added', 'text-red-400': log.action==='deleted'}"> {{ log.action.toUpperCase() }} </span>
                 <span class="text-gray-300">{{ log.file_path }}</span>
              </div>
              <div v-if="logs.length===0" class="text-gray-600 italic">暂无日志</div>
           </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { settingsApi } from '@/api/settings'
import { ElMessage } from 'element-plus'

const form = ref({ storageRoot: '' })
const pathValid = ref<boolean | null>(null)
const indexStatus = ref({ running: false, progress: 0, added: 0, deleted: 0, errors: 0, message: '', current_task: '' })
const logs = ref<any[]>([])
let pollTimer: number | null = null

const pathStatusText = computed(() => {
  if (pathValid.value === null) return ''
  return pathValid.value ? '路径有效' : '路径无效或不可写'
})

const pathStatusClass = computed(() => {
  if (pathValid.value === null) return ''
  return pathValid.value ? 'text-green-600' : 'text-red-600'
})

const loadData = async () => {
  try {
    const res = await settingsApi.getStorageRoot()
    form.value.storageRoot = res.storage_root
    if (form.value.storageRoot) validatePath()
  } catch (e) {
    console.error(e)
  }
}

const validatePath = async () => {
  if (!form.value.storageRoot) return
  try {
    await settingsApi.updateStorageRoot(form.value.storageRoot)
    pathValid.value = true
    ElMessage.success('主目录路径已更新')
    // await loadData()
  } catch {
    pathValid.value = false
    ElMessage.error('路径无效')
  }
}

const saveRoot = async () => {
  await validatePath()
}

const rebuildIndex = async () => {
  try {
    await settingsApi.rebuildIndex()
    ElMessage.success('索引重建任务已启动')
    pollStatus()
  } catch {
    ElMessage.error('启动失败')
  }
}

const fetchStatus = async () => {
  try {
      indexStatus.value = await settingsApi.getIndexStatus()
  } catch (e) {}
}

const pollStatus = async () => {
  await fetchStatus()
  await fetchLogs()
  if (indexStatus.value.running) {
    pollTimer = window.setTimeout(pollStatus, 2000)
  }
}

const fetchLogs = async () => {
  try {
      logs.value = await settingsApi.getIndexLogs(50)
  } catch (e) {}
}

onMounted(async () => {
  await loadData()
  await fetchStatus()
  await fetchLogs()
  if (indexStatus.value.running) {
    pollStatus()
  }
})

onUnmounted(() => {
    if (pollTimer) {
        clearTimeout(pollTimer)
        pollTimer = null
    }
})
</script>
