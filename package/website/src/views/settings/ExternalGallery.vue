<template>
  <div class="p-6 bg-white rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
      <h2 class="text-lg font-semibold mb-4 border-b pb-2 dark:text-white">外部图库管理</h2>
      <p class="text-sm text-gray-500 mb-4 dark:text-gray-400">
        添加外部文件夹路径，系统将扫描这些文件夹中的图片（只读模式）。
        <br>外部文件夹中的图片不会被移动或修改，生成的缩略图将存储在主目录中。
      </p>
      
      <div class="mb-4 flex flex-col sm:flex-row gap-2">
        <el-input v-model="newDir" placeholder="输入外部文件夹绝对路径" class="w-full sm:max-w-[400px]" />
        <el-button type="primary" @click="addDir" class="w-full sm:w-auto">添加目录</el-button>
      </div>

      <el-table :data="directories" style="width: 100%" border>
        <el-table-column prop="path" label="目录路径" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="removeDir(row.path)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { settingsApi } from '@/api/settings'
import { ElMessage, ElMessageBox } from 'element-plus'

const directories = ref<{path: string}[]>([])
const newDir = ref('')

const loadData = async () => {
    try {
        const res = await settingsApi.getDirectories()
        directories.value = res.external.map((d: string) => ({ path: d }))
    } catch (e) {
        console.error(e)
    }
}

const addDir = async () => {
    if (!newDir.value) return
    try {
        await settingsApi.addDirectory(newDir.value)
        newDir.value = ''
        ElMessage.success('添加成功')
        await loadData()
    } catch {
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
        await settingsApi.removeDirectory(path)
        ElMessage.success('移除成功')
        await loadData()
    } catch (e) {
        if (e !== 'cancel') ElMessage.error('移除失败')
    }
}

onMounted(() => {
    loadData()
})
</script>
