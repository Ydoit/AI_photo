<template>
  <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4 mb-6 flex flex-wrap gap-4 justify-between items-center shadow-sm transition-colors">
    <div class="flex items-center gap-3 w-full sm:w-auto">
      <div class="relative w-full sm:w-40">
        <select
          :value="filterType"
          @change="$emit('update:filterType', ($event.target as HTMLSelectElement).value)"
          class="w-full appearance-none bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-sm rounded-md px-3 py-2 pr-8 focus:border-primary-500 dark:text-white outline-none cursor-pointer"
        >
          <option value="all">全部车票</option>
          <option value="flight">飞机票</option>
          <option value="highspeed">高铁/动车</option>
          <option value="normal">普速列车</option>
        </select>
        <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
      </div>

      <div class="hidden sm:flex bg-slate-100 dark:bg-slate-700 rounded-md p-1 flex-wrap gap-1">
        <button 
          v-for="type in sortOptions"
          :key="type.value"
          @click="$emit('change-sort-type', type.value)"
          :class="['px-3 py-1 text-xs font-medium rounded transition-all dark:bg-gray-800', sortType === type.value ? 'bg-white dark:bg-slate-600 text-primary-600 dark:text-primary-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-100']"
        >
          {{ type.label }}
        </button>
      </div>
    </div>

    <div class="flex items-center gap-3 w-full sm:w-auto justify-end">
      <div class="bg-slate-100 dark:bg-slate-700 p-1 rounded-md flex gap-1">
        <button 
          @click="$emit('fetch-tickets')"
          class="p-1.5 rounded transition-all text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-white dark:hover:bg-slate-600 hover:shadow-sm dark:bg-gray-800"
          title="刷新数据"
          :disabled="loading"
        >
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
        </button>
        <div class="w-px bg-slate-300 dark:bg-slate-600 my-1 mx-0.5"></div>
        <button 
          @click="$emit('update:viewMode', 'timeline')"
          :class="['p-1.5 rounded transition-all dark:bg-gray-800', viewMode === 'timeline' ? 'bg-white dark:bg-slate-600 shadow-sm text-primary-600 dark:text-primary-400' : 'text-slate-500 hover:text-slate-600 dark:hover:text-slate-300']"
          title="时间轴视图"
        >
          <ListTree class="w-4 h-4" />
        </button>
        <button 
          @click="$emit('update:viewMode', 'grid')"
          :class="['p-1.5 rounded transition-all dark:bg-gray-800', viewMode === 'grid' ? 'bg-white dark:bg-slate-600 shadow-sm text-primary-600 dark:text-primary-400' : 'text-slate-500 hover:text-slate-600 dark:hover:text-slate-300']"
          title="卡片视图"
        >
          <LayoutGrid class="w-4 h-4" />
        </button>
      </div>

      <div class="h-6 w-px bg-slate-200 dark:bg-slate-700 mx-1 hidden sm:block"></div>

      <div class="flex items-center gap-2 px-2">
        <el-checkbox 
          :model-value="isAllSelected"
          :indeterminate="isIndeterminate"
          @change="$emit('toggle-select-all', $event)"
        >
          <span class="text-sm text-slate-600 dark:text-slate-400">全选</span>
        </el-checkbox>
      </div>

      <button 
        :disabled="selectedTickets.length === 0 || loading"
        @click="$emit('batch-delete')"
        :class="['flex items-center gap-2 text-sm px-4 py-2 rounded-md transition-colors', selectedTickets.length > 0 ? 'text-red-600 bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50' : 'text-slate-300 dark:text-slate-400 bg-slate-50 dark:bg-slate-700 cursor-not-allowed']"
      >
        <Trash2 class="w-4 h-4" />
        <span class="hidden sm:inline">删除选中</span>
        <span v-if="selectedTickets.length > 0">({{ selectedTickets.length }})</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ChevronDown, RefreshCw, ListTree, LayoutGrid, Trash2 } from 'lucide-vue-next';
import type { SortType } from '@/types/ticket';

defineProps<{
  filterType: string;
  sortType: string;
  viewMode: string;
  isAllSelected: boolean;
  isIndeterminate: boolean;
  loading: boolean;
  selectedTickets: (number | string)[];
  sortOptions: { label: string; value: SortType }[];
}>();

defineEmits<{
  (e: 'update:filterType', value: string): void;
  (e: 'update:viewMode', value: string): void;
  (e: 'change-sort-type', value: SortType): void;
  (e: 'fetch-tickets'): void;
  (e: 'toggle-select-all', value: boolean | string | number): void;
  (e: 'batch-delete'): void;
}>();
</script>
