<template>
  <div class="w-full overflow-x-auto pb-2 no-scrollbar">
    <div class="flex space-x-3 px-4 min-w-max">
      <!-- Total Media Card -->
      <div 
        class="bg-gray-100 dark:bg-neutral-800 rounded-lg p-4 w-[140px] h-[80px] flex flex-col justify-between cursor-pointer hover:scale-95 transition-transform duration-200"
        @click="$router.push('/photos')"
      >
        <div class="flex items-center space-x-2">
          <span class="text-xl">📸</span>
          <span class="text-lg font-bold text-gray-800 dark:text-gray-100">{{ data.total_media }}</span>
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">照片+视频</div>
      </div>

      <!-- Recently Updated Card -->
      <div 
        class="bg-gray-100 dark:bg-neutral-800 rounded-lg p-4 w-[140px] h-[80px] flex flex-col justify-between cursor-pointer hover:scale-95 transition-transform duration-200"
        @click="$router.push('/photos')"
      >
        <div class="flex items-center space-x-2">
          <span class="text-xl">🆕</span>
          <span class="text-lg font-bold text-gray-800 dark:text-gray-100">{{ data.today_new }}</span>
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">今日新增</div>
      </div>

      <!-- Storage Card -->
      <div 
        class="bg-gray-100 dark:bg-neutral-800 rounded-lg p-4 w-[140px] h-[80px] flex flex-col justify-between cursor-pointer hover:scale-95 transition-transform duration-200"
        @click="emit('showStorage')"
      >
        <div class="flex items-center space-x-2">
          <span class="text-xl">💾</span>
          <span class="text-lg font-bold text-gray-800 dark:text-gray-100">{{ data.storage_used }}</span>
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">占用空间</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PropType } from 'vue';
import { DashboardCard } from '@/api/dashboard';

defineProps({
  data: {
    type: Object as PropType<DashboardCard>,
    required: true,
    default: () => ({ total_media: 0, today_new: 0, storage_used: '0GB' })
  }
});

const emit = defineEmits(['showStorage']);
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
