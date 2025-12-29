<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getAnnualReport } from '@/api/annualReport';
import type { AnnualReportData } from '@/types/annualReport';
import AnnualContainer from '@/components/annual-report/AnnualContainer.vue';
import SectionCover from '@/components/annual-report/SectionCover.vue';
import SectionPhotoWall from '@/components/annual-report/SectionPhotoWall.vue';
import SectionTime from '@/components/annual-report/SectionTime.vue';
import SectionAccount from '@/components/annual-report/SectionAccount.vue';
import SectionCategory from '@/components/annual-report/SectionCategory.vue';
import SectionHighlight from '@/components/annual-report/SectionHighlight.vue';
import SectionEmotion from '@/components/annual-report/SectionEmotion.vue';
import SectionLocation from '@/components/annual-report/SectionLocation.vue';
import SectionSeason from '@/components/annual-report/SectionSeason.vue';
import SectionEasterEgg from '@/components/annual-report/SectionEasterEgg.vue';
import SectionMessage from '@/components/annual-report/SectionMessage.vue';
import SectionEnd from '@/components/annual-report/SectionEnd.vue';
import { Loader2 } from 'lucide-vue-next';

const loading = ref(true);
const reportData = ref<AnnualReportData | null>(null);
const containerRef = ref<InstanceType<typeof AnnualContainer> | null>(null);

onMounted(async () => {
  try {
    reportData.value = await getAnnualReport();
  } catch (error) {
    console.error('Failed to load report data', error);
  } finally {
    loading.value = false;
  }
});

const handleReplay = () => {
  if (containerRef.value && containerRef.value.$el) {
    const scrollWrapper = containerRef.value.$el.querySelector('.scroll-wrapper');
    if (scrollWrapper) {
        scrollWrapper.scrollTo({ top: 0, behavior: 'smooth' });
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
        <!-- 1. Cover -->
        <SectionCover :user="reportData.user" :year="reportData.year" />

        <!-- 1. Photo Wall -->
        <SectionPhotoWall :year="reportData.year" />

        <!-- 2. Time -->
        <SectionTime :data="reportData.time" />

        <!-- 3. Account -->
        <SectionAccount :time="reportData.time" :emotion="reportData.emotion" />

        <!-- 4. Category -->
        <SectionCategory :data="reportData.memory" />

        <!-- 5. Highlight -->
        <SectionHighlight :memory="reportData.memory" />

        <!-- 6. Emotion -->
        <SectionEmotion :data="reportData.emotion" />

        <!-- 7. Location -->
        <SectionLocation :data="reportData.location" />

        <!-- 8. Season -->
        <SectionSeason :data="reportData.season" />
        
        <!-- 9. Easter Egg -->
        <SectionEasterEgg :data="reportData.easterEgg" />
        
        <!-- 10. Message -->
        <SectionMessage />
        
        <!-- 11. End -->
        <SectionEnd @replay="handleReplay" />
    </AnnualContainer>
    
    <!-- Error State -->
    <div v-else class="w-full h-full flex flex-col items-center justify-center">
        <p class="text-light-text3">时光数据加载失败，请刷新重试</p>
    </div>
  </div>
</template>
