<template>
  <div class="not-prose">
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-lg overflow-hidden border border-slate-200 dark:border-slate-700">
      <div class="p-6 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
        <h3 class="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2 m-0">
          <ScanLine class="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
          12306 电子车票的识别效果展示
        </h3>
        <p class="text-slate-500 dark:text-slate-400 mt-2 text-sm">
          左侧为 12306 App「本人车票」原图，右侧为识别效果图。
        </p>
      </div>

      <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
        <div class="flex flex-col gap-3">
          <div class="flex items-center gap-2 text-slate-700 dark:text-slate-200 font-medium">
            <ImageIcon class="w-5 h-5 text-indigo-500" />
            车票原图
          </div>
          <div
            class="relative group cursor-zoom-in rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-sm bg-slate-100 dark:bg-slate-900 aspect-[4/3]"
            @click="openLightbox('/images/img_1.png', '车票原图')"
          >
            <img
              src="/images/img_1.png"
              alt="车票原图"
              class="w-full h-full object-contain hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
            <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center">
              <ZoomIn class="w-8 h-8 text-white opacity-0 group-hover:opacity-100 drop-shadow-md transition-opacity" />
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-3">
          <div class="flex items-center gap-2 text-slate-700 dark:text-slate-200 font-medium">
            <CheckCircle2 class="w-5 h-5 text-green-500" />
            识别效果图
          </div>
          <div
            class="relative group cursor-zoom-in rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-sm bg-slate-100 dark:bg-slate-900 aspect-[4/3]"
            @click="openLightbox('/images/img.png', '识别效果图')"
          >
            <img
              src="/images/img.png"
              alt="识别效果图"
              class="w-full h-full object-contain hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
            <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center">
              <ZoomIn class="w-8 h-8 text-white opacity-0 group-hover:opacity-100 drop-shadow-md transition-opacity" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <Transition name="fade">
      <div
        v-if="lightbox.isOpen"
        class="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-sm p-4"
        @click="closeLightbox"
      >
        <button
          class="absolute top-4 right-4 text-white/70 hover:text-white transition-colors p-2"
          @click.stop="closeLightbox"
        >
          <X class="w-8 h-8" />
        </button>

        <div class="max-w-[90vw] max-h-[90vh] flex flex-col items-center gap-4" @click.stop>
          <img
            :src="lightbox.src"
            :alt="lightbox.title"
            class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
          />
          <span class="text-white/90 font-medium text-lg">{{ lightbox.title }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ScanLine, Image as ImageIcon, CheckCircle2, ZoomIn, X } from 'lucide-vue-next'

const lightbox = ref({
  isOpen: false,
  src: '',
  title: ''
})

const openLightbox = (src: string, title: string) => {
  lightbox.value = {
    isOpen: true,
    src,
    title
  }
  document.body.style.overflow = 'hidden'
}

const closeLightbox = () => {
  lightbox.value.isOpen = false
  document.body.style.overflow = ''
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && lightbox.value.isOpen) {
    closeLightbox()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
