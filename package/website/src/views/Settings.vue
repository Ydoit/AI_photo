<template>
  <div class="container mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold mb-4">设置</h1>
    
    <div class="mb-8 p-6 bg-white rounded-lg shadow-sm border border-gray-100">
      <h2 class="text-lg font-semibold mb-4 border-b pb-2">主存储设置</h2>
      <el-form :model="form" label-width="140px" class="max-w-3xl">
        <el-form-item label="图片存储根目录">
          <div class="flex gap-2 w-full">
            <el-input v-model="form.storageRoot" placeholder="例如 C:/TrailSnap/uploads" />
            <el-button type="primary" @click="validatePath">验证路径</el-button>
            <el-button @click="saveRoot">保存</el-button>
          </div>
          <p class="text-sm mt-2 text-gray-500">主目录用于存储上传的照片和所有缩略图。</p>
          <p class="text-sm mt-1" :class="pathStatusClass">{{ pathStatusText }}</p>
        </el-form-item>
      </el-form>
    </div>

    <div class="mb-8 p-6 bg-white rounded-lg shadow-sm border border-gray-100">
      <h2 class="text-lg font-semibold mb-4 border-b pb-2">外部目录管理</h2>
      <p class="text-sm text-gray-500 mb-4">添加其他包含照片的文件夹，这些照片将被索引并显示在相册中（只读模式，缩略图存放在主目录）。</p>
      
      <div class="flex gap-2 mb-4 max-w-2xl">
        <el-input v-model="newDir" placeholder="输入外部目录路径 (例如 D:/MyPhotos)" />
        <el-button type="primary" @click="addDir">添加目录</el-button>
      </div>
      
      <el-table :data="directories.external.map(d => ({ path: d }))" stripe style="width: 100%" class="mb-4">
        <el-table-column prop="path" label="目录路径" />
        <el-table-column label="状态" width="120">
          <template #default>
            <el-tag type="success">已索引</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button type="danger" size="small" @click="removeDir(scope.row.path)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="mb-8 p-6 bg-white rounded-lg shadow-sm border border-gray-100">
      <h2 class="text-lg font-semibold mb-4 border-b pb-2">索引维护</h2>
      <el-form label-width="140px" class="max-w-3xl">
        <el-form-item label="重建索引">
          <el-button type="danger" @click="rebuildIndex" :disabled="indexStatus.running">立即重建索引</el-button>
          <div class="mt-4 w-full" v-if="indexStatus.running || indexStatus.progress > 0">
            <div class="flex justify-between text-sm mb-1">
              <span>进度: {{ Math.round(indexStatus.progress*100) }}%</span>
              <span v-if="indexStatus.running" class="text-blue-600 animate-pulse">正在扫描...</span>
            </div>
            <el-progress :percentage="Math.round(indexStatus.progress*100)" :status="indexStatus.running ? undefined : 'success'" :stroke-width="15" />
            <div class="grid grid-cols-3 gap-4 mt-2 text-sm text-center bg-gray-50 p-2 rounded">
              <div class="text-green-600">新增: {{ indexStatus.added }}</div>
              <div class="text-red-600">删除: {{ indexStatus.deleted }}</div>
              <div class="text-orange-600">错误: {{ indexStatus.errors }}</div>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="索引日志">
          <el-table :data="logs" height="250" stripe style="width: 100%" size="small">
            <el-table-column prop="created_at" label="时间" width="160">
              <template #default="scope">
                {{ new Date(scope.row.created_at).toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column prop="action" label="动作" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.action === 'added' ? 'success' : 'danger'" size="small">{{ scope.row.action }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="file_path" label="文件路径" show-overflow-tooltip />
          </el-table>
        </el-form-item>
      </el-form>
    </div>
  </div>
  </template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { settingsApi } from '@/api/settings'

const form = ref({ storageRoot: '' })
const pathValid = ref<boolean | null>(null)
const indexStatus = ref({ running: false, progress: 0, added: 0, deleted: 0, errors: 0 })
const logs = ref<any[]>([])
const directories = ref<{ primary: string, external: string[] }>({ primary: '', external: [] })
const newDir = ref('')

const pathStatusText = computed(() => {
  if (pathValid.value === null) return ''
  return pathValid.value ? '路径有效' : '路径无效或不可写'
})

const pathStatusClass = computed(() => {
  if (pathValid.value === null) return ''
  return pathValid.value ? 'text-green-600' : 'text-red-600'
})

const loadData = async () => {
  const res = await settingsApi.getDirectories()
  directories.value = res
  form.value.storageRoot = res.primary
}

const validatePath = async () => {
  try {
    const res = await settingsApi.updateStorageRoot(form.value.storageRoot)
    pathValid.value = true
    ElMessage.success('主目录路径已更新')
    await loadData()
  } catch {
    pathValid.value = false
    ElMessage.error('路径无效')
  }
}

const saveRoot = async () => {
  await validatePath()
}

const addDir = async () => {
  if (!newDir.value) return
  try {
    directories.value = await settingsApi.addDirectory(newDir.value)
    newDir.value = ''
    ElMessage.success('目录已添加')
  } catch (e) {
    ElMessage.error('添加失败，请检查路径是否存在')
  }
}

const removeDir = async (path: string) => {
  try {
    await ElMessageBox.confirm(`确定要移除目录 "${path}" 吗？该目录下的所有照片索引及其缩略图将被删除（源文件不会被删除）。`, '确认移除', {
      confirmButtonText: '移除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    directories.value = await settingsApi.removeDirectory(path)
    ElMessage.success('目录已移除')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('移除失败')
  }
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
  indexStatus.value = await settingsApi.getIndexStatus()
}

const pollStatus = async () => {
  await fetchStatus()
  await fetchLogs()
  if (indexStatus.value.running) {
    setTimeout(pollStatus, 2000)
  }
}

const fetchLogs = async () => {
  logs.value = await settingsApi.getIndexLogs(50)
}

onMounted(async () => {
  await loadData()
  await fetchStatus()
  await fetchLogs()
  if (indexStatus.value.running) {
    pollStatus()
  }
})
</script>

