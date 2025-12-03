<template>
  <div 
    @click="onClick"
    :class="['bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm transition-all', clickable ? 'hover:shadow-md cursor-pointer group relative overflow-hidden' : '']"
  >
    <div class="flex justify-between items-start z-10 relative">
      <div>
        <div class="flex items-baseline gap-2">
          <slot name="value"></slot>
        </div>
        <p class="text-xs text-slate-400 mt-1">{{ label }}</p>
      </div>
      <div 
        :class="['p-2 rounded-lg transition-colors', clickable ? 'bg-primary-50 dark:bg-slate-700 group-hover:bg-primary-500 group-hover:text-white' : 'bg-primary-50 dark:bg-slate-700']"
      >
        <component 
          :is="icon" 
          :class="['w-5 h-5 text-primary-600 dark:text-primary-400', clickable ? 'group-hover:text-white' : '']" 
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue';

interface Props {
  label: string;
  icon: Component;
  clickable?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  clickable: false
});

const emit = defineEmits<{
  (e: 'click'): void
}>();

const onClick = () => {
  if (props.clickable) emit('click');
};
</script>