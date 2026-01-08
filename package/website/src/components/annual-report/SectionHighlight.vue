<script setup lang="ts">
import ReportPage from './ReportPage.vue';
import type { MemoryMetrics, EasterEgg } from '@/types/annualReport';
import { User, MapPin, Calendar, Zap } from 'lucide-vue-next';
import { ref } from 'vue';
import { useIntersectionObserver } from '@vueuse/core';

const props = defineProps<{
  memory: MemoryMetrics;
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
    icon: User,
    label: '年度出镜最多的人',
    value: `${props.memory.topPersonName}`,
    subValue: `${props.memory.topPersonCount} 次`,
    desc: '陪伴是最长情的告白',
    color: 'text-pink-500',
    bg: 'bg-pink-100 dark:bg-pink-900/30'
  },
  {
    icon: MapPin,
    label: '年度打卡最多的地点',
    value: props.memory.topLocation,
    desc: '心安之处即是故乡',
    color: 'text-green-500',
    bg: 'bg-green-100 dark:bg-green-900/30'
  },
  {
    icon: Calendar,
    label: '年度最忙碌的一天',
    value: props.memory.maxPhotoDay,
    subValue: `${props.memory.maxPhotoDayCount} 张`,
    desc: '那一天的快乐，不曾褪色',
    color: 'text-blue-500',
    bg: 'bg-blue-100 dark:bg-blue-900/30'
  },
  {
    icon: Zap,
    label: `年度相机品牌：${props.memory.topMake}`,
    value: `${props.memory.topModel}`,
    subValue: `${props.memory.topMakeModelCount} 次`,
    desc: '记录下每一个瞬间',
    color: 'text-yellow-500',
    bg: 'bg-yellow-100 dark:bg-yellow-900/30'
  }
];
</script>

<template>
  <ReportPage>
    <div ref="sectionRef" class="flex flex-col h-full w-full justify-center">
        <h2 class="text-2xl font-bold text-center mb-10 text-light-text1 dark:text-white opacity-0" :class="{ 'animate-fade-in-down': isActive }">
            高光时刻
        </h2>

        <div class="flex flex-col gap-6">
            <div 
                v-for="(item, index) in items" 
                :key="index"
                class="flex items-center gap-4 p-2 rounded-xl hover:bg-white/30 dark:hover:bg-white/5 transition-colors opacity-0"
                :class="{ 'animate-slide-in-right': isActive }"
                :style="{ animationDelay: `${index * 150}ms` }"
            >
                <div class="w-12 h-12 rounded-full flex items-center justify-center shrink-0" :class="item.bg">
                    <component :is="item.icon" class="w-6 h-6" :class="item.color" />
                </div>

                <div class="flex-1">
                    <div class="flex items-baseline justify-between">
                        <span class="text-lg font-bold text-light-text1 dark:text-gray-100">{{ item.label }}</span>
                    </div>
                    <div class="flex items-baseline gap-2 mt-1">
                        <span class="text-xl font-bold text-primary-amber">{{ item.value }}</span>
                        <span v-if="item.subValue" class="text-sm text-light-text3 dark:text-gray-400">{{ item.subValue }}</span>
                    </div>
                    <div class="text-xs text-light-text3/70 dark:text-gray-500 mt-1">{{ item.desc }}</div>
                </div>
            </div>
        </div>
    </div>
  </ReportPage>
</template>

<style scoped>
.animate-fade-in-down {
  animation: fadeInDown 0.8s ease-out forwards;
}

.animate-slide-in-right {
  animation: slideInRight 0.8s ease-out forwards;
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(30px); }
  to { opacity: 1; transform: translateX(0); }
}
</style>
