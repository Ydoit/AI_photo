<template>
  <div 
    ref="containerRef"
    class="fixed cursor-pointer right-1 md:right-2 top-1/2 transform -translate-y-1/2 z-40 flex flex-col items-end select-none py-4 pr-1 md:pr-2 touch-none max-h-[80vh] overflow-y-auto no-scrollbar"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
    @touchstart="handleTouchStart"
    @touchmove="handleTouchMove"
    @touchend="handleMouseLeave"
    @click="handleItemClick"
  >
    <div
      v-for="item in timelineItems"
      :key="item.key"
      :ref="el => setItemRef(el, item.key)"
      class="flex items-center justify-end group relative transition-all duration-200 w-12 md:w-24"
      :class="[
        item.isYearStart ? 'mt-2 mb-1' : 'my-[2px]'
      ]"
    >

      <!-- Year Label -->
      <div
        v-if="item.isYearStart"
        class="absolute right-6 md:right-8 text-[10px] md:text-xs font-bold font-mono transition-all duration-300"
        :class="[
          item.isActiveYear ? 'text-primary-500 scale-110' : 'text-gray-400 dark:text-gray-500'
        ]"
      >
        {{ item.year }}
      </div>

      <!-- Marker Line -->
      <div 
        class="h-px transition-all duration-300 rounded-full hover:w-10"
        :class="[
          item.isYearStart
            ? 'w-6 bg-gray-400 dark:bg-gray-400'
            : 'w-2 bg-gray-300 dark:bg-gray-600',
          item.isActive ? '!w-8 !bg-primary-500 shadow-[0_0_8px_rgba(var(--primary-500),0.6)]' : '',
        ]"
      ></div>
    </div>

    <!-- Independent Pointer -->
    <div 
      v-show="isHovering"
      class="absolute right-1 md:right-2 h-px bg-primary-500 w-8 md:w-12 pointer-events-none z-50 shadow-[0_0_8px_rgba(var(--primary-500),0.6)]"
      :style="pointerStyle"
    >
      <div class="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-primary-500 rounded-full shadow-sm"></div>
    </div>
  </div>

  <!-- Tooltip (teleported to body 防止被裁剪) -->
  <teleport to="body">
    <div 
      v-show="isHovering && hoveredDate"
      class="fixed bg-gray-900/90 text-white text-[10px] px-2 py-1 rounded whitespace-nowrap pointer-events-none z-[9999] backdrop-blur-sm shadow-lg transition-transform duration-50"
      :style="tooltipStyle"
    >
      {{ hoveredDate }}
    </div>
  </teleport>
</template>



<script setup lang="ts">
import { computed, ref, onUnmounted } from 'vue'

const props = defineProps<{
  dates: string[]
  activeDate: string
}>()

const emit = defineEmits(['select'])

// State
const containerRef = ref<HTMLElement | null>(null)
const itemRefs = ref<Map<string, HTMLElement>>(new Map())
const hoveredDate = ref<string | null>(null)
const isHovering = ref(false)
const pointerTop = ref(0)
const tooltipTop = ref(0)

// Collect refs
const setItemRef = (el: any, key: string) => {
  if (el) itemRefs.value.set(key, el as HTMLElement)
  else itemRefs.value.delete(key)
}

interface TimelineItem {
  key: string
  year: number
  month: number
  dateStr: string
  isYearStart: boolean
  hasData: boolean
  isActive: boolean
  isActiveYear: boolean
}

