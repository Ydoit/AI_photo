<template>
  <div ref="containerRef" class="w-full h-full flex items-center justify-center bg-gray-200 relative overflow-hidden">
    <!-- Character Group Container -->
    <div class="relative w-[400px] h-[400px]">
      
      <!-- Purple Character (Back Left) -->
      <div class="absolute left-16 bottom-0 w-40 h-96 bg-[#6366F1] rounded-t-2xl z-10 transition-all duration-300 origin-bottom"
           :class="{ 
             'animate-bounce-custom': isCelebrating && !isEntering,
             'animate-shake': isMocking && !isEntering,
             'animate-drop-in': isEntering,
             '-skew-x-12 translate-x-8': focusTarget === 'username' && !isEntering
           }"
           :style="isEntering ? { animationDelay: '0ms' } : {}">
        <!-- Eyes -->
        <div class="absolute top-12 left-10 flex space-x-4">
          <!-- Normal Eyes -->
          <template v-if="!isMocking">
            <div class="w-8 h-8 bg-white rounded-full relative flex items-center justify-center overflow-hidden">
              <div class="w-3 h-3 bg-black rounded-full transition-transform duration-75 ease-out"
                   :style="getPupilStyle(64 + 40 + 16, 400 - 96*4 + 48 + 16)"></div>
            </div>
            <div class="w-8 h-8 bg-white rounded-full relative flex items-center justify-center overflow-hidden">
              <div class="w-3 h-3 bg-black rounded-full transition-transform duration-75 ease-out"
                   :style="getPupilStyle(64 + 40 + 32 + 16, 400 - 96*4 + 48 + 16)"></div>
            </div>
          </template>
          <!-- Mocking Eyes (Squint/Happy) -->
          <template v-else>
            <div class="w-8 h-8 flex items-center justify-center">
               <div class="w-6 h-2 bg-black rounded-full transform rotate-12"></div>
            </div>
            <div class="w-8 h-8 flex items-center justify-center">
               <div class="w-6 h-2 bg-black rounded-full transform -rotate-12"></div>
            </div>
          </template>
        </div>
      </div>

      <!-- Black Character (Back Right) -->
      <div class="absolute right-16 bottom-0 w-32 h-72 bg-[#1E293B] rounded-t-2xl z-20 transition-all duration-300 delay-75 origin-bottom"
           :class="{ 
             'animate-bounce-custom': isCelebrating && !isEntering,
             'animate-shake': isMocking && !isEntering,
             'animate-drop-in': isEntering,
             '-skew-x-6 translate-x-4': focusTarget === 'username' && !isEntering
           }"
           :style="isEntering ? { animationDelay: '100ms' } : {}">
        <!-- Eyes -->
        <div class="absolute top-10 left-6 flex space-x-4">
          <template v-if="!isMocking">
            <div class="w-8 h-8 bg-white rounded-full relative flex items-center justify-center overflow-hidden">
              <div class="w-3 h-3 bg-black rounded-full transition-transform duration-75 ease-out"
                   :style="getPupilStyle(400 - 16 - 32 + 24 + 16, 400 - 72 + 40 + 16)"></div>
            </div>
            <div class="w-8 h-8 bg-white rounded-full relative flex items-center justify-center overflow-hidden">
              <div class="w-3 h-3 bg-black rounded-full transition-transform duration-75 ease-out"
                   :style="getPupilStyle(400 - 16 - 32 + 24 + 32 + 16, 400 - 72 + 40 + 16)"></div>
            </div>
          </template>
          <template v-else>
             <div class="w-8 h-8 flex items-center justify-center">
               <div class="w-4 h-4 border-t-4 border-r-4 border-white transform rotate-45"></div>
             </div>
             <div class="w-8 h-8 flex items-center justify-center">
               <div class="w-4 h-4 border-t-4 border-l-4 border-white transform -rotate-45"></div>
             </div>
          </template>
        </div>
      </div>

      <!-- Orange Character (Front Left) -->
      <div class="absolute left-4 bottom-0 w-44 h-36 bg-[#F97316] rounded-t-full z-30 transition-all duration-300 delay-100 origin-bottom"
           :class="{ 
             'animate-bounce-custom': isCelebrating && !isEntering,
             'animate-shake': isMocking && !isEntering,
             'animate-drop-in': isEntering,
             '-skew-x-3 translate-x-2': focusTarget === 'username' && !isEntering
           }"
           :style="isEntering ? { animationDelay: '200ms' } : {}">
        <!-- Eyes -->
        <div class="absolute top-10 left-10 flex space-x-8">
           <template v-if="!isMocking">
             <div class="w-6 h-6 bg-white rounded-full relative flex items-center justify-center overflow-hidden">
               <div class="w-2 h-2 bg-black rounded-full transition-transform duration-75 ease-out"
                    :style="getPupilStyle(4 + 10 + 12, 400 - 36 + 10 + 12)"></div>
             </div>
             <div class="w-6 h-6 bg-white rounded-full relative flex items-center justify-center overflow-hidden">
               <div class="w-2 h-2 bg-black rounded-full transition-transform duration-75 ease-out"
                    :style="getPupilStyle(4 + 10 + 24 + 12, 400 - 36 + 10 + 12)"></div>
             </div>
           </template>
           <template v-else>
              <div class="w-6 h-6 flex items-center justify-center">
                 <div class="w-4 h-1 bg-black rounded-full"></div>
              </div>
              <div class="w-6 h-6 flex items-center justify-center">
                 <div class="w-4 h-1 bg-black rounded-full"></div>
              </div>
           </template>
        </div>
        <!-- Mouth -->
         <div class="absolute bottom-10 left-1/2 transform -translate-x-1/2 w-8 h-4 border-[#111827] rounded-full opacity-80 transition-all duration-300"
              :class="isMocking ? 'border-b-0 border-t-4 h-2 mt-2' : 'border-b-4'"></div>
      </div>

      <!-- Yellow Character (Front Right) -->
      <div class="absolute right-8 bottom-0 w-28 h-40 bg-[#FACC15] rounded-t-full z-40 transition-all duration-300 delay-150 origin-bottom"
           :class="{ 
             'animate-bounce-custom': isCelebrating && !isEntering,
             'animate-shake': isMocking && !isEntering,
             'animate-drop-in': isEntering,
             '-skew-x-3 translate-x-2': focusTarget === 'username' && !isEntering
           }"
           :style="isEntering ? { animationDelay: '300ms' } : {}">
        <!-- Eyes -->
        <div class="absolute top-10 left-5 flex space-x-6">
           <template v-if="!isMocking">
             <div class="w-6 h-6 bg-white rounded-full relative flex items-center justify-center overflow-hidden">
               <div class="w-2 h-2 bg-black rounded-full transition-transform duration-75 ease-out"
                    :style="getPupilStyle(400 - 8 - 28 + 5 + 12, 400 - 40 + 10 + 12)"></div>
             </div>
             <div class="w-6 h-6 bg-white rounded-full relative flex items-center justify-center overflow-hidden">
               <div class="w-2 h-2 bg-black rounded-full transition-transform duration-75 ease-out"
                    :style="getPupilStyle(400 - 8 - 28 + 5 + 24 + 12, 400 - 40 + 10 + 12)"></div>
             </div>
           </template>
           <template v-else>
             <div class="w-6 h-6 flex items-center justify-center">
                <div class="w-4 h-4 text-black font-bold text-lg leading-none">></div>
             </div>
             <div class="w-6 h-6 flex items-center justify-center">
                <div class="w-4 h-4 text-black font-bold text-lg leading-none"><</div>
             </div>
           </template>
        </div>
        <!-- Mouth -->
        <div class="absolute top-20 left-1/2 transform -translate-x-1/2 w-10 h-2 bg-[#111827] rounded-full transition-all duration-300"
             :class="isMocking ? 'h-4 w-6 rounded-b-full' : ''"></div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, toRefs } from 'vue';

