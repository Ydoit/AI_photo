<!-- src/views/AboutPage.vue -->
<template>
  <div class="about-page max-w-4xl mx-auto p-6 space-y-12">
    <!-- 项目介绍 -->
    <section class="space-y-4">
      <h1 class="text-4xl font-bold text-slate-800 dark:text-slate-100">关于拾光物语 (TrailSnap)</h1>
      <p class="text-lg text-slate-600 dark:text-slate-300">
        拾光物语是一个基于 Vue 3 + TypeScript 开发的现代化 Web 应用，旨在记录和管理个人的出行轨迹与车票信息。
      </p>
    </section>

    <!-- 项目背景与愿景 -->
    <section class="space-y-4">
      <h2 class="text-2xl font-bold text-slate-800 dark:text-slate-100">项目背景</h2>
      <p class="text-slate-600 dark:text-slate-300">
        在快节奏的现代生活中，我们常常忘记记录那些珍贵的出行瞬间。拾光物语致力于帮助用户轻松记录、整理和回顾自己的出行经历，
        让每一段旅程都成为值得珍藏的记忆。
      </p>
    </section>

    <!-- 技术栈 -->
    <section class="space-y-4">
      <h2 class="text-2xl font-bold text-slate-800 dark:text-slate-100">技术栈</h2>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div class="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
          <h3 class="font-semibold text-slate-700 dark:text-slate-300">前端框架</h3>
          <p class="text-slate-500 dark:text-slate-400">Vue 3 + TypeScript</p>
        </div>
        <div class="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
          <h3 class="font-semibold text-slate-700 dark:text-slate-300">路由管理</h3>
          <p class="text-slate-500 dark:text-slate-400">Vue Router</p>
        </div>
        <div class="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
          <h3 class="font-semibold text-slate-700 dark:text-slate-300">UI组件库</h3>
          <p class="text-slate-500 dark:text-slate-400">Element Plus</p>
        </div>
        <div class="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
          <h3 class="font-semibold text-slate-700 dark:text-slate-300">样式方案</h3>
          <p class="text-slate-500 dark:text-slate-400">Tailwind CSS</p>
        </div>
        <div class="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
          <h3 class="font-semibold text-slate-700 dark:text-slate-300">状态管理</h3>
          <p class="text-slate-500 dark:text-slate-400">Pinia</p>
        </div>
        <div class="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
          <h3 class="font-semibold text-slate-700 dark:text-slate-300">图表库</h3>
          <p class="text-slate-500 dark:text-slate-400">ECharts</p>
        </div>
      </div>
    </section>

    <!-- 主要功能 -->
    <section class="space-y-4">
      <h2 class="text-2xl font-bold text-slate-800 dark:text-slate-100">主要功能</h2>
      <ul class="space-y-2 text-slate-600 dark:text-slate-300">
        <li class="flex items-start gap-2">
          <span class="text-primary-500 mt-1">•</span>
          <span>车票信息管理：添加、编辑、删除和查看车票信息</span>
        </li>
        <li class="flex items-start gap-2">
          <span class="text-primary-500 mt-1">•</span>
          <span>数据可视化：通过图表展示出行统计信息</span>
        </li>
        <li class="flex items-start gap-2">
          <span class="text-primary-500 mt-1">•</span>
          <span>响应式设计：适配不同屏幕尺寸的设备</span>
        </li>
        <li class="flex items-start gap-2">
          <span class="text-primary-500 mt-1">•</span>
          <span>深色模式：支持亮色和暗色主题切换</span>
        </li>
      </ul>
    </section>

    <!-- 联系方式 -->
    <section class="space-y-4">
      <h2 class="text-2xl font-bold text-slate-800 dark:text-slate-100">联系方式</h2>
      <div class="flex flex-col gap-3">
        <div class="flex items-center gap-4 text-slate-600 dark:text-slate-300">
          <span class="font-semibold">作者：</span>
          <span>SiYuan</span>
        </div>
        <div class="flex items-center gap-4 text-slate-600 dark:text-slate-300">
          <span class="font-semibold">邮箱：</span>
          <a href="mailto:sixyuan044@gmail.com" class="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 transition-colors">
            sixyuan044@gmail.com
          </a>
        </div>
      </div>
    </section>

    <!-- 开源地址 -->
    <section class="space-y-4">
      <h2 class="text-2xl font-bold text-slate-800 dark:text-slate-100">开源地址</h2>
      <div class="flex items-center gap-4 text-slate-600 dark:text-slate-300">
        <span class="font-semibold">GitHub：</span>
        <a href="https://github.com/LC044/TrailSnap" target="_blank" rel="noopener noreferrer" class="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 transition-colors flex items-center gap-2">
          <i class="mgc_github_2_line text-2xl"></i>
          <span>github.com/LC044/TrailSnap</span>
        </a>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.about-page {
  padding-top: 2rem;
  padding-bottom: 4rem;
}
</style>