<template>
  <div class="location-list p-6 min-h-screen bg-gray-50 dark:bg-gray-950">
    <!-- Header -->
    <div class="mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div class="flex items-center gap-3 w-full md:w-auto bg-white/80 dark:bg-gray-900/80 backdrop-blur-md px-3 py-1.5 rounded-full shadow-sm border border-gray-200/50 dark:border-gray-700/50">
        <button @click="router.back()" class="p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors bg-white dark:bg-gray-900">
          <ArrowLeft class="w-5 h-5 text-gray-600 dark:text-gray-300" />
        </button>
        <h1 class="text-2xl font-bold text-gray-800 dark:text-white">位置相册</h1>
      </div>

      <!-- Toggle -->
      <div class="bg-gray-200 dark:bg-gray-800 p-1 rounded-lg flex">
        <button
          @click="changeLevel('city')"
          :class="['px-4 py-1.5 rounded-md text-sm font-medium transition-all bg-white dark:bg-gray-700', level === 'city' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700']"
        >
          城市
        </button>
        <button
          @click="changeLevel('province')"
          :class="['px-4 py-1.5 rounded-md text-sm font-medium transition-all bg-white dark:bg-gray-700', level === 'province' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700']"
        >
          省份
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
      <div v-for="i in 10" :key="i" class="flex flex-col">
        <div class="w-full aspect-square bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse"></div>
        <div class="mt-3 h-4 bg-gray-200 dark:bg-gray-800 rounded w-2/3 animate-pulse"></div>
        <div class="mt-1 h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/3 animate-pulse"></div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="locations.length === 0" class="flex flex-col items-center justify-center h-[60vh] text-gray-500">
      <div class="p-6 rounded-full bg-gray-100 dark:bg-gray-900 mb-4">
        <MapPin class="w-12 h-12 opacity-20" />
      </div>
      <p class="text-lg font-medium">暂无位置信息</p>
    </div>

    <!-- Content Grid -->
    <div v-else class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-12 gap-6">
      <div
        v-for="loc in locations"
        :key="loc.name"
        class="group cursor-pointer flex flex-col"
        @click="goToLocation(loc)"
      >
        <div class="relative w-full aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 shadow-sm group-hover:shadow-md transition-all duration-300">
           <img
             v-if="loc.cover"
             :src="mapPhotoToImage(loc.cover).thumbnail"
             class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
             loading="lazy"
           />
           <div v-else class="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-600">
             <MapPin class="w-12 h-12" />
           </div>
           
           <!-- Overlay -->
           <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors"></div>
        </div>

        <div class="mt-2.5 px-1">
          <h3 class="font-semibold text-gray-900 dark:text-white truncate" :title="loc.name">
            {{ loc.name }}
          </h3>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {{ loc.count }} 个项目
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { locationService } from '@/api/location'
import { mapPhotoToImage } from '@/stores/photoStore'
import type { Location } from '@/types/location'
import { ArrowLeft, MapPin } from 'lucide-vue-next'

const router = useRouter()
const level = ref<'city' | 'province'>('city')
const locations = ref<Location[]>([])
const loading = ref(true)

const fetchLocations = async () => {
  loading.value = true
  try {
    locations.value = await locationService.getLocations(level.value)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const changeLevel = (newLevel: 'city' | 'province') => {
  if (level.value === newLevel) return
  level.value = newLevel
  fetchLocations()
}

const goToLocation = (loc: Location) => {
  router.push({
    name: 'LocationDetail',
    params: { name: loc.name },
    query: { level: level.value }
  })
}

onMounted(() => {
  fetchLocations()
})
</script>