const props = defineProps<{
  focusTarget: 'username' | 'password' | null;
  isCelebrating: boolean;
  isMocking?: boolean;
}>();

const { focusTarget } = toRefs(props);
const mouseX = ref(0);
const mouseY = ref(0);
const containerRef = ref<HTMLElement | null>(null);
const containerRect = ref<DOMRect | null>(null);
const isEntering = ref(true);

const handleMouseMove = (e: MouseEvent) => {
  if (!focusTarget.value) {
    mouseX.value = e.clientX;
    mouseY.value = e.clientY;
  }
};

const updateContainerRect = () => {
  if (containerRef.value) {
    containerRect.value = containerRef.value.getBoundingClientRect();
  }
};

watch(focusTarget, (newVal) => {
  if (newVal === 'username') {
    mouseX.value = window.innerWidth; 
    mouseY.value = window.innerHeight / 2;
  } else if (newVal === 'password') {
    mouseX.value = 0;
    mouseY.value = 0;
  }
});

onMounted(() => {
  window.addEventListener('mousemove', handleMouseMove);
  window.addEventListener('resize', updateContainerRect);
  updateContainerRect();
  
  mouseX.value = window.innerWidth / 2;
  mouseY.value = window.innerHeight / 2;

  // 动画结束后移除入场状态
  setTimeout(() => {
    isEntering.value = false;
  }, 1000);
});

onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove);
  window.removeEventListener('resize', updateContainerRect);
});

// Helper to calculate pupil transform
const getPupilStyle = (x: number, y: number) => {
  if (!containerRect.value) return {};
  
  const centerX = containerRect.value.left + containerRect.value.width / 2;
  const centerY = containerRect.value.top + containerRect.value.height / 2;
  
  const boxLeft = centerX - 200;
  const boxTop = centerY - 200;
  
  const eyeScreenX = boxLeft + x;
  const eyeScreenY = boxTop + y;
  
  const dx = mouseX.value - eyeScreenX;
  const dy = mouseY.value - eyeScreenY;
  const angle = Math.atan2(dy, dx);
  const distance = Math.min(6, Math.sqrt(dx * dx + dy * dy) / 15);
  
  const moveX = Math.cos(angle) * distance;
  const moveY = Math.sin(angle) * distance;
  
  return {
    transform: `translate(${moveX}px, ${moveY}px)`
  };
};
</script>

<style scoped>
@keyframes bounce-custom {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px) rotate(-5deg); }
  75% { transform: translateX(5px) rotate(5deg); }
}

.animate-bounce-custom {
  animation: bounce-custom 0.5s ease-in-out infinite;
}

.animate-shake {
  animation: shake 0.3s ease-in-out infinite;
}

.animate-drop-in {
  animation: drop-bounce 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
  transition: none !important;
}

@keyframes drop-bounce {
  0% { transform: translateY(-100vh) scale(1); opacity: 0; }
  60% { transform: translateY(0) scale(1.3, 0.7); opacity: 1; }
  75% { transform: translateY(-20px) scale(0.9, 1.1); }
  90% { transform: translateY(0) scale(1.05, 0.95); }
  100% { transform: translateY(0) scale(1); }
}
</style>
