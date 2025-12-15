<template>
  <div>
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg border border-red-100 dark:border-red-900/30">
            <h3 class="text-sm font-medium text-red-800 dark:text-red-300">数据库新增失败</h3>
            <p class="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{{ stats.failed_process_tasks }}</p>
        </div>
    </div>

    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-semibold text-gray-800 dark:text-white">任务列表</h2>
        <el-button type="primary" @click="showCreateTaskDialog">新建任务</el-button>
      </div>
      <el-table :data="tasks" style="width: 100%" border class="dark:border-gray-700 dark:text-white dark:bg-gray-800">
        <el-table-column prop="type" label="任务类型" width="180">
             <template #default="{ row }">
                 {{ formatTaskType(row.type) }}
             </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ formatStatus(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度">
          <template #default="{ row }">
            <div v-if="row.total_items > 0">
                <el-progress :percentage="Math.round((row.processed_items / row.total_items) * 100)" />
                <span class="text-xs text-gray-500 dark:text-gray-400">{{ row.processed_items }} / {{ row.total_items }}</span>
            </div>
            <div v-else-if="row.status === 'completed'">
                 <el-progress :percentage="100" status="success" />
            </div>
             <div v-else>
                 -
             </div>
          </template>
        </el-table-column>
         <el-table-column prop="created_at" label="创建时间" width="180">
             <template #default="{ row }">
                 {{ formatDate(row.created_at) }}
             </template>
         </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button 
                size="small" 
                type="danger" 
                :disabled="['completed', 'failed', 'cancelled'].includes(row.status)"
                @click="cancelTask(row.id)"
            >取消</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Create Task Dialog -->
    <el-dialog v-model="createTaskVisible" title="新建任务" width="500px" class="dark:bg-gray-800 dark:text-white">
        <el-form :model="newTaskForm" label-width="120px" class="dark:text-white">
            <el-form-item label="任务类型" class="dark:text-white">
                <el-select v-model="newTaskForm.type" placeholder="选择任务类型" class="dark:text-white">
                    <el-option label="重建缩略图" value="REBUILD_THUMBNAILS" />
                    <el-option label="重建元数据" value="REBUILD_METADATA" />
                </el-select>
            </el-form-item>
             <el-form-item label="范围" class="dark:text-white">
                <el-select v-model="newTaskForm.scope" placeholder="选择范围" class="dark:text-white">
                    <el-option label="所有图片" value="all" />
                </el-select>
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
import { tasksApi, type Task } from '@/api/tasks'
import { ElMessage, ElMessageBox } from 'element-plus'

const tasks = ref<Task[]>([])
const stats = ref({ failed_process_tasks: 0 })
const createTaskVisible = ref(false)
const newTaskForm = ref({
    type: '',
    scope: 'all'
})
let taskPollTimer: number | null = null

const fetchTasks = async () => {
    try {
        tasks.value = await tasksApi.listTasks()
        stats.value = await tasksApi.getTaskStats()
    } catch (e) {
        console.error("Failed to fetch tasks", e)
    }
}

const showCreateTaskDialog = () => {
    newTaskForm.value = { type: '', scope: 'all' }
    createTaskVisible.value = true
}

const submitCreateTask = async () => {
    if (!newTaskForm.value.type) {
        ElMessage.warning('请选择任务类型')
        return
    }
    try {
        await tasksApi.createTask(newTaskForm.value.type, { scope: newTaskForm.value.scope })
        ElMessage.success('任务创建成功')
        createTaskVisible.value = false
        fetchTasks()
    } catch (e) {
        ElMessage.error('创建失败')
    }
}

const cancelTask = async (taskId: string) => {
    try {
        await ElMessageBox.confirm('确定要取消该任务吗？', '提示', { type: 'warning' })
        await tasksApi.cancelTask(taskId)
        ElMessage.success('任务已取消')
        fetchTasks()
    } catch (e) {
        if (e !== 'cancel') ElMessage.error('取消失败')
    }
}

const formatTaskType = (type: string) => {
    const map: Record<string, string> = {
        'SCAN_FOLDER': '扫描文件夹',
        'PROCESS_IMAGE': '处理图片',
        'GENERATE_THUMBNAIL': '生成缩略图',
        'EXTRACT_METADATA': '提取元数据',
        'REBUILD_THUMBNAILS': '重建缩略图',
        'REBUILD_METADATA': '重建元数据'
    }
    return map[type] || type
}

const getStatusType = (status: string) => {
    const map: Record<string, string> = {
        'pending': 'info',
        'processing': 'primary',
        'completed': 'success',
        'failed': 'danger',
        'cancelled': 'warning'
    }
    return map[status] || ''
}

const formatStatus = (status: string) => {
     const map: Record<string, string> = {
        'pending': '等待中',
        'processing': '进行中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
    }
    return map[status] || status
}

const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
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
