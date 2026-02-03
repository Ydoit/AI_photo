<template>
  <aside class="w-full xl:w-[320px] shrink-0 space-y-4">
    <div class="lg:hidden mb-4">
      <input
        :value="searchQuery"
        @input="handleSearchInput"
        type="text"
        placeholder="搜索车票 / 乘车人..."
        class="w-full px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white"
      />
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 xl:grid-cols-1 gap-4">
      <StatsCard 
        label="点击查看足迹地图" 
        :icon="MapPin" 
        clickable 
        @click="$emit('show-city-modal')"
      >
        <template #value>
          <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ uniqueCities.length }}</span>
          <span class="text-xs text-slate-500 dark:text-slate-400">座城市</span>
        </template>
      </StatsCard>

      <StatsCard label="总时长" :icon="Clock">
        <template #value>
          <div v-if="loading && tickets.length > 0 && !statsMap" class="flex items-center gap-2">
            <div class="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
            <span class="text-sm text-slate-400">计算中...</span>
          </div>
          <div v-else>
            <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ totalDuration.hours }}<span class="text-sm font-normal text-slate-500 ml-0.5">小时</span></span>
            <span class="text-lg font-semibold text-slate-600 dark:text-slate-300">{{ totalDuration.minutes }}<span class="text-xs font-normal text-slate-500 ml-0.5">分钟</span></span>
          </div>
        </template>
      </StatsCard>

      <StatsCard label="总里程" :icon="Route">
        <template #value>
          <div v-if="loading && tickets.length > 0 && !statsMap" class="flex items-center gap-2">
            <div class="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
            <span class="text-sm text-slate-400">计算中...</span>
          </div>
          <div v-else>
            <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ totalDistance.toLocaleString() }}</span>
            <span class="text-xs text-slate-500 dark:text-slate-400">km</span>
          </div>
        </template>
      </StatsCard>
    </div>

    <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm">
      <h3 class="text-sm font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
        <User class="w-4 h-4 text-primary-600 dark:text-primary-400" />
        乘车人筛选
      </h3>
      <div class="flex flex-wrap gap-2 max-h-[200px] overflow-y-auto">
        <span 
          v-for="passenger in uniquePassengers" 
          :key="passenger"
          @click="$emit('filter-by-passenger', passenger)"
          class="px-3 py-1.5 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-full text-sm hover:bg-primary-50 hover:text-primary-600 hover:border-primary-200 dark:hover:bg-slate-600 dark:hover:text-primary-400 border border-transparent cursor-pointer transition-colors"
          :class="selectedPassenger === passenger ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400' : ''"
        >
          {{ passenger }}
        </span>
        <span 
          @click="$emit('clear-passenger-filter')"
          class="px-3 py-1.5 bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded-full text-sm hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-600 cursor-pointer transition-colors"
        >
          全部
        </span>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { MapPin, Clock, Route, User } from 'lucide-vue-next';
import StatsCard from '@/components/StatsCard.vue';

defineProps<{
  searchQuery: string;
  uniqueCities: string[];
  totalDuration: { hours: number; minutes: number };
  totalDistance: number;
  uniquePassengers: string[];
  selectedPassenger: string;
  loading: boolean;
  tickets: any[];
  statsMap: any;
}>();

const emit = defineEmits<{
  (e: 'update:searchQuery', value: string): void;
  (e: 'show-city-modal'): void;
  (e: 'filter-by-passenger', passenger: string): void;
  (e: 'clear-passenger-filter'): void;
}>();

const handleSearchInput = (event: Event) => {
  const target = event.target as HTMLInputElement;
  emit('update:searchQuery', target.value);
};
</script>
