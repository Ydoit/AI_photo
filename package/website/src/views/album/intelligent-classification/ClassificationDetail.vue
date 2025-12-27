<template>
  <UnifiedPhotoPage
    :title="title"
    :subtitle="`${totalCount > 0 ? totalCount + ' 个项目' : (photos.length + (hasMore ? '+' : '')) + ' 个项目'}`"
    :loading="loading && photos.length === 0"
    :photos="photos"
    :has-more="hasMore"
    :timeline-items="timeline"
    :timeline-stats="{ timeline }"
    @back="router.back()"
    @load-more="loadMore"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { classificationService } from '@/api/classification'
import UnifiedPhotoPage from '@/components/UnifiedPhotoPage.vue'
import { mapPhotoToImage } from '@/stores/photoStore'
import type { AlbumImage } from '@/types/album'

const route = useRoute()
const router = useRouter()
const name = route.params.name as string

const loading = ref(false)
const photos = ref<AlbumImage[]>([])
const timeline = ref<any[]>([])
const skip = ref(0)
const hasMore = ref(true)
const totalCount = ref(0)

const title = computed(() => name)

const calculateTimelineStats = (photos: AlbumImage[]) => {
  const stats = new Map<string, { year: number, month: number, day: number, count: number }>()

  photos.forEach(photo => {
    const date = new Date(photo.timestamp)
    const year = date.getFullYear()
    const month = date.getMonth() + 1
    const day = date.getDate()
    const key = `${year}-${month}-${day}`

    if (!stats.has(key)) {
      stats.set(key, { year, month, day, count: 0 })
    }
    stats.get(key)!.count++
  })

  timeline.value = Array.from(stats.values()).sort((a, b) => {
    if (a.year !== b.year) return b.year - a.year
    if (a.month !== b.month) return b.month - a.month
    return b.day - a.day
  })
}

const loadMore = async () => {
  if (loading.value || !hasMore.value) return
  loading.value = true
  console.log('Loading more photos for tag:', name, 'skip:', skip.value)
  try {
    const limit = 500
    let hasNext = true

    while (hasNext) {
      const rawPhotos = await classificationService.getTagPhotos(name, skip.value, limit)

      if (rawPhotos.length < limit) {
        hasMore.value = false
        hasNext = false
      }

      const newPhotos = rawPhotos.map(mapPhotoToImage)
      photos.value.push(...newPhotos)
      skip.value += limit

      calculateTimelineStats(photos.value)
    }
  } catch (e) {
    console.error('Failed to load tag photos:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadMore()
})
</script>
