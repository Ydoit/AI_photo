<template>
  <div class="bg-white dark:bg-neutral-900 rounded-lg p-4 mx-4 my-3">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <div class="flex items-baseline gap-2">
        <span class="text-gray-600 dark:text-gray-300 text-sm">{{ selectedYear ? `在 ${selectedYear} 年` : '过去一年' }}共拍摄</span>
        <span class="text-xl font-bold text-gray-800 dark:text-gray-100">{{ data?.total_photos || 0 }}</span>
        <span class="text-gray-600 dark:text-gray-300 text-sm">张</span>
      </div>
      <div class="flex items-center gap-4 text-xs text-gray-500">
        <span class="hidden sm:inline">累计拍摄天数: {{ data?.total_days || 0 }}</span>
        <span class="hidden sm:inline">连续拍摄: {{ data?.max_consecutive_days || 0 }}</span>
        <el-select v-model="selectedYear" size="small" class="w-28" @change="fetchData" placeholder="过去一年">
          <el-option label="过去一年" :value="undefined" />
          <el-option v-for="year in availableYears" :key="year" :label="`${year}年`" :value="year" />
        </el-select>
      </div>
    </div>
    
    <div class="flex sm:hidden items-center gap-4 text-xs text-gray-500 mb-4">
      <span>累计拍摄天数: {{ data?.total_days || 0 }}</span>
      <span>连续拍摄: {{ data?.max_consecutive_days || 0 }}</span>
    </div>

    <!-- Heatmap Grid -->
    <div class="overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-200 dark:scrollbar-thumb-gray-700" ref="scrollContainer">
      <div class="flex flex-col gap-1" style="min-width: max-content;">
        <div class="flex gap-1">
          <div v-for="(col, colIndex) in gridColumns" :key="colIndex" class="flex flex-col gap-1">
             <div v-for="(day, rowIndex) in col" :key="`${colIndex}-${rowIndex}`" 
                  class="w-3 h-3 rounded-[2px]"
                  :class="getColorClass(day.count)"
                  :title="day.date ? `${day.date}: ${day.count}张` : ''">
             </div>
          </div>
        </div>
        <!-- Month labels -->
        <div class="mt-1 text-[10px] text-gray-400 relative h-4 w-full">
           <div v-for="label in monthLabels" :key="label.index"
                class="absolute"
                :style="{ left: `${label.index * 16}px` }">
             {{ label.text }}
           </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue';
import { dashboardApi, HeatmapResponse } from '@/api/dashboard';
import { format, subDays, startOfYear, endOfYear, eachDayOfInterval, getDay } from 'date-fns';
import { ElMessage } from 'element-plus';

const selectedYear = ref<number | undefined>(undefined);
const data = ref<HeatmapResponse | null>(null);
const availableYears = ref<number[]>([]);
const scrollContainer = ref<HTMLElement | null>(null);

const gridColumns = ref<{date: string, count: number}[][]>([]);
const monthLabels = ref<{text: string, index: number}[]>([]);

const getColorClass = (count: number) => {
  if (count === -1) return 'bg-transparent';
  if (count === 0) return 'bg-gray-100 dark:bg-gray-800';
  if (count < 5) return 'bg-[#9be9a8] dark:bg-[#0e4429]';
  if (count < 15) return 'bg-[#40c463] dark:bg-[#006d32]';
  if (count < 30) return 'bg-[#30a14e] dark:bg-[#26a641]';
  return 'bg-[#216e39] dark:bg-[#39d353]';
};

const buildGrid = (heatmapData: {date: string, count: number}[]) => {
  const dataMap = heatmapData.reduce((acc, item) => {
    acc[item.date] = item.count;
    return acc;
  }, {} as Record<string, number>);

  const today = new Date();
  let startDate: Date;
  let endDate: Date;

  if (selectedYear.value) {
    startDate = startOfYear(new Date(selectedYear.value, 0, 1));
    endDate = endOfYear(new Date(selectedYear.value, 0, 1));
    // Cap end date to today if it's the current year
    if (selectedYear.value === today.getFullYear()) {
        endDate = today;
    }
  } else {
    endDate = today;
    startDate = subDays(today, 364);
  }

  const days = eachDayOfInterval({ start: startDate, end: endDate });
  const firstDayOfWeek = getDay(startDate);
  
  const paddedDays: (Date | null)[] = Array(firstDayOfWeek).fill(null).concat(days);
  
  const columns = [];
  const labels: {text: string, index: number}[] = [];
  let currentMonth = -1;

  for (let i = 0; i < paddedDays.length; i += 7) {
    const colDays = paddedDays.slice(i, i + 7);
    // Pad end if necessary
    while (colDays.length < 7) {
      colDays.push(null);
    }
    
    columns.push(colDays.map(date => {
      if (!date) return { date: '', count: -1 };
      const dateStr = format(date, 'yyyy-MM-dd');
      return {
        date: dateStr,
        count: dataMap[dateStr] || 0
      };
    }));

    // Find the first valid day in this column to determine month
    const firstValidDay = colDays.find(d => d !== null);
    if (firstValidDay) {
      const month = firstValidDay.getMonth();
      if (month !== currentMonth) {
        labels.push({ text: `${month + 1}月`, index: columns.length - 1 });
        currentMonth = month;
      }
    }
  }
  
  gridColumns.value = columns;
  monthLabels.value = labels;
  
  // Scroll to end (right) when showing past year or current year
  if (!selectedYear.value || selectedYear.value === today.getFullYear()) {
    nextTick(() => {
      if (scrollContainer.value) {
        scrollContainer.value.scrollLeft = scrollContainer.value.scrollWidth;
      }
    });
  }
};

const fetchData = async () => {
  try {
    const res = await dashboardApi.getHeatmap(selectedYear.value || undefined);
    data.value = res;
    if (res.available_years) {
      availableYears.value = res.available_years;
    }
    buildGrid(res.data);
  } catch (error) {
    console.error('Failed to fetch heatmap data:', error);
    ElMessage.error('加载拍摄情况失败');
  }
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
/* Tooltip styling if needed, but native title is usually fine for simple cases */
</style>
