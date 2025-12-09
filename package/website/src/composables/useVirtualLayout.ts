import { ref, computed, watch, type Ref } from 'vue'
import type { TimelineStats, TimelineItem } from '@/types/album'
import type { AlbumImage } from '@/stores/photoStore'

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
  layoutMode: Ref<'grid' | 'masonry' | 'waterfall' | 'list'> // Added 'waterfall'
  viewSize: Ref<'sm' | 'md' | 'lg'>
  photos: Ref<AlbumImage[]> // Added photos dependency
}

export function useVirtualLayout(options: UseVirtualLayoutOptions) {
  const { timelineStats, containerWidth, layoutMode, viewSize, photos } = options

  const monthBlocks = ref<MonthBlock[]>([])
  const totalHeight = ref(0)
  
  // Expose these for component use
  const colCount = ref(3)
  const rowHeightVal = ref(0)
  const gapVal = ref(0)

  // Configuration constants
  const HEADER_HEIGHT = 0 
  const DAY_HEADER_HEIGHT = 50
  
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

    const mode = layoutMode.value
    const cols = getColumns()
    const gap = getGap()
    const width = containerWidth.value || 1000 
    
    // Update refs
    colCount.value = cols
    gapVal.value = gap

    let rowHeight = 0
    if (mode === 'grid' || mode === 'masonry') {
         const colWidth = (width - (cols - 1) * gap) / cols
         // Grid: Square (1:1) if mode is 'grid', else 3:2 if 'masonry' (legacy default)
         // But user wants 'Square' as one mode. Let's assume 'grid' = Square.
         // And 'waterfall' = Justified.
         // If user selects 'Square', we use 1:1.
         // If user selects 'Waterfall', we handle below.
         // Let's assume 'grid' is the default Square mode now as per request "Square layout".
         const aspectRatio = (mode === 'grid') ? 1 : 1.5 
         rowHeight = colWidth / aspectRatio
    } else if (mode === 'waterfall') {
         rowHeight = 220 // Target Row Height for Waterfall
    }
    
    rowHeightVal.value = rowHeight
    
    // Group photos by day for Waterfall calculation
    const photosByDay = new Map<string, AlbumImage[]>()
    if (mode === 'waterfall') {
        photos.value.forEach(p => {
             const d = new Date(p.timestamp)
             const key = `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`
             if (!photosByDay.has(key)) photosByDay.set(key, [])
             photosByDay.get(key)!.push(p)
        })
    }

    // Group Timeline by Month
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
        let currentMonthTop = HEADER_HEIGHT 
        let monthCount = 0

        data.days.forEach(dayItem => {
            let rows = 0
            let contentHeight = 0
            
            if (mode === 'waterfall') {
                // Calculate rows for Justified Layout
                const dayKey = `${dayItem.year}-${dayItem.month}-${dayItem.day}`
                const dayPhotos = photosByDay.get(dayKey) || []
                
                let currentWidth = 0
                rows = 1
                
                // We need to iterate 'dayItem.count' times
                for (let i = 0; i < dayItem.count; i++) {
                    // Try to get photo
                    let ar = 1.5
                    if (i < dayPhotos.length) {
                        const p = dayPhotos[i]
                        if (p.width && p.height) ar = p.width / p.height
                    }
                    
                    const itemWidth = rowHeight * ar
                    
                    if (currentWidth + itemWidth > width) {
                        rows++
                        currentWidth = itemWidth + gap
                    } else {
                        currentWidth += (currentWidth > 0 ? gap : 0) + itemWidth
                    }
                }
                
                contentHeight = rows * rowHeight + Math.max(0, rows - 1) * gap
            } else {
                // Standard Grid / Square
                rows = Math.ceil(dayItem.count / cols)
                contentHeight = rows * rowHeight + Math.max(0, rows - 1) * gap
            }

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
  // Added photos to watch list
  watch([() => timelineStats.value, containerWidth, layoutMode, viewSize, () => photos.value.length], () => {
    recalculateLayout()
  }, { immediate: true })

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
