<template>
  <div class="grid grid-cols-2 gap-3 px-4 pb-20">
    <!-- Toolbox Link (Replacing Low Score Cleanup) or just remove it? -->
    <!-- The requirement is to move it to Toolbox page. So I remove it here. -->
    
    <!-- Clean Duplicates -->
    <div 
      class="bg-gray-100 dark:bg-neutral-800 rounded-lg p-3 h-[60px] flex items-center justify-between cursor-pointer hover:bg-gray-200 dark:hover:bg-neutral-700 transition-colors"
      @click="$router.push('/tools/clean')"
    >
      <div class="flex flex-col">
        <div class="flex items-center space-x-1 mb-1">
          <span class="text-orange-500">🧹</span>
          <span class="text-xs font-bold text-gray-800 dark:text-gray-100">清理重复</span>
        </div>
        <span class="text-[10px] text-gray-500">89张</span>
      </div>
      <button class="bg-orange-500 text-white text-[10px] px-2 py-1 rounded">一键清理</button>
    </div>
  </div>
</template>
