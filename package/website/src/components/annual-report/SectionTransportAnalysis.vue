<template>
  <ReportPage :class="{ 'animate-in': isActive }" ref="sectionRef">
    <div class="flex flex-col items-center justify-center h-full text-center px-4 py-8 overflow-y-auto custom-scrollbar">
      
      <!-- Header -->
      <div class="mb-8 shrink-0">
         <h2 class="text-3xl font-bold text-primary-amber mb-2">交通出行年度分析</h2>
         <div class="h-1 w-20 bg-primary-amber/20 rounded-full mx-auto"></div>
         <p class="text-xs text-light-text3 dark:text-gray-400 mt-2">基于 2025 年车票数据的深度洞察</p>
      </div>

      <!-- Key Metrics -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl mx-auto mb-8 animate-fade-in-up">
        <!-- 2025 Total Mileage -->
        <div class="bg-white/50 dark:bg-black/20 rounded-xl p-4 backdrop-blur-sm">
           <p class="text-sm text-light-text3 dark:text-gray-400 mb-1">年度总里程</p>
           <p class="text-2xl font-bold text-primary-amber">
             {{ totalMileage2025.toLocaleString() }} <span class="text-sm font-normal text-gray-500">km</span>
           </p>
        </div>
        <!-- Max Frequency Month -->
        <div class="bg-white/50 dark:bg-black/20 rounded-xl p-4 backdrop-blur-sm">
           <p class="text-sm text-light-text3 dark:text-gray-400 mb-1">出行高峰月份</p>
           <div v-if="maxFreqMonth">
             <p class="text-2xl font-bold text-primary-amber inline-block mr-2">{{ maxFreqMonth.month }}月</p>
             <span class="text-xs text-gray-500">累计出行 <span class="text-primary-amber font-bold">{{ maxFreqMonth.count }}</span> 次</span>
           </div>
           <div v-else>
             <p class="text-lg text-gray-400">暂无数据</p>
           </div>
        </div>
      </div>

      <!-- Analysis Text -->
      <div class="w-full max-w-4xl mx-auto mb-6 animate-fade-in-up" style="animation-delay: 0.2s;">
        <div class="bg-white/50 dark:bg-black/20 rounded-xl p-4 backdrop-blur-sm text-left">
          <h3 class="text-sm font-bold text-light-text2 dark:text-gray-200 mb-2">出行时段分析</h3>
          <p class="text-sm text-light-text1 dark:text-gray-300 leading-relaxed">
            {{ timeDistributionText }}
          </p>
        </div>
      </div>

      <!-- Top Lists -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl mx-auto mb-8 animate-fade-in-up" style="animation-delay: 0.4s;">
        <!-- Top Routes -->
        <div class="bg-white/50 dark:bg-black/20 rounded-xl p-4 backdrop-blur-sm text-left">
          <h3 class="text-sm font-bold text-light-text2 dark:text-gray-200 mb-3">常用路线 TOP5</h3>
          <div class="flex flex-col gap-2">
            <div v-for="(r, idx) in data.behavior.topRoutes" :key="idx" class="flex items-center justify-between hover:bg-black/5 p-2 rounded transition-colors">
              <span class="text-sm text-light-text1 dark:text-gray-200">{{ r.route }}</span>
              <span class="text-xs text-primary-amber font-bold">{{ r.count }} 次</span>
            </div>
            <div v-if="!data.behavior.topRoutes?.length" class="text-xs text-gray-500 text-center py-4">暂无数据</div>
          </div>
        </div>

        <!-- Top Destinations -->
        <div class="bg-white/50 dark:bg-black/20 rounded-xl p-4 backdrop-blur-sm text-left">
          <h3 class="text-sm font-bold text-light-text2 dark:text-gray-200 mb-3">热门目的地 TOP5</h3>
          <div class="flex flex-col gap-2">
            <div v-for="(d, idx) in data.behavior.topDestinations" :key="idx" class="flex items-center justify-between hover:bg-black/5 p-2 rounded transition-colors">
              <span class="text-sm text-light-text1 dark:text-gray-200">{{ d.city }}</span>
              <span class="text-xs text-primary-amber font-bold">{{ d.count }} 次</span>
            </div>
            <div v-if="!data.behavior.topDestinations?.length" class="text-xs text-gray-500 text-center py-4">暂无数据</div>
          </div>
        </div>
      </div>

      <!-- Footer Note -->
      <p class="text-xs text-light-text3 dark:text-gray-500 mt-auto animate-fade-in-up shrink-0" style="animation-delay: 0.6s;">
          数据来源：车票收藏夹 | 统计时间：{{ new Date().toLocaleDateString() }}
      </p>

    </div>
  </ReportPage>
