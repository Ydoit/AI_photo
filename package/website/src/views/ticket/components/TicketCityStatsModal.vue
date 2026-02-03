<template>
  <Transition name="fade">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" @click="$emit('update:show', false)"></div>
      <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-lg relative z-10 p-6">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <MapPin class="w-5 h-5 text-primary-600 dark:text-primary-400" />
            足迹地图
          </h2>
          <button @click="$emit('update:show', false)"><X class="w-5 h-5 text-slate-400" /></button>
        </div>
        
        <div class="flex flex-wrap gap-2 max-h-[60vh] overflow-y-auto">
          <span 
            v-for="city in uniqueCities" 
            :key="city"
            @click="$emit('filter-by-city', city)"
            class="px-3 py-1.5 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-full text-sm hover:bg-primary-50 hover:text-primary-600 hover:border-primary-200 dark:hover:bg-slate-600 dark:hover:text-primary-400 border border-transparent cursor-pointer transition-colors"
          >
            {{ city }}
          </span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { X, MapPin } from 'lucide-vue-next';

defineProps<{
  show: boolean;
  uniqueCities: string[];
}>();

defineEmits<{
  (e: 'update:show', value: boolean): void;
  (e: 'filter-by-city', city: string): void;
}>();
</script>
