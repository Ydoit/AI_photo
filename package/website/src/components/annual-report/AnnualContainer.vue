<template>
  <div class="annual-container w-full h-screen overflow-hidden bg-bg-light dark:bg-dark-navy text-light-text1 dark:text-dark-text-warm-gray">
    <!-- Scroll Wrapper -->
    <div ref="scrollWrapper" class="scroll-wrapper snap-y snap-mandatory overflow-y-auto h-screen w-full relative">
       <slot />
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const scrollWrapper = ref(null)
// 标记是否为桌面端（用于区分处理逻辑）
const isDesktop = ref(false)
// 防止滚轮快速滚动时多次触发
let isScrolling = false

// 判断设备类型（简单版，也可结合ua判断）
const judgeDevice = () => {
  const userAgent = navigator.userAgent
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent)
  isDesktop.value = !isMobile
}

// 处理滚轮事件
const handleWheel = (e) => {
  // 只在桌面端拦截默认行为
  if (!isDesktop.value) return

  // 阻止默认滚动（消除小段位移）
  e.preventDefault()
  
  // 防抖：避免快速滚动时多次触发
  if (isScrolling) return
  isScrolling = true
  setTimeout(() => { isScrolling = false }, 300)

  const wrapper = scrollWrapper.value
  const scrollHeight = wrapper.scrollHeight
  const viewportHeight = wrapper.clientHeight
  
  // 判断滚动方向：向上（负值）/向下（正值）
  const isDown = e.deltaY > 0
  
  // 计算目标滚动位置
  let targetScrollTop
  if (isDown) {
    // 向下滚动：滚动到当前位置 + 一屏高度（不超过最大滚动值）
    targetScrollTop = Math.min(wrapper.scrollTop + viewportHeight, scrollHeight - viewportHeight)
  } else {
    // 向上滚动：滚动到当前位置 - 一屏高度（不小于0）
    targetScrollTop = Math.max(wrapper.scrollTop - viewportHeight, 0)
  }

  // 平滑滚动到目标位置（替代原生snap的吸附）
  wrapper.scrollTo({
    top: targetScrollTop,
    behavior: 'smooth' // 保持丝滑的滚动动画
  })
}

onMounted(() => {
  judgeDevice()
  const wrapper = scrollWrapper.value
  if (wrapper && isDesktop.value) {
    // 监听滚轮事件（passive: false 才能阻止默认行为）
    wrapper.addEventListener('wheel', handleWheel, { passive: false })
  }
})

onUnmounted(() => {
  const wrapper = scrollWrapper.value
  if (wrapper && isDesktop.value) {
    wrapper.removeEventListener('wheel', handleWheel)
  }
})
</script>

<style scoped>
.scroll-wrapper {
  scroll-behavior: smooth;
  scrollbar-width: none;
  /* 补充CSS优化：确保每个子项的吸附更精准 */
  scroll-snap-type: y mandatory;
}
.scroll-wrapper::-webkit-scrollbar { display: none; }

/* 给slot里的每一个子项（Section）添加吸附对齐（关键） */
.scroll-wrapper > * {
  scroll-snap-align: start; /* 吸附到子项的顶部 */
  scroll-snap-stop: always; /* 强制停在当前子项，不跳过 */
  height: 100vh; /* 确保每个Section都是全屏高度（如果Section本身没设置，这里兜底） */
}
</style>
