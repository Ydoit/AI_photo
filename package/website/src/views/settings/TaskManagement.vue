<template>
  <div>
    <!-- Stats Cards -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-semibold text-gray-800 dark:text-white">任务管理</h2>
        <div class="flex gap-4 items-center">
             <div class="flex items-center gap-2">
                <span class="text-sm text-gray-600 dark:text-gray-300">快速模式</span>
                <el-switch v-model="fastMode" @change="handleFastModeChange" />
                <el-tooltip content="开启后将同时运行不同类型的任务（CPU/IO），最大化资源利用" placement="top">
                    <span class="text-gray-400 cursor-pointer">
                        <i class="i-mdi-help-circle-outline"></i>
                    </span>
                </el-tooltip>
             </div>
            <el-button type="primary" @click="showCreateTaskDialog">新建任务</el-button>
        </div>
      </div>
      
      <!-- Category Cards -->
      <div class="grid grid-cols-1 gap-4">
        <div v-for="cat in groupedTasks" :key="cat.category" class="border rounded-lg p-4 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
          <div class="flex justify-between items-center mb-4">
            <div class="flex items-center gap-3">
              <h3 class="text-lg font-medium dark:text-white">{{ formatCategory(cat.category) }}</h3>
              <el-tag effect="plain" size="small" class="ml-2">
                 优先级: {{ cat.priority }}
              </el-tag>
              
              <!-- Status Logic -->
              <el-tag v-if="cat.status === 'paused'" type="warning" size="small">已暂停</el-tag>
              <el-tag v-else-if="cat.pending === 0 && cat.completed > 0" type="success" size="small">已完成</el-tag>
              <el-tag v-else-if="cat.completed === 0 && cat.pending === 0" type="info" size="small">等待中</el-tag>
              <el-tag v-else type="primary" size="small">进行中</el-tag>
            </div>
            <div>
               <el-button
                 v-if="cat.status === 'paused'"
                 type="success"
                 size="small"
                 @click="resumeCategory(cat.category)"
               >继续</el-button>
               <el-button
                 v-else
                 type="warning"
                 size="small"
                 @click="pauseCategory(cat.category)"
               >暂停</el-button>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4 text-center">
             <div class="bg-white dark:bg-gray-800 p-3 rounded shadow-sm">
               <div class="text-gray-500 text-xs mb-1">待处理</div>
               <div class="text-xl font-bold text-blue-600">{{ cat.pending }}</div>
             </div>
             <div class="bg-white dark:bg-gray-800 p-3 rounded shadow-sm">
               <div class="text-gray-500 text-xs mb-1">失败</div>
               <div class="text-xl font-bold text-red-600">{{ cat.failed }}</div>
             </div>
          </div>
        </div>
      </div>

    </div>

    <!-- Create Task Dialog -->
    <el-dialog v-model="createTaskVisible" title="新建任务" width="500px" class="dark:bg-gray-800 dark:text-white">
        <el-form :model="newTaskForm" label-width="120px" class="dark:text-white">
            <el-form-item label="任务类型" class="dark:text-white">
                <el-select v-model="newTaskForm.type" placeholder="选择任务类型" class="dark:text-white">
                    <el-option label="扫描文件夹" value="SCAN_FOLDER" />
                    <el-option label="重建缩略图" value="REBUILD_THUMBNAILS" />
                    <el-option label="重建元数据" value="REBUILD_METADATA" />
                    <el-option label="人脸识别" value="RECOGNIZE_FACE" />
                    <el-option label="OCR识别" value="OCR" />
                </el-select>
            </el-form-item>
             <el-form-item label="范围" class="dark:text-white">
                <el-select v-model="newTaskForm.scope" placeholder="选择范围" class="dark:text-white">
                    <el-option label="所有图片" value="all" />
                </el-select>
            </el-form-item>
            <el-form-item label="强制处理" class="dark:text-white">
                <el-switch v-model="newTaskForm.force" active-text="是" inactive-text="否" />
                <span class="text-xs text-gray-400 ml-2">是否处理已标记为完成的项目</span>
            </el-form-item>
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="createTaskVisible = false">取消</el-button>
                <el-button type="primary" @click="submitCreateTask">创建</el-button>
            </span>
        </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { tasksApi } from '@/api/tasks'
import { ElMessage } from 'element-plus'

interface GroupedTask {
    category: string
    pending: number
    completed: number
    failed: number
    status: string
    priority: number
}

const groupedTasks = ref<GroupedTask[]>([])
const stats = ref({ failed_process_tasks: 0 })
const createTaskVisible = ref(false)
const fastMode = ref(false)
const newTaskForm = ref({
    type: '',
    scope: 'all',
    force: false
})
let taskPollTimer: number | null = null

const fetchTasks = async () => {
    try {
        groupedTasks.value = await tasksApi.getGroupedStatus()
        stats.value = await tasksApi.getTaskStats()

        // Fetch global status for fast mode
        const globalStatus = await tasksApi.getGlobalStatus()
        if (globalStatus && typeof globalStatus.fast_mode !== 'undefined') {
            fastMode.value = globalStatus.fast_mode=="True"
        }
    } catch (e) {
        console.error("Failed to fetch tasks", e)
    }
}

const handleFastModeChange = async (val: boolean) => {
    try {
        await tasksApi.toggleFastMode(val)
        ElMessage.success(val ? '快速模式已开启' : '快速模式已关闭')
    } catch (e) {
        ElMessage.error('设置失败')
        fastMode.value = !val // Revert
    }
}

const showCreateTaskDialog = () => {
    newTaskForm.value = { type: '', scope: 'all', force: false }
    createTaskVisible.value = true
}

const submitCreateTask = async () => {
    if (!newTaskForm.value.type) {
        ElMessage.warning('请选择任务类型')
        return
    }
    try {
        await tasksApi.createTask(newTaskForm.value.type, { 
            scope: newTaskForm.value.scope,
            force: newTaskForm.value.force
        })
        ElMessage.success('任务创建成功')
        createTaskVisible.value = false
        fetchTasks()
    } catch (e) {
        ElMessage.error('创建失败')
    }
}

const pauseCategory = async (category: string) => {
    try {
        await tasksApi.pauseCategory(category)
        ElMessage.success('已暂停')
        fetchTasks()
    } catch (e) {
        ElMessage.error('暂停失败')
    }
}

const resumeCategory = async (category: string) => {
    try {
        await tasksApi.resumeCategory(category)
        ElMessage.success('已继续')
        fetchTasks()
    } catch (e) {
        ElMessage.error('操作失败')
    }
}

const formatCategory = (cat: string) => {
    const map: Record<string, string> = {
        'scanning': '扫描文件夹',
        'metadata': '处理元数据',
        'face': '识别人物',
        'ocr': 'OCR识别'
    }
    return map[cat] || cat
}

onMounted(() => {
    fetchTasks()
    taskPollTimer = window.setInterval(fetchTasks, 2000)
})

onUnmounted(() => {
    if (taskPollTimer) {
        clearInterval(taskPollTimer)
        taskPollTimer = null
    }
})
</script>
