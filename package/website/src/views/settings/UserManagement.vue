<template>
  <div class="p-6">
    <div class="mb-6 flex justify-between items-center">
      <h2 class="text-2xl font-bold text-gray-800 dark:text-white">用户管理</h2>
      <el-button type="danger" @click="handleLogout">退出登录</el-button>
    </div>

    <div class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
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
