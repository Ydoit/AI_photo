<template>
  <div class="mx-auto mt-20 min-w-0 max-w-7xl overflow-hidden lg:mt-[-4.5rem] lg:h-dvh lg:px-8">
    <div class="relative mx-auto block size-full min-w-0 max-w-[1800px] flex-col flex-wrap items-center lg:flex lg:flex-row">
      <div class="hero-content item text-left">
        <!-- 深色模式下文字颜色调整 -->
        <p class="greeting p-2 text-2xl text-gray-600 dark:text-gray-300">Hi, I’m <span class="font-bold">SiYuan</span> <span class="wave">👋</span></p>
        <p class="title p-2 text-4xl text-gray-800 dark:text-gray-100">An undergraduate student </p>
        <p class="subtitle p-2 text-xl text-gray-600 dark:text-gray-300">studying computer science with a research focus on databases.</p>

        <!-- 社交链接/图标列表 -->
        <ul class="social-links flex gap-4 p-0 mt-4 mb-0 list-none">
          <li class="flex items-center justify-center w-10 h-10 text-4xl rounded-full">
            <a href="https://github.com/LC044" target="_blank" rel="noreferrer" class="text-gray-600 dark:text-gray-300 transition-all duration-200 hover:scale-110 hover:text-pink-400">
              <i class="mgc_github_2_line"></i>
            </a>
          </li>
          <li class="flex items-center justify-center w-10 h-10 text-4xl rounded-full">
            <a href="mailto:sixyuan044@gmail.com" target="_blank" rel="noreferrer" class="text-gray-600 dark:text-gray-300 transition-all duration-200 hover:scale-110 hover:text-pink-400">
              <i class="mgc_mailbox_line"></i>
            </a>
          </li>
          <li class="flex items-center justify-center w-10 h-10 text-4xl rounded-full">
            <a href="https://blog.lc044.love" target="_blank" rel="noreferrer" class="text-gray-600 dark:text-gray-300 transition-all duration-200 hover:scale-110 hover:text-pink-400">
              <i class="mgc_comment_2_line"></i>
            </a>
          </li>
          <!-- ... -->
        </ul>
      </div>

      <div class="item flex flex-col justify-center items-center">
        <!-- 角色插画（深色模式下添加轻微阴影增强对比度） -->
        <img src="/avatar.png" alt="avatar" class="hero-avatar w-[300px] max-w-[40vw] object-contain animate-float dark:shadow-lg dark:shadow-pink-500/10" />
      </div>
      <!-- 卡片列表（网格布局） -->
    </div>
  </div>

  <!-- 底部文字和箭头（深色模式颜色调整） -->
  <div class="inset-x-0 bottom-0 mt-12 flex flex-col items-center text-center lg:absolute lg:mt-0 text-neutral-800/80 dark:text-neutral-200/80 opacity-100 transform-none">
    <small>司然后能行，行所以致远。</small>
    <span class="mt-8 animate-bounce">
      <i class="mgc_down_line text-3xl inline-block"></i>
    </span>
  </div>
</template>

<script setup>
import { ref } from 'vue'
defineProps({
  msg: String,
})

const count = ref(0)
</script>

<style scoped>
/* 保留关键动画和无法用Tailwind实现的样式 */
.wave {
  display: inline-block;
  animation: wave 1s infinite alternate;
}

.animate-float {
  animation: floatUpDown 3s ease-in-out infinite alternate;
}

@keyframes wave {
  from { transform: rotate(0deg); }
  to { transform: rotate(20deg); }
}

@keyframes floatUpDown {
  from { transform: translateY(0); }
  to { transform: translateY(-20px); }
}

/* 响应式补充样式 */
@media (max-width: 767px) {
  .hero-content {
    text-align: center;
    align-items: center;
  }
  .fullscreen-div {
      position: relative;
      display: flex;
      flex-direction:column;
      justify-content: center;
      align-items: center;
      height: 100vh;
      max-width: 1080px;
  }
  content {
      display: flex;
      gap: 20px;
  }
  .item {
    flex: 0;
    display: flex;
    flex-direction:column;
    justify-content: center;
  }
  .hero {
    align-items: center;
    text-align: center;
  }
  .hero-content {
    align-items: center;
    text-align: center;
  }
  .item {
    flex: 0;
    display: flex;
  }
  .hero-avatar {
    position: static;
    margin-top: 2rem;
    width: 200px !important;
    max-width: 60vw !important;
    animation: none;
  }
}

/* 深色模式下的补充样式（无法用Tailwind实现的） */
.dark .social-links a {
  filter: brightness(0.9);
}
.dark .social-links a:hover {
  filter: brightness(1.1);
}
</style>