// Build items
const timelineItems = computed(() => {
  if (!props.dates.length) return []

  const activeYear = props.activeDate ? parseInt(props.activeDate.split('年')[0]) : null
  const parsedDates = props.dates.map(d => {
    const parts = d.split('年')
    return {
      year: parseInt(parts[0]),
      month: parseInt(parts[1].replace('月', ''))
    }
  })

  const minYear = Math.min(...parsedDates.map(d => d.year))
  const maxYear = Math.max(...parsedDates.map(d => d.year))
  const maxMonth = Math.max(...parsedDates.filter(d => d.year === maxYear).map(d => d.month))
  const minMonth = Math.min(...parsedDates.filter(d => d.year === minYear).map(d => d.month))

  const items: TimelineItem[] = []

  for (let y = maxYear; y >= minYear; y--) {
    const startM = (y === maxYear) ? maxMonth : 12
    const endM = (y === minYear) ? minMonth : 1
    
    for (let m = startM; m >= endM; m--) {
      const dateStr = `${y}年${String(m).padStart(2, '0')}月`
      const hasData = props.dates.includes(dateStr)
      const isYearStart = (y === maxYear && m === startM) || m === 12

      items.push({
        key: `${y}-${m}`,
        year: y,
        month: m,
        dateStr,
        isYearStart,
        hasData,
        isActive: props.activeDate === dateStr,
        isActiveYear: activeYear === y
      })
    }
  }
  return items
})

// Utility: find next active date
const findNextActive = (dateStr: string | null) => {
  if (!dateStr) return null
  const all = [...props.dates].sort()
  for (const d of all) {
    if (d >= dateStr) return d
  }
  return all[all.length - 1]
}

// Click logic
const handleItemClick = (e: MouseEvent) => {
  const next = findNextActive(hoveredDate.value)
  emit('select', next)
}

// Pointer / Tooltip style
const pointerStyle = computed(() => ({
  transform: `translateY(${pointerTop.value}px)`
}))

const tooltipStyle = computed(() => ({
  top: `${tooltipTop.value+5}px`,
  left: `calc(100vw - 160px)`,
}))

// Find closest item
const findClosestItem = (y: number) => {
  let closestKey: string | null = null
  let minDistance = Infinity
  let closestItemCenter = 0

  for (const [key, el] of itemRefs.value.entries()) {
    const rect = el.getBoundingClientRect()
    const containerRect = containerRef.value!.getBoundingClientRect()
    const itemCenter = (rect.top - containerRect.top) + rect.height / 2

    const dist = Math.abs(y - itemCenter)
    if (dist < minDistance) {
      minDistance = dist
      closestKey = key
      closestItemCenter = itemCenter
    }
  }
  return { key: closestKey, center: closestItemCenter }
}

// Instant update hovered date（无延迟）
const updateHoveredDate = (key: string | null) => {
  if (!key) {
    hoveredDate.value = null
    return
  }
  const item = timelineItems.value.find(i => i.key === key)
  hoveredDate.value = item ? item.dateStr : null
}

let rafId: number | null = null

const updatePosition = (clientY: number) => {
  if (!containerRef.value) return

  const containerRect = containerRef.value.getBoundingClientRect()
  const y = clientY - containerRect.top

  if (y < 0 || y > containerRect.height) {
    isHovering.value = false
    return
  }

  isHovering.value = true
  pointerTop.value = y- 18 // 指针在鼠标之上
  tooltipTop.value = containerRect.top + y - 16

  const { key } = findClosestItem(y)
  updateHoveredDate(key)
}

const handleMouseMove = (e: MouseEvent) => {
  if (rafId) cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(() => updatePosition(e.clientY))
}

const handleMouseLeave = () => {
  isHovering.value = false
  hoveredDate.value = null
  if (rafId) cancelAnimationFrame(rafId)
}

const handleTouchStart = (e: TouchEvent) => {
  e.preventDefault()
  if (e.touches.length > 0) updatePosition(e.touches[0].clientY)
}

const handleTouchMove = (e: TouchEvent) => {
  e.preventDefault()
  if (rafId) cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(() => {
    if (e.touches.length > 0) updatePosition(e.touches[0].clientY)
  })
}

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
})
</script>


<style scoped>
/* Optimize performance */
.will-change-transform {
  will-change: transform;
}
</style>