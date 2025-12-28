<template>
  <ReportPage>
    <div class="flex flex-col w-full">
        <!-- Title -->
        <div class="text-center mb-2">
            <h2 class="text-2xl font-bold text-light-text1 dark:text-white">你的年度生活图谱</h2>
            <p class="text-sm text-light-text3 dark:text-gray-400 mt-2">镜头里的世界，藏着你的热爱</p>
        </div>

        <!-- Chart -->
        <div ref="chartRef" class="w-full h-[250px] md:h-[350px]"></div>

        <!-- Top List -->
        <div class="flex flex-col gap-3 mt-0">
            <div
                v-for="(cat, index) in topCategories"
                :key="cat.name"
                class="flex items-center justify-between bg-white/50 dark:bg-white/5 p-3 rounded-xl backdrop-blur-sm"
            >
                <div class="flex items-center gap-3">
                    <div class="w-3 h-3 rounded-full" :style="{ backgroundColor: ['#F97316', '#FBBF24', '#EC4899'][index] || '#ccc' }"></div>
                    <span class="font-medium text-light-text1 dark:text-gray-200">{{ cat.name }}</span>
                </div>
                <span class="text-primary-amber font-bold">{{ cat.value }}%</span>
            </div>
        </div>
    </div>
  </ReportPage>
</template>


<script setup lang="ts">
import ReportPage from './ReportPage.vue';
import type { MemoryMetrics } from '@/types/annualReport';
import { onMounted, ref, watch } from 'vue';
import * as echarts from 'echarts';

const props = defineProps<{
  data: MemoryMetrics;
}>();

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

const initChart = () => {
  if (!chartRef.value) return;
  chartInstance = echarts.init(chartRef.value);

  const option = {
    series: [
      {
        type: 'pie',
        radius: ['50%', '70%'],
        center: ['50%', '40%'],
        data: props.data.categoryDistribution,
        color: ['#F97316', '#FBBF24', '#EC4899', '#8B5CF6', '#10B981'],
        label: { show: false },
        emphasis: {
            itemStyle: {
                scale: true,
                scaleSize: 10,
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
            } 
        }
      }
    ],
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}%' // Assuming value is percentage or count
    }
  };
  
  chartInstance.setOption(option);
};

onMounted(() => {
    // Delay init to ensure transition is done or use IntersectionObserver
    setTimeout(initChart, 500);
    window.addEventListener('resize', () => chartInstance?.resize());
});

// Top 3 Categories
const topCategories = computed(() => {
    return [...props.data.categoryDistribution]
        .sort((a, b) => b.value - a.value)
        .slice(0, 3);
});

import { computed } from 'vue';
</script>