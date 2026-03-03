<template>
  <div class="p-4 md:p-6">
    <div class="mb-4 md:mb-6 flex justify-between items-center">
      <h2 class="text-xl md:text-2xl font-bold text-gray-800 dark:text-white">用户管理</h2>
      <el-button type="danger" @click="handleLogout" class="hidden md:inline-flex">退出登录</el-button>
      <el-button type="danger" size="small" @click="handleLogout" class="md:hidden">退出</el-button>
    </div>

    <!-- Desktop View -->
    <div class="hidden md:block bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <el-table :data="users" style="width: 100%" v-loading="loading">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="角色">
          <template #default="{ row }">
            <el-tag :type="row.is_superuser ? 'danger' : 'info'">
              {{ row.is_superuser ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-popconfirm
              v-if="currentUser?.id !== row.id"
              title="确定删除该用户吗？这将删除其所有相册和照片数据（保留原文件）。"
              @confirm="handleDelete(row)"
              width="250"
            >
              <template #reference>
                <el-button type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
            <span v-else class="text-gray-400 text-sm">当前用户</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Mobile View -->
    <div class="md:hidden space-y-4" v-loading="loading">
      <div v-if="users.length === 0 && !loading" class="text-center text-gray-500 py-8">
        暂无用户数据
      </div>
      <div v-for="user in users" :key="user.id" class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div class="flex justify-between items-start mb-3">
          <div>
            <div class="font-bold text-gray-800 dark:text-white text-lg">{{ user.username }}</div>
            <div class="text-sm text-gray-500 mt-1">{{ user.email }}</div>
          </div>
          <el-tag :type="user.is_superuser ? 'danger' : 'info'" size="small">
            {{ user.is_superuser ? '管理员' : '普通用户' }}
          </el-tag>
        </div>
        
        <div class="flex justify-between items-center pt-3 border-t dark:border-gray-700">
          <div class="flex items-center gap-2">
             <span class="text-sm text-gray-500">状态:</span>
             <el-tag :type="user.is_active ? 'success' : 'danger'" size="small">
              {{ user.is_active ? '正常' : '禁用' }}
             </el-tag>
          </div>
          
          <div v-if="currentUser?.id !== user.id">
            <el-popconfirm
              title="确定删除该用户吗？"
              @confirm="handleDelete(user)"
              width="200"
            >
              <template #reference>
                <el-button type="danger" size="small" plain>删除</el-button>
              </template>
            </el-popconfirm>
          </div>
          <span v-else class="text-gray-400 text-xs">当前用户</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { userService, type User } from '@/api/user'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()
const users = ref<User[]>([])
const loading = ref(false)

const currentUser = computed(() => userStore.userInfo)

const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await userService.getUsers()
    users.value = response
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleLogout = async () => {
  await userStore.logout()
  router.push('/login')
}

const handleDelete = async (user: User) => {
  try {
    await userService.deleteUser(user.id)
    ElMessage.success('用户删除成功')
    await fetchUsers()
  } catch (error) {
    ElMessage.error('删除用户失败')
  }
}

onMounted(() => {
  fetchUsers()
  // Ensure we have current user info
  if (!userStore.userInfo) {
    userStore.getUserInfo()
  }
})
</script>
