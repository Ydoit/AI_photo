<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getReportEasterEgg, getReportSummary ,getReportMemory, getReportLocation, getReportSeason, getReportEmotion, getReportExpenses, getReportTransportAnalysis } from '@/api/annualReport';
import type { AnnualReportData } from '@/types/annualReport';
import AnnualContainer from '@/components/annual-report/AnnualContainer.vue';
import SectionCover from '@/components/annual-report/SectionCover.vue';
import SectionPhotoWall from '@/components/annual-report/SectionPhotoWall.vue';
import SectionTime from '@/components/annual-report/SectionTime.vue';
import SectionAccount from '@/components/annual-report/SectionAccount.vue';
import SectionExpense from '@/components/annual-report/SectionExpense.vue';
import SectionTransportAnalysis from '@/components/annual-report/SectionTransportAnalysis.vue';
import SectionCategory from '@/components/annual-report/SectionCategory.vue';
import SectionHighlight from '@/components/annual-report/SectionHighlight.vue';
import SectionEmotion from '@/components/annual-report/SectionEmotion.vue';
import SectionLocation from '@/components/annual-report/SectionLocation.vue';
import SectionFarthestCity from '@/components/annual-report/SectionFarthestCity.vue';

import SectionSeason from '@/components/annual-report/SectionSeason.vue';
import SectionEasterEgg from '@/components/annual-report/SectionEasterEgg.vue';
import SectionMessage from '@/components/annual-report/SectionMessage.vue';
import SectionEnd from '@/components/annual-report/SectionEnd.vue';
import { Loader2 } from 'lucide-vue-next';

const loading = ref(true);
const reportData = ref<AnnualReportData>({} as AnnualReportData);
const containerRef = ref<InstanceType<typeof AnnualContainer> | null>(null);
let startTime = '2025-01-01 00:00:00';
let endTime = '2025-12-31 23:59:59';
onMounted(async () => {
  try {

    const data = await getReportSummary(startTime, endTime);
    reportData.value.user = data.user;
    reportData.value.time = data.time;
    const memoryData = await getReportMemory(startTime, endTime);
    reportData.value.memory = memoryData;
    const locationData = await getReportLocation(startTime, endTime);
    reportData.value.location = locationData;
    const seasonData = await getReportSeason(startTime, endTime);
    reportData.value.season = seasonData;
    const emotionData = await getReportEmotion(startTime, endTime);
    reportData.value.emotion = emotionData;
    const easterEggData = await getReportEasterEgg(startTime, endTime);
    reportData.value.easterEgg = easterEggData;
    const expenseData = await getReportExpenses(startTime, endTime);
    reportData.value.expense = expenseData;
    const transportAnalysisData = await getReportTransportAnalysis(startTime, endTime);
    reportData.value.transportAnalysis = transportAnalysisData;
  } catch (error) {
    console.error('Failed to load report data', error);
  } finally {
    loading.value = false;
  }
});

let isScrolling = false
let scrollAnimationFrame: number | null = null // 手动滚动的动画帧
/**
 * 手动实现平滑滚动（替代原生smooth，稳定无冲突）
 * @param {HTMLElement} el 滚动容器
 * @param {number} targetTop 目标位置
 * @param {number} duration 动画时长（ms）
 */
const smoothScrollTo = (el: HTMLElement, targetTop: number, duration = 400) => {
  // 取消上一次未完成的动画
  if (scrollAnimationFrame) cancelAnimationFrame(scrollAnimationFrame)
  
  const startTop = el.scrollTop
  const distance = targetTop - startTop
  const startTime = performance.now()

  // 缓动函数：ease-out（先快后慢，贴近原生滑动手感）
  const easeOut = (t: number, b: number, c: number, d: number) => {
    t /= d
    t--
    return c * (t * t * t + 1) + b
  }

  const animate = (currentTime: number) => {
    const elapsed = currentTime - startTime
    if (elapsed < duration) {
      el.scrollTop = easeOut(elapsed, startTop, distance, duration)
      scrollAnimationFrame = requestAnimationFrame(animate)
    } else {
      el.scrollTop = targetTop // 动画结束精准定位
      scrollAnimationFrame = null
      isScrolling = false
    }
  }

  scrollAnimationFrame = requestAnimationFrame(animate)
}

const handleReplay = () => {
  if (containerRef.value && containerRef.value.$el) {
    const scrollWrapper = containerRef.value.$el.querySelector('.scroll-wrapper');
    if (scrollWrapper) {
        smoothScrollTo(scrollWrapper, 0, 1200);
        // scrollWrapper.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }
};
</script>

<template>
  <div class="w-full h-screen bg-bg-light dark:bg-dark-navy">
    <!-- Loading State -->
    <div v-if="loading" class="w-full h-full flex flex-col items-center justify-center">
        <Loader2 class="w-10 h-10 text-primary-amber animate-spin mb-4" />
        <p class="text-light-text3 dark:text-gray-400">正在开启时光信笺...</p>
    </div>

    <!-- Report Content -->
    <AnnualContainer v-else-if="reportData" ref="containerRef">
        <!-- 0. Cover -->
        <SectionCover :user="reportData.user" :year="reportData.year" />

        <!-- 1. Photo Wall -->
        <SectionPhotoWall :startTime="startTime" :endTime="endTime" />

        <!-- 2. Time -->
        <SectionTime :data="reportData.time" />

        <!-- 3. Highlight -->
        <SectionHighlight :memory="reportData.memory" />

        <!-- 4. Account -->
        <SectionAccount :time="reportData.time" :emotion="reportData.emotion" />

        <!-- 5. Category -->
        <SectionCategory :data="reportData.memory" />

        <!-- 6. Emotion -->
        <SectionEmotion :data="reportData.emotion" />

        <!-- 7. Location -->
        <SectionLocation :data="reportData.location" />

        <!-- 8. Farthest City -->
        <SectionFarthestCity :data="reportData.location" />

        <!-- 9. Season -->
        <SectionSeason :data="reportData.season" />

        <!-- 11 Expense -->
        <SectionExpense v-if="reportData.expense" :data="reportData.expense" :startTime="startTime" :endTime="endTime" />

        <!-- 12 Transport Analysis (Merged Behavior & Comprehensive) -->
        <SectionTransportAnalysis v-if="reportData.transportAnalysis" :data="reportData.transportAnalysis" />

        <!-- 13. Message -->
        <SectionMessage />

        <!-- 10. Easter Egg -->
        <SectionEasterEgg v-if="reportData.easterEgg" :data="reportData.easterEgg" />

        <!-- 14. End -->
        <SectionEnd @replay="handleReplay" />
    </AnnualContainer>

    <!-- Error State -->
    <div v-else class="w-full h-full flex flex-col items-center justify-center">
        <p class="text-light-text3">时光数据加载失败，请刷新重试</p>
    </div>
  </div>
</template>
