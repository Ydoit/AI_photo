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
      v-for="item in displayItems"
      :key="item.key"
      :ref="el => setItemRef(el, item.key)"
      class="flex items-center justify-end group relative transition-all duration-200 w-12 md:w-24"
      :class="[
        item.isYearStart ? 'mt-4 mb-1' : 'my-[2px]'
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

      <!-- Month Label (Hover) -->
      <div
        v-if="!item.isYearStart"
        class="absolute right-6 md:right-8 text-[9px] font-mono text-gray-300 dark:text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity"
      >
        {{ item.month }}
      </div>

      <!-- Marker Line -->
      <div 
        class="h-1 rounded-full transition-all duration-300"
        :class="[
          item.isYearStart
            ? 'w-4 bg-gray-400 dark:bg-gray-400'
            : 'w-2 bg-gray-300 dark:bg-gray-600',
          item.isActive ? '!w-6 !bg-primary-500 shadow-[0_0_8px_rgba(var(--primary-500),0.6)]' : '',
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

  <!-- Tooltip (teleported to body) -->
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
import { computed, ref, onUnmounted, watch } from 'vue'
import type { TimelineItem as ApiTimelineItem } from '@/types/album'

const props = defineProps<{
  items: ApiTimelineItem[]
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

interface DisplayItem {
  key: string
  year: number
  month: number
  dateStr: string
  isYearStart: boolean
  isActive: boolean
  isActiveYear: boolean
}

// Build items (Group by Month)
const displayItems = computed(() => {
  if (!props.items?.length) return []

  // Parse active date (format: "YYYY年MM月" or "YYYY-MM")
  const activeMatch = props.activeDate ? (props.activeDate.match(/(\d+)年(\d+)月/) || props.activeDate.match(/(\d+)-(\d+)/)) : null
  const activeYear = activeMatch ? parseInt(activeMatch[1]) : null
  const activeMonth = activeMatch ? parseInt(activeMatch[2]) : null
  
  // Aggregate by Month
  const monthMap = new Map<string, { year: number, month: number }>()
  
  props.items.forEach(item => {
      const key = `${item.year}-${item.month}`
      if (!monthMap.has(key)) {
          monthMap.set(key, { year: item.year, month: item.month })
      }
  })

  // Sort Descending
  const sortedMonths = Array.from(monthMap.values()).sort((a, b) => {
      if (a.year !== b.year) return b.year - a.year
      return b.month - a.month
  })

  const items: DisplayItem[] = []
  let lastYear = -1

  sortedMonths.forEach((p) => {
      const isYearStart = p.year !== lastYear
      if (isYearStart) lastYear = p.year

      const dateStr = `${p.year}年${String(p.month).padStart(2, '0')}月`
      
      items.push({
        key: dateStr,
        year: p.year,
        month: p.month,
        dateStr: dateStr,
        isYearStart: isYearStart,
        isActive: activeYear === p.year && activeMonth === p.month,
        isActiveYear: activeYear === p.year
      })
  })

  return items
})

// Click logic
const handleItemClick = (e: MouseEvent) => {
  updatePosition(e.clientY)
  if (hoveredDate.value) {
    emit('select', hoveredDate.value)
  }
}

// Pointer / Tooltip style
const pointerStyle = computed(() => ({
  transform: `translateY(${pointerTop.value}px)`
}))

const tooltipStyle = computed(() => ({
  top: `${tooltipTop.value}px`,
  left: `calc(100vw - 140px)`,
}))

// Find closest item
const findClosestItem = (y: number) => {
  let closestKey: string | null = null
  let minDistance = Infinity

  for (const [key, el] of itemRefs.value.entries()) {
    const rect = el.getBoundingClientRect()
    const containerRect = containerRef.value!.getBoundingClientRect()
    const itemCenter = (rect.top - containerRect.top) + rect.height / 2

    const dist = Math.abs(y - itemCenter)
    if (dist < minDistance) {
      minDistance = dist
      closestKey = key
    }
  }
  return { key: closestKey }
}

// Instant update hovered date
const updateHoveredDate = (key: string | null) => {
  if (!key) {
    hoveredDate.value = null
    return
  }
  const item = displayItems.value.find(i => i.key === key)
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
  pointerTop.value = y
  tooltipTop.value = clientY - 10

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
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