</template>

<script setup lang="ts">
import ReportPage from './ReportPage.vue';
import type { TransportAnalysisMetrics } from '@/types/annualReport';
import { computed, onMounted, ref } from 'vue';
import { useTicketStore } from '@/stores/ticketStore';
import { storeToRefs } from 'pinia';
import { useIntersectionObserver } from '@vueuse/core';

const props = defineProps<{
  data: TransportAnalysisMetrics;
}>();

const sectionRef = ref<HTMLElement | null>(null);
const isActive = ref(false);

useIntersectionObserver(
  sectionRef,
  ([{ isIntersecting }]) => {
    if (isIntersecting) {
      isActive.value = true;
    }
  },
  { threshold: 0.3 }
);

// --- 1. Data Fetching (2025 Ticket Data) ---
const ticketStore = useTicketStore();
const { tickets, statsMap } = storeToRefs(ticketStore);

onMounted(() => {
  if (tickets.value.length === 0) {
    ticketStore.fetchTickets();
  }
});

const tickets2025 = computed(() => {
  return tickets.value.filter(t => {
    const dateStr = t.date_time || '';
    return dateStr.startsWith('2025');
  });
});

// --- 2. Calculate Total Mileage for 2025 ---
const totalMileage2025 = computed(() => {
  let distance = 0;
  tickets2025.value.forEach(t => {
    if (t.id && statsMap.value && statsMap.value[t.id]) {
      distance += statsMap.value[t.id].distance_km;
    } else {
      const n = Number((t as any).total_mileage);
      if (isFinite(n) && !isNaN(n) && n > 0 && n < 1000000) {
        distance += n;
      }
    }
  });
  return Math.round(distance);
});

// --- 3. Max Frequency Month ---
const maxFreqMonth = computed(() => {
  const counts = Array(12).fill(0);
  tickets2025.value.forEach(t => {
    const dateStr = t.date_time || '';
    // Format: "YYYY-MM-DD ..."
    const monthPart = dateStr.slice(5, 7);
    const m = parseInt(monthPart, 10);
    if (m >= 1 && m <= 12) {
      counts[m - 1]++;
    }
  });

  let maxCount = -1;
  let maxIdx = -1;
  counts.forEach((c, i) => {
    if (c > maxCount) {
      maxCount = c;
      maxIdx = i;
    }
  });

  if (maxCount > 0) {
    return { month: maxIdx + 1, count: maxCount };
  }
  return null;
});

// --- 4. Travel Time Analysis (Text Description) ---
const timeDistributionText = computed(() => {
  if (tickets2025.value.length === 0) return '暂无 2025 年出行数据。';

  let workday = 0;
  let weekend = 0;
  // Simple heuristic: check day of week
  // Note: Holiday handling requires complex calendar logic, here we simplify to Workday/Weekend
  // or use the 'tripTypeDistribution' logic if it was available per ticket.
  // Since we don't have a calendar library here, we'll stick to Day of Week.
  
  tickets2025.value.forEach(t => {
    const dateStr = (t.date_time || '').split(' ')[0];
    if (dateStr) {
      const d = new Date(dateStr);
      const day = d.getDay(); // 0 = Sunday, 6 = Saturday
      if (day === 0 || day === 6) {
        weekend++;
      } else {
        workday++;
      }
    }
  });

  const total = workday + weekend;
  if (total === 0) return '暂无数据';

  const workPct = Math.round((workday / total) * 100);
  const weekPct = Math.round((weekend / total) * 100);

  let mainType = '';
  let mainPct = 0;
  
  if (workday >= weekend) {
    mainType = '工作日';
    mainPct = workPct;
  } else {
    mainType = '周末';
    mainPct = weekPct;
  }

  // Generate text
  // "主要集中在[工作日/周末]出行，占比达 X%。"
  // "Travel is mainly concentrated on [Workday/Weekend], accounting for X%."
  return `2025 年您的出行主要集中在${mainType}，占比达 ${mainPct}%。${
    mainType === '工作日' 
      ? '这表明您的出行可能以商务差旅或日常通勤为主。' 
      : '这表明您倾向于利用闲暇时间进行休闲出游。'
  }`;
});

</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5);
  border-radius: 20px;
}
</style>
