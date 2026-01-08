<template>
  <div class="annual-container w-full h-screen overflow-hidden bg-bg-light dark:bg-dark-navy text-light-text1 dark:text-dark-text-warm-gray">
    <!-- Scroll Wrapper -->
    <div 
      ref="scrollWrapper" 
      class="scroll-wrapper overflow-y-auto h-screen w-full relative"
      :class="{ 
        'snap-y snap-mandatory snap-container-mobile': !isDesktop, // 移动端保留snap
        'scroll-container-desktop': isDesktop // PC端单独样式
      }"
    >
       <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const scrollWrapper = ref(null)
const isDesktop = ref(false)
let isScrolling = false
let scrollAnimationFrame: number | null = null // 手动滚动的动画帧

// 判断设备类型
const judgeDevice = () => {
  const userAgent = navigator.userAgent
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent)
  isDesktop.value = !isMobile
}

/**
 * 手动实现平滑滚动（替代原生smooth，稳定无冲突）
 * @param {HTMLElement} el 滚动容器
 * @param {number} targetTop 目标位置
 * @param {number} duration 动画时长（ms）
 */
const smoothScrollTo = (el: HTMLElement, targetTop: number, duration = 400) => {
  // 取消上一次未完成的动画
  if (scrollAnimationFrame) cancelAnimationFrame(scrollAnimationFrame)
  
  const startTop = el.scrollTop
  const distance = targetTop - startTop
  const startTime = performance.now()

  // 缓动函数：ease-out（先快后慢，贴近原生滑动手感）
  const easeOut = (t: number, b: number, c: number, d: number) => {
    t /= d
    t--
    return c * (t * t * t + 1) + b
  }

  const animate = (currentTime: number) => {
    const elapsed = currentTime - startTime
    if (elapsed < duration) {
      el.scrollTop = easeOut(elapsed, startTop, distance, duration)
      scrollAnimationFrame = requestAnimationFrame(animate)
    } else {
      el.scrollTop = targetTop // 动画结束精准定位
      scrollAnimationFrame = null
      isScrolling = false
    }
  }

  scrollAnimationFrame = requestAnimationFrame(animate)
}

// 处理滚轮事件
const handleWheel = (e: WheelEvent) => {
  if (!isDesktop.value || !scrollWrapper.value) return

  e.preventDefault() // 阻止原生滚动
  if (isScrolling) return // 防抖
  isScrolling = true

  const wrapper = scrollWrapper.value as HTMLElement
  const viewportHeight = wrapper.clientHeight
  const scrollHeight = wrapper.scrollHeight
  const currentScrollTop = wrapper.scrollTop
  const isDown = e.deltaY > 0

  // 计算目标位置
  let targetScrollTop = isDown 
    ? Math.min(currentScrollTop + viewportHeight, scrollHeight - viewportHeight)
    : Math.max(currentScrollTop - viewportHeight, 0)

  // 用手动平滑滚动替代原生scrollTo
  smoothScrollTo(wrapper, targetScrollTop, 600)
}

onMounted(() => {
  judgeDevice()
  const wrapper = scrollWrapper.value
  if (wrapper && isDesktop.value) {
    (wrapper as HTMLElement).addEventListener('wheel', handleWheel as EventListener, { passive: false })
  }
})

onUnmounted(() => {
  const wrapper = scrollWrapper.value as unknown as HTMLElement
  if (wrapper && isDesktop.value) {
    wrapper.removeEventListener('wheel', handleWheel as EventListener)
  }
  if (scrollAnimationFrame) cancelAnimationFrame(scrollAnimationFrame)
})
</script>

<style scoped>
.scroll-wrapper {
  scrollbar-width: none;
  scroll-behavior: smooth; /* 仅给移动端兜底，PC端会被覆盖 */
}
.scroll-wrapper::-webkit-scrollbar { display: none; }

/* 移动端：保留snap样式，保证原生丝滑 */
.snap-container-mobile > * {
  scroll-snap-align: start;
  scroll-snap-stop: always;
  height: 100vh;
}

/* PC端：完全移除所有snap样式，避免干扰手动滚动 */
.scroll-container-desktop {
  scroll-behavior: auto !important; /* 禁用原生smooth，避免冲突 */
}
.scroll-container-desktop > * {
  scroll-snap-align: none !important; /* 彻底关闭子项吸附 */
  scroll-snap-stop: normal !important;
  height: 100vh; /* 仅保留全屏高度，无其他snap相关样式 */
}
</style>