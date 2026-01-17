<template>
  <ReportPage>
    <div ref="sectionRef" class="flex flex-col justify-center h-full w-full">
      <h2 class="text-2xl font-bold text-center mb-8 text-light-text1 dark:text-white opacity-0" :class="{ 'animate-fade-in-down': isActive }">
        时光账本
      </h2>
      
      <div class="grid grid-cols-2 gap-4 md:gap-6 w-full">
        <div 
          v-for="(item, index) in items" 
          :key="index"
          class="bg-white/60 dark:bg-white/5 backdrop-blur-md rounded-2xl p-4 md:p-6 flex flex-col items-center text-center gap-3 border border-white/20 shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 opacity-0"
          :class="{ 'animate-zoom-in': isActive }"
          :style="{ animationDelay: `${index * 100}ms` }"
        >
          <component :is="item.icon" class="w-8 h-8" :class="item.color" />
          <div class="text-2xl font-bold text-light-text1 dark:text-white">{{ item.value }}</div>
          <div class="text-xs text-light-text3 dark:text-gray-400 font-medium">{{ item.label }}</div>
          <div class="text-[10px] text-light-text3/70 dark:text-gray-500">{{ item.desc }}</div>
        </div>
      </div>
    </div>
  </ReportPage>
</template>

<script setup lang="ts">
import ReportPage from './ReportPage.vue';
import type { TimeMetrics, EmotionMetrics } from '@/types/annualReport';
import { Camera, Star, Video, Tag, User, Clock } from 'lucide-vue-next';
import { ref } from 'vue';
import { useIntersectionObserver } from '@vueuse/core';

const props = defineProps<{
  time: TimeMetrics;
  emotion: EmotionMetrics;
}>();

const sectionRef = ref<HTMLElement | null>(null);
const isActive = ref(false);

useIntersectionObserver(
  sectionRef,
  ([{ isIntersecting }]) => {
    if (isIntersecting && !isActive.value) {
      isActive.value = true;
    }
  },
  { threshold: 0.3 }
);

const items = [
  {
    icon: Camera,
    value: props.time.totalPhotos,
    label: '年度留存总数',
    desc: '每一帧，都是时光的印记',
    color: 'text-blue-500'
  },
  {
    icon: User,
    value: props.emotion.livePhotos,
    label: '实况照片数',
    desc: '每一帧，都是生活的瞬间',
    color: 'text-yellow-500'
  },
  {
    icon: Video,
    value: `${(props.emotion.totalVideoDuration / 60).toFixed(0)}分钟`,
    label: '年度拍摄视频时长',
    desc: '流动的时光，都被温柔留存',
    color: 'text-cyan-500'
  },
  {
    icon: Tag,
    value: props.emotion.cameraPhotos,
    label: '相机拍摄照片数',
    desc: '镜头的偏爱，藏着生活模样',
    color: 'text-purple-500'
  }
];
</script>

<style scoped>
.animate-fade-in-down {
  animation: fadeInDown 0.8s ease-out forwards;
}

.animate-zoom-in {
  animation: zoomIn 0.6s ease-out forwards;
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes zoomIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}
</style>