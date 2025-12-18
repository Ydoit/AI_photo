<template>
  <UnifiedPhotoPage
    :title="identity?.identity_name || ''"
    :subtitle="`${images.length} 张`"
    :loading="loading"
    :loading-title="!identity"
    :photos="images"
    :timeline-items="timeline"
    :timeline-stats="{ timeline }"
    :allow-upload="false"
    delete-label="从人物中移除"
    :pending-remove-ids="pendingRemoveIds"
    confirm-remove
    @back="router.back()"
    @confirm-delete="handleConfirmDelete"
    @set-cover="handleSetCover"
  >
    <template #batch-actions="{ selectedIds, clearSelection }">
      <button
          v-if="selectedIds.size === 1"
          @click="handleSetCover(Array.from(selectedIds)); clearSelection()"
          class="bg-transparent flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors font-medium"
          title="设为封面"
      >
          <FolderIcon class="w-5 h-5" />
      </button>
    </template>
  </UnifiedPhotoPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { faceApi, type FaceIdentity, type CoverPhotoInfo } from '@/api/face'
import UnifiedPhotoPage from '@/components/UnifiedPhotoPage.vue'
import { Folder as FolderIcon } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import { usePhotoStore, type AlbumImage } from '@/stores/photoStore'

const photoStore = usePhotoStore()

const route = useRoute()
const router = useRouter()
const identityId = route.params.id as string

// State
const identity = ref<FaceIdentity | null>(null)
const images = ref<AlbumImage[]>([])
const loading = ref(true)
const timeline = ref<any[]>([])
const pendingRemoveIds = ref(new Set<string>())

const fetchIdentity = async () => {
  try {
    const identities = await faceApi.listIdentities(1, 1000)
    identity.value = identities.find(i => i.id === identityId) || null
  } catch (e) {
    console.error('Failed to fetch identity info', e)
  }
}

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

const fetchAllPhotos = async () => {
  loading.value = true
  images.value = []

  try {
    let page = 1
    const limit = 100
    let hasNext = true

    while (hasNext) {
      const photos = await faceApi.getIdentityPhotos(identityId, page, limit)
      if (photos.length === 0) break

      const newImages = photos.map(photoStore.mapPhotoToImage)
      images.value.push(...newImages)

      if (photos.length < limit) hasNext = false
      page++
    }

    // Sort by time desc
    images.value.sort((a, b) => b.timestamp - a.timestamp)

    // Calculate timeline
    calculateTimelineStats(images.value)

  } catch (e) {
    console.error(e)
    ElMessage.error('加载照片失败')
  } finally {
    loading.value = false
  }
}

const handleConfirmDelete = async (ids: string[], callback: (success: boolean) => void) => {
  try {
    ids.forEach(id => pendingRemoveIds.value.add(id))

    await faceApi.removePhotos(identityId, ids)

    // Remove from local list
    images.value = images.value.filter(img => !ids.includes(img.id))
    calculateTimelineStats(images.value)
    ElMessage.success('移除成功')

    callback(true)

  } catch (e) {
    ElMessage.error('移除失败')
    callback(false)
  } finally {
    ids.forEach(id => pendingRemoveIds.value.delete(id))
  }
}

const handleSetCover = async (ids: string[]) => {
  if (!ids.length) return
  const photoId = ids[0]
  try {
    await faceApi.setCover(identityId, photoId)
    ElMessage.success('已设为封面')
    // Update local identity cover if needed
    fetchIdentity() // Refresh identity info
  } catch (e) {
    ElMessage.error('设置封面失败')
  }
}

onMounted(() => {
  fetchIdentity()
  fetchAllPhotos()
})
</script>

<style scoped>
/* Scoped styles */
</style>
