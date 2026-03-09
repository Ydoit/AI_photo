import { ref, computed, watch, type Ref } from 'vue'
import type { TimelineStats, TimelineItem, AlbumImage } from '@/types/album'

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
    // If no timeline, check if we have photos to show in a flat list
    if (!timelineStats.value?.timeline && photos.value.length === 0) {
        monthBlocks.value = []
        totalHeight.value = 0
        return
    }

    // Prepare timeline data
    let timeline = timelineStats.value?.timeline 
      ? [...timelineStats.value.timeline].sort((a, b) => {
          if (a.year !== b.year) return b.year - a.year
          if (a.month !== b.month) return b.month - a.month
          return b.day - a.day
        })
      : []

    // If no timeline data but we have photos, create a dummy timeline item
    if (timeline.length === 0 && photos.value.length > 0) {
       // Create a single "All Photos" block
       // We can iterate photos to find date range or just group them all
       // For simplicity, let's treat them as one large group
       timeline = [{
         year: 0,
         month: 0,
         day: 0,
         count: photos.value.length
       }]
    }

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
                // For dummy timeline (year=0), we need to map photos correctly
                // If timeline is dummy, we can't key by date. 
                // We should rely on global indices or just map all photos.
                
                // If it's a dummy day (year=0), just take the slice of photos for this "day"
                // But wait, the loop below iterates dayItem.count.
                // We need to fetch the correct photos.
                // The globalIndex tracks where we are in the photo array.
                // So we can use globalIndex + i to access photos.value
                
                let currentWidth = 0
                rows = 1
                
                // We need to iterate 'dayItem.count' times
                for (let i = 0; i < dayItem.count; i++) {
                    // Try to get photo
                    let ar = 1.5
                    const pIndex = globalIndex + i
                    if (pIndex < photos.value.length) {
                        const p = photos.value[pIndex]
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
            
            // If it's the dummy day, don't show header?
            // Or just show 0 height header.
            const isDummy = dayItem.year === 0
            const effectiveHeaderHeight = isDummy ? 0 : DAY_HEADER_HEIGHT

            const dayHeight = effectiveHeaderHeight + contentHeight + gap 
            
            dayBlocks.push({
                key: isDummy ? 'all' : `${dayItem.year}-${dayItem.month}-${dayItem.day}`,
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
