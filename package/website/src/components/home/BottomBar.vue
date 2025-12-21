<template>
  <div class="fixed bottom-0 left-0 right-0 h-12 bg-white dark:bg-neutral-900 border-t border-gray-200 dark:border-gray-800 flex items-center justify-between px-4 z-10">
    <button 
      class="text-sm text-blue-500 hover:text-blue-600 transition-colors"
      @click="$emit('customize')"
    >
      自定义展示
    </button>
    <button 
      class="text-gray-600 dark:text-gray-400 hover:text-blue-500 transition-colors flex items-center"
      @click="$emit('refresh')"
    >
      <i class="mgc_refresh_3_line text-xl" :class="{ 'animate-spin': loading }"></i>
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps({
  loading: Boolean
});

defineEmits(['customize', 'refresh']);
</script>
