<!-- src/layouts/MainLayout.vue -->
<template>
  <div 
    :class="[isDarkMode ? 'dark' : '']" 
    :style="themeStyle"
    class="h-screen font-sans transition-colors duration-300 bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-200"
  >
    <!-- 顶部导航（原 App.vue 中的 NavBar） -->
    <NavBar />
    <div class="w-full bg-slate-50 dark:bg-gray-900 pt-14 box-border dark:from-gray-900 dark:to-gray-800">
      <!-- 页面内容挂载点：所有子页面渲染在这里 -->
      <transition name="fade-slide" mode="out-in">
        <router-view />
      </transition>
    </div>

    <!-- 悬浮的 Agent 助手按钮 -->
    <button 
      v-show="!isAgentOpen && $route.name !== 'Login'" 
      @click="isAgentOpen = true"
      class="fixed bottom-6 right-6 sm:bottom-8 sm:right-8 z-50 w-14 h-14 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-lg shadow-indigo-500/30 flex items-center justify-center transition-transform hover:scale-110 active:scale-95 group"
    >
      <Bot class="w-6 h-6 group-hover:animate-bounce" />
    </button>

    <!-- Agent 聊天弹窗 -->
    <AgentChat v-model="isAgentOpen" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
// 导入导航栏、页脚组件
import NavBar from '@/layouts/NavBar.vue';
import Footer from '@/layouts/Footer.vue';
import AgentChat from '@/components/AgentChat.vue';
import { Bot } from 'lucide-vue-next';
// 导入主题逻辑（保持原有的主题功能）
import { provideTheme } from '@/composables/useTheme';

const isAgentOpen = ref(false);

// 提供主题状态（供子组件（如 NavBar）注入使用）
const {
  isDarkMode,
  currentTheme,
  themeStyle,
  themeColors,
  setMode,
  setTheme
} = provideTheme();
</script>

<style scoped>

/* 页面过渡动画（原 App.vue 中的样式） */
.fade-slide-enter-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.fade-slide-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>