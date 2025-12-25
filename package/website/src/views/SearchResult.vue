<template>
  <div class="min-h-screen bg-white dark:bg-gray-950 pb-8">
    <!-- Header -->
    <div class="sticky top-0 z-30 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
      <div class="max-w-7xl mx-auto px-4 py-3 flex items-center gap-4">
        <button 
          @click="router.back()" 
          class="p-2 -ml-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <ArrowLeft class="w-5 h-5 text-gray-600 dark:text-gray-300" />
        </button>
        <div>
          <h1 class="text-lg font-bold text-gray-900 dark:text-white leading-tight">
            {{ title }}
          </h1>
          <p class="text-xs text-gray-500">{{ subtitle }}</p>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="max-w-7xl mx-auto px-4 py-6">
      <!-- Loading State (Initial) -->
      <div v-if="loading && photos.length === 0" class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10 gap-4">
        <div v-for="i in 20" :key="i" class="aspect-square bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse"></div>
      </div>

      <!-- Empty State -->
      <div v-else-if="!loading && photos.length === 0" class="flex flex-col items-center justify-center py-20 text-gray-500">
        <div class="p-6 rounded-full bg-gray-100 dark:bg-gray-900 mb-4">
          <Search class="w-12 h-12 opacity-20" />
        </div>
        <p class="text-lg font-medium">未找到相关照片</p>
        <p class="text-sm mt-2">尝试更换搜索关键词</p>
      </div>

      <!-- Photo Grid -->
      <div v-else class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10 gap-4">
        <div 
          v-for="(photo, index) in photos" 
          :key="photo.id" 
          class="group relative aspect-square bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden cursor-pointer"
          @click="openLightbox(index)"
        >
          <img 
            :src="photo.thumbnail" 
            :alt="photo.id"
            loading="lazy"
            class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          />
          <!-- Hover Overlay -->
          <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300"></div>
        </div>
      </div>

      <!-- Load More Sentinel / Loading Indicator -->
      <div 
        ref="loadMoreTrigger" 
        class="h-20 flex items-center justify-center mt-8"
        v-if="hasMore && photos.length > 0"
      >
        <div v-if="loading" class="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    </div>

    <!-- Lightbox -->
    <PhotoLightbox
      :visible="showLightbox"
      :image="photos[lightboxIndex]"
      :has-prev="lightboxIndex > 0"
      :has-next="lightboxIndex < photos.length - 1"
      @close="closeLightbox"
      @prev="prevPhoto"
      @next="nextPhoto"
      @delete="handlePhotoDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Search } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import searchService from '@/api/search'
import { albumService } from '@/api/album'
import { mapPhotoToImage } from '@/stores/photoStore'
import PhotoLightbox from '@/components/PhotoLightbox.vue'
import type { AlbumImage } from '@/types/album'

const route = useRoute()
const router = useRouter()

const query = computed(() => route.query.q as string || '')
const title = computed(() => query.value ? `搜索: ${query.value}` : '搜索结果')

const loading = ref(false)
const photos = ref<AlbumImage[]>([])
const skip = ref(0)
const limit = 50 // Increased from 3 to 50 for grid view
const hasMore = ref(true)
const loadMoreTrigger = ref<HTMLElement | null>(null)

// Lightbox State
const showLightbox = ref(false)
const lightboxIndex = ref(0)

const openLightbox = (index: number) => {
  lightboxIndex.value = index
  showLightbox.value = true
}

const closeLightbox = () => {
  showLightbox.value = false
}

const prevPhoto = () => {
  if (lightboxIndex.value > 0) {
    lightboxIndex.value--
  }
}

const nextPhoto = () => {
  if (lightboxIndex.value < photos.value.length - 1) {
    lightboxIndex.value++
  }
}

const handlePhotoDelete = async (id: string) => {
  try {
    await albumService.deletePhoto(id)
    photos.value = photos.value.filter(p => p.id !== id)
    ElMessage.success('删除成功')
    
    if (photos.value.length === 0) {
      closeLightbox()
    } else {
      if (lightboxIndex.value >= photos.value.length) {
        lightboxIndex.value = photos.value.length - 1
      }
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('删除失败')
  }
}

const subtitle = computed(() => {
  if (loading.value && photos.value.length === 0) return '搜索中...'
  return `${photos.value.length}${hasMore.value ? '+' : ''} 个结果`
})

// Intersection Observer for Infinite Scroll
let observer: IntersectionObserver | null = null

const setupObserver = () => {
  if (observer) observer.disconnect()
  
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && hasMore.value && !loading.value) {
      loadMore()
    }
  }, {
    rootMargin: '200px'
  })

  if (loadMoreTrigger.value) {
    observer.observe(loadMoreTrigger.value)
  }
}

watch(loadMoreTrigger, () => {
  if (loadMoreTrigger.value) setupObserver()
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})

const performSearch = async (isLoadMore = false) => {
  if (!query.value) return
  if (loading.value) return
  
  if (!isLoadMore) {
    photos.value = []
    skip.value = 0
    hasMore.value = true
  }
  
  loading.value = true
  try {
    const res = await searchService.searchByText({
      text: query.value,
      limit: limit,
      skip: skip.value,
      threshold: 0.2
    })

    const newPhotos = res.map(item => mapPhotoToImage(item.photo))

    if (newPhotos.length < limit) {
      hasMore.value = false
    }

    if (isLoadMore) {
      photos.value.push(...newPhotos)
    } else {
      photos.value = newPhotos
    }

    skip.value += limit
  } catch (e) {
    console.error('Search failed:', e)
  } finally {
    loading.value = false
    // Re-setup observer after DOM update if needed, but watch handles it usually
  }
}

const loadMore = () => {
  if (hasMore.value) {
    performSearch(true)
  }
}

watch(() => route.query.q, () => {
  performSearch()
}, { immediate: true })

</script>
