<template>
  <div class="bg-gray-100 dark:bg-neutral-800 rounded-lg mx-4 my-3 overflow-hidden transition-all duration-300">
    <!-- Header -->
    <div 
      class="flex justify-between items-center p-4 cursor-pointer"
      @click="isExpanded = !isExpanded"
    >
      <span class="text-base text-gray-800 dark:text-gray-100">内容细分</span>
      <span class="text-gray-500 transition-transform duration-300" :class="{ 'rotate-180': isExpanded }">
        ↓
      </span>
    </div>

    <!-- Content -->
    <div 
      v-show="isExpanded"
      class="px-4 pb-4 grid grid-cols-2 gap-4 text-xs text-gray-600 dark:text-gray-300"
    >
      <!-- Photos -->
      <div class="col-span-2 sm:col-span-1" @click="$router.push('/photos?type=image')">
        <div class="flex items-center space-x-2 mb-1">
          <span class="text-lg">📷</span>
          <span class="font-bold">照片：{{ data.photos.total }}</span>
        </div>
        <div class="pl-7 text-gray-500">
          {{ data.photos.sub_1_label }}: {{ data.photos.sub_1_count }} / {{ data.photos.sub_2_label }}: {{ data.photos.sub_2_count }}
        </div>
      </div>

      <!-- Videos -->
      <div class="col-span-2 sm:col-span-1" @click="$router.push('/photos?type=video')">
        <div class="flex items-center space-x-2 mb-1">
          <span class="text-lg">🎬</span>
          <span class="font-bold">视频：{{ data.videos.total }}</span>
        </div>
        <div class="pl-7 text-gray-500">
          {{ data.videos.sub_1_label }}: {{ data.videos.sub_1_count }} / {{ data.videos.sub_2_label }}: {{ data.videos.sub_2_count }}
        </div>
      </div>

      <!-- Scenery -->
      <div class="col-span-1" @click="$router.push('/albums/tags/scenery')">
        <span class="text-lg">🏞️</span> 风景：{{ data.scenery_count }}
      </div>

      <!-- Food -->
      <div class="col-span-1" @click="$router.push('/albums/tags/food')">
        <span class="text-lg">🍜</span> 美食：{{ data.food_count }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, PropType } from 'vue';
import { DashboardContentStats } from '@/api/dashboard';

defineProps({
  data: {
    type: Object as PropType<DashboardContentStats>,
    required: true
  }
});

const isExpanded = ref(false);
</script>
