
<template>
  <ReportPage>
    <div class="flex flex-col items-center justify-center h-full text-center px-4">
      
      <!-- Big Number -->
      <div class="relative">
         <h2 class="text-[clamp(4rem,15vw,7rem)] font-bold text-primary-amber leading-none tracking-tight tabular-nums">
            {{ displayValue.toLocaleString() }}
         </h2>
         <div class="absolute -bottom-4 left-0 right-0 h-1 bg-primary-amber/20 rounded-full"></div>
      </div>

      <!-- Annotation -->
      <div class="mt-12 space-y-4 max-w-md mx-auto animate-fade-in-up">
        <p class="text-xl md:text-2xl text-light-text2 dark:text-gray-200 leading-relaxed">
            这一年，你用镜头收藏了 <br>
            <span class="text-primary-amber font-bold">{{ data.totalPhotos }}</span> 个珍贵瞬间
        </p>
        
        <p class="text-sm text-light-text3 dark:text-gray-400 mt-8">
            我们陪你走过了 {{ data.accompanyDays }} 天<br>
            步履不停，时光不散
        </p>
      </div>
      
    </div>
  </ReportPage>
</template>

<script setup lang="ts">
import ReportPage from './ReportPage.vue';
import type { TimeMetrics } from '@/types/annualReport';
import { ref, onMounted, watch } from 'vue';

const props = defineProps<{
  data: TimeMetrics;
}>();

// CountUp Logic
const displayValue = ref(0);

const startCountUp = () => {
  const start = 0;
  const end = props.data.totalPhotos;
  const duration = 2000; // 2 seconds
  const startTime = performance.now();

  const animate = (currentTime: number) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // EaseOutExpo function
    const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
    
    displayValue.value = Math.floor(start + (end - start) * easeProgress);

    if (progress < 1) {
      requestAnimationFrame(animate);
    }
  };

  requestAnimationFrame(animate);
};

onMounted(() => {
    // Small delay to start animation after slide transition
    setTimeout(() => {
        startCountUp();
    }, 500);
});
</script>

<style scoped>
.animate-fade-in-up {
  opacity: 0;
  animation: fadeInUp 1s ease-out forwards;
  animation-delay: 1s;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
