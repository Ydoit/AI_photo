<template>
  <div class="space-y-10 animate-in fade-in duration-500">
    <!-- City Albums -->
    <section v-if="cityAlbums.length > 0">
      <div class="flex items-center gap-2 mb-4 px-1">
        <MapPin class="w-5 h-5 text-primary-500" />
        <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">城市足迹</h2>
        <span class="text-xs text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">{{ cityAlbums.length }}</span>
      </div>
      
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
        <div
          v-for="album in cityAlbums"
          :key="album.id"
          class="group cursor-pointer"
          @click="navigateToAlbum(album.id)"
        >
          <div class="aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 relative shadow-sm group-hover:shadow-md transition-all duration-300 mb-3 border border-gray-100 dark:border-gray-800">
            <img
              :src="album.cover"
              class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
              loading="lazy"
            />
            <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors"></div>
            <div class="absolute top-2 right-2">
              <span class="bg-black/50 backdrop-blur-sm text-white text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1">
                <MapPin class="w-3 h-3 text-yellow-400" /> {{ album.title }}
              </span>
            </div>
          </div>
          <h3 class="font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-primary-500 transition-colors">{{ album.title }}</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ album.count }} 张照片</p>
        </div>
      </div>
    </section>

    <!-- Year Albums -->
    <section v-if="yearAlbums.length > 0">
      <div class="flex items-center gap-2 mb-4 px-1">
        <CalendarDays class="w-5 h-5 text-primary-500" />
        <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">时光回忆</h2>
        <span class="text-xs text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">{{ yearAlbums.length }}</span>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
        <div
          v-for="album in yearAlbums"
          :key="album.id"
          class="group cursor-pointer"
          @click="navigateToAlbum(album.id)"
        >
          <div class="aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 relative shadow-sm group-hover:shadow-md transition-all duration-300 mb-3 border border-gray-100 dark:border-gray-800">
            <img
              :src="album.cover"
              class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
              loading="lazy"
            />
            <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors"></div>
            <div class="absolute top-2 right-2">
              <span class="bg-black/50 backdrop-blur-sm text-white text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1">
                <CalendarDays class="w-3 h-3 text-purple-400" /> {{ album.title }}
              </span>
            </div>
          </div>
          <h3 class="font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-primary-500 transition-colors">{{ album.title }}</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ album.count }} 张照片</p>
        </div>
      </div>
    </section>

    <!-- Category Albums -->
    <section v-if="categoryAlbums.length > 0">
      <div class="flex items-center gap-2 mb-4 px-1">
        <Tags class="w-5 h-5 text-primary-500" />
        <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">智能分类</h2>
        <span class="text-xs text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">{{ categoryAlbums.length }}</span>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
        <div
          v-for="album in categoryAlbums"
          :key="album.id"
          class="group cursor-pointer"
          @click="navigateToAlbum(album.id)"
        >
          <div class="aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 relative shadow-sm group-hover:shadow-md transition-all duration-300 mb-3 border border-gray-100 dark:border-gray-800">
            <img
              :src="album.cover"
              class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
              loading="lazy"
            />
            <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors"></div>
            <div class="absolute top-2 right-2">
              <span class="bg-black/50 backdrop-blur-sm text-white text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1">
                <Sparkles class="w-3 h-3 text-blue-400" /> {{ album.title }}
              </span>
            </div>
          </div>
          <h3 class="font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-primary-500 transition-colors">{{ album.title }}</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ album.count }} 张照片</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAlbumStore } from '@/stores/albumStore'
import { MapPin, Tags, Sparkles, CalendarDays } from 'lucide-vue-next'

const router = useRouter()
const store = useAlbumStore()

const cityAlbums = computed(() => store.conditionalAlbums.filter(a => a.id.startsWith('city-')))
const yearAlbums = computed(() => store.conditionalAlbums.filter(a => a.id.startsWith('year-')))
const categoryAlbums = computed(() => store.conditionalAlbums.filter(a => a.id.startsWith('cat-')))

const navigateToAlbum = (id: string) => {
  router.push(`/album/${id}`)
}
</script>
