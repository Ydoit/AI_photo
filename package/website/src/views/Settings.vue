<template>
  <div class="flex h-full bg-gray-50 dark:bg-gray-900 min-h-screen">
    <!-- Sidebar -->
    <div class="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-shrink-0">
      <div class="p-6">
        <h1 class="text-xl font-bold text-gray-800 dark:text-white">设置中心</h1>
      </div>
      <nav class="mt-2">
        <a 
          v-for="item in menuItems" 
          :key="item.key"
          @click="activeTab = item.key"
          class="flex items-center px-6 py-3 text-gray-600 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
          :class="{ 'bg-blue-50 text-primary-500 border-r-2 border-primary-500 dark:bg-gray-700': activeTab === item.key }"
        >
          <component :is="item.icon" class="w-5 h-5 mr-3" />
          {{ item.label }}
        </a>
      </nav>
    </div>

    <!-- Content Area -->
    <div class="flex-1 overflow-auto p-8">
      <UserManagement v-if="activeTab === 'user'" />
      <TaskManagement v-if="activeTab === 'tasks'" />
      <BasicSettings v-if="activeTab === 'settings'" />
      <ExternalGallery v-if="activeTab === 'external'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { User, List, Settings, FolderOpen } from 'lucide-vue-next'
import UserManagement from './settings/UserManagement.vue'
import TaskManagement from './settings/TaskManagement.vue'
import BasicSettings from './settings/BasicSettings.vue'
import ExternalGallery from './settings/ExternalGallery.vue'

const activeTab = ref('user')
const menuItems = [
  { key: 'user', label: '用户管理', icon: User },
  { key: 'tasks', label: '任务管理', icon: List },
  { key: 'settings', label: '基础设置', icon: Settings },
  { key: 'external', label: '外部图库', icon: FolderOpen },
]
</script>
