<template>
  <Transition name="slide-in">
    <div v-if="visible" class="fixed inset-0 z-[100] flex items-center justify-center pointer-events-none">
      <div class="absolute inset-0 z-10 bg-black/50 backdrop-blur-sm pointer-events-auto transition-opacity" @click="cancel"></div>
      <div class="bg-white dark:bg-gray-800 z-20 rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden pointer-events-auto m-4">
        <div class="p-6">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">{{ title }}</h3>
          <p class="text-gray-500 text-sm mb-6">{{ message }}</p>
          <div class="flex gap-3 justify-end">
             <button 
               @click="cancel"
               class="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors font-medium text-sm"
             >
               {{ cancelText }}
             </button>
             <button 
               @click="confirm"
               class="px-4 py-2 text-white rounded-lg transition-colors shadow-lg font-medium text-sm"
               :class="type === 'danger' ? 'bg-red-500 hover:bg-red-600 shadow-red-500/30' : 'bg-primary-500 hover:bg-primary-600 shadow-primary-500/30'"
             >
               {{ confirmText }}
             </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  visible: boolean
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'primary'
}>(), {
  title: '提示',
  message: '',
  confirmText: '确认',
  cancelText: '取消',
  type: 'danger'
})

const emit = defineEmits(['update:visible', 'confirm', 'cancel'])

const cancel = () => {
  emit('update:visible', false)
  emit('cancel')
}

const confirm = () => {
  emit('update:visible', false)
  emit('confirm')
}
</script>

<style scoped>
.slide-in-enter-active, .slide-in-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-in-enter-from, .slide-in-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
.slide-in-leave-active {
  transition-duration: 0.2s;
}
</style>