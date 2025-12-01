<!-- src/views/NotFound.vue -->
<template>
  <div class="not-found flex flex-col items-center justify-center h-full p-4">
    <h1 class="text-6xl font-bold text-slate-400 mb-4">404</h1>
    <p class="text-slate-500 dark:text-slate-400 mb-6">页面未找到</p>
    <router-link to="/" class="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors">
      返回首页
    </router-link>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.not-found {
  min-height: calc(100vh - 100px);
}
</style>