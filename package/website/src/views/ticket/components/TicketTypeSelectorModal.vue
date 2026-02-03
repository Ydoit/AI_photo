<template>
  <Transition name="fade">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" @click="$emit('update:show', false)"></div>
      <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-sm relative z-10 p-6 flex flex-col gap-4">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-bold text-slate-800 dark:text-white">选择添加票据类型</h3>
          <button @click="$emit('update:show', false)" class="text-slate-400 hover:text-red-500 transition-colors">
            <X class="w-5 h-5" />
          </button>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <button @click="$emit('select-type', 'train')" class="flex flex-col items-center justify-center p-4 rounded-xl border-2 border-slate-100 dark:border-slate-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all gap-2 group">
            <TrainFront class="w-10 h-10 text-slate-400 group-hover:text-primary-500 transition-colors" />
            <span class="font-medium text-slate-600 dark:text-slate-300 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">火车票</span>
          </button>
          <button @click="$emit('select-type', 'flight')" class="flex flex-col items-center justify-center p-4 rounded-xl border-2 border-slate-100 dark:border-slate-700 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all gap-2 group">
            <Plane class="w-10 h-10 text-slate-400 group-hover:text-blue-500 transition-colors" />
            <span class="font-medium text-slate-600 dark:text-slate-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">飞机票</span>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { X, TrainFront, Plane } from 'lucide-vue-next';

defineProps<{
  show: boolean;
}>();

defineEmits<{
  (e: 'update:show', value: boolean): void;
  (e: 'select-type', type: 'train' | 'flight'): void;
}>();
</script>
