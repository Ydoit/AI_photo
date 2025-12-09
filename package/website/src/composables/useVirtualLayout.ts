import { ref, computed, watch, type Ref } from 'vue'
import type { TimelineStats, TimelineItem } from '@/types/album'

export interface DayBlock {
  key: string // YYYY-MM-DD
  year: number
  month: number
  day: number
  count: number
  startIndex: number // Global index
  height: number
  top: number // Relative to Month top
  rows: number
}

export interface MonthBlock {
  key: string
  year: number
  month: number
  count: number
  startIndex: number
  height: number
  top: number
  days: DayBlock[]
}

interface UseVirtualLayoutOptions {
  timelineStats: Ref<TimelineStats | undefined>
  containerWidth: Ref<number>
  layoutMode: Ref<'grid' | 'masonry' | 'list'>
  viewSize: Ref<'sm' | 'md' | 'lg'>
}

export function useVirtualLayout(options: UseVirtualLayoutOptions) {
  const { timelineStats, containerWidth, layoutMode, viewSize } = options

  const monthBlocks = ref<MonthBlock[]>([])
  const totalHeight = ref(0)
  
  // Expose these for component use
  const colCount = ref(3)
  const rowHeightVal = ref(0)
  const gapVal = ref(0)

  // Configuration constants
  const HEADER_HEIGHT = 60 // Month header height
  const DAY_HEADER_HEIGHT = 40 // Day header height (New)
  
  const getGap = () => {
    return viewSize.value === 'lg' ? 16 : 8
  }
  
  // Get columns based on viewSize
  const getColumns = () => {
    const width = containerWidth.value || window.innerWidth
    if (viewSize.value === 'sm') return width < 640 ? 4 : (width < 768 ? 6 : (width < 1024 ? 8 : 12))
    if (viewSize.value === 'md') return width < 640 ? 3 : (width < 768 ? 5 : (width < 1024 ? 6 : 8))
    return width < 640 ? 2 : (width < 768 ? 3 : (width < 1024 ? 4 : 6))
  }

  const recalculateLayout = () => {
    if (!timelineStats.value?.timeline) {
        monthBlocks.value = []
        totalHeight.value = 0
        return
    }

    const timeline = [...timelineStats.value.timeline].sort((a, b) => {
        if (a.year !== b.year) return b.year - a.year
        if (a.month !== b.month) return b.month - a.month
        return b.day - a.day
    })

    const cols = getColumns()
    const gap = getGap()
    const width = containerWidth.value || 1000 
    
    // Update refs
    colCount.value = cols
    gapVal.value = gap

    const colWidth = (width - (cols - 1) * gap) / cols
    const rowHeight = colWidth / 1.5 // 3:2 Aspect Ratio
    rowHeightVal.value = rowHeight
    
    // Group by Month
    const months = new Map<string, { year: number, month: number, days: TimelineItem[] }>()
    
    timeline.forEach(item => {
        const key = `${item.year}-${item.month}`
        if (!months.has(key)) {
            months.set(key, { year: item.year, month: item.month, days: [] })
        }
        months.get(key)!.days.push(item)
    })

    const blocks: MonthBlock[] = []
    let currentTop = 0
    let globalIndex = 0

    months.forEach((data, key) => {
        const dayBlocks: DayBlock[] = []
        let currentMonthTop = HEADER_HEIGHT // Start after Month Header
        let monthCount = 0

        data.days.forEach(dayItem => {
            const rows = Math.ceil(dayItem.count / cols)
            // Height = Header + (Rows * RowHeight) + (Gaps between rows)
            // Note: Gaps are between rows. If rows=1, gap=0.
            const contentHeight = rows * rowHeight + Math.max(0, rows - 1) * gap
            // Add margin bottom to day block? Say gap
            const dayHeight = DAY_HEADER_HEIGHT + contentHeight + gap 
            
            dayBlocks.push({
                key: `${dayItem.year}-${dayItem.month}-${dayItem.day}`,
                year: dayItem.year,
                month: dayItem.month,
                day: dayItem.day,
                count: dayItem.count,
                startIndex: globalIndex,
                height: dayHeight,
                top: currentMonthTop,
                rows
            })

            currentMonthTop += dayHeight
            monthCount += dayItem.count
            globalIndex += dayItem.count
        })

        // Month total height = currentMonthTop (which includes header and all days)
        // Check if we want extra padding at bottom of month
        const monthHeight = currentMonthTop 
        
        blocks.push({
            key,
            year: data.year,
            month: data.month,
            count: monthCount,
            startIndex: globalIndex - monthCount,
            height: monthHeight,
            top: currentTop,
            days: dayBlocks
        })
        
        currentTop += monthHeight
    })

    monthBlocks.value = blocks
    totalHeight.value = currentTop
  }

  // Watchers
  watch([() => timelineStats.value, containerWidth, layoutMode, viewSize], () => {
    recalculateLayout()
  }, { immediate: true })

  // Helper to find visible blocks
  const getVisibleBlocks = (scrollTop: number, viewportHeight: number, buffer = 1000) => {
    const startY = scrollTop - buffer
    const endY = scrollTop + viewportHeight + buffer
    
    return monthBlocks.value.filter(block => {
        const blockEnd = block.top + block.height
        return blockEnd > startY && block.top < endY
    })
  }

  return {
    monthBlocks,
    totalHeight,
    colCount,
    rowHeight: rowHeightVal,
    gap: gapVal,
    getVisibleBlocks,
    recalculateLayout
  }
}
