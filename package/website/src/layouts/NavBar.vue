<template>
  <header class="header bg-light-bg dark:bg-gray-900 transition-colors duration-300">
    <div class="logo-wrapper destop-only">
      <img src="@/assets/logo.svg" alt="Logo" class="logo" />
      <h1 class="site-title text-gray-800 dark:text-gray-100">行影集</h1>
    </div>

    <nav class="nav-bg bg-light-bg/80 dark:bg-gray-800/80 backdrop-blur-md shadow-md rounded-full px-4 py-1 flex justify-center items-center space-x-2 fixed left-1/2 transform -translate-x-1/2 transition-colors duration-300">
      <RouterLink
        v-for="(item, index) in navLinks"
        :key="index"
        :to="item.href"
        class="relative px-3 py-1.5 text-sm text-gray-700 dark:text-gray-200 hover:text-primary-500 dark:hover:text-primary-500 transition-colors flex items-center gap-1.5"
        active-class="font-medium text-primary-600 dark:text-primary-400"
      >
        <ImageIcon v-if="item.icon" class="w-4 h-4" />
        {{ item.label }}
        <span
          v-if="$route.path === item.href || ($route.path.startsWith(item.href) && item.href !== '/')"
          class="absolute bottom-0 left-0 w-full h-0.5 bg-primary-500 rounded-full"
        ></span>
      </RouterLink>

      <div class="relative transition-all duration-300 ease-in-out" :class="[isSearchExpanded ? 'w-48' : 'w-8']">
        <button 
          @click="toggleSearch"
          class="absolute left-0 top-1/2 -translate-y-1/2 p-1.5 text-gray-700 dark:text-gray-200 hover:text-primary-500 transition-colors z-10 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800"
          :class="{'bg-transparent hover:bg-transparent dark:hover:bg-transparent': isSearchExpanded}"
          title="搜索"
        >
          <Search class="w-4 h-4" />
        </button>
        
        <input
          v-show="isSearchExpanded"
          ref="searchInputRef"
          v-model="searchText"
          @keydown.enter="handleSearch"
          @blur="handleBlur"
          type="text"
          placeholder="搜索"
          class="w-full pl-9 pr-7 py-1 text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded-full focus:outline-none focus:border-primary-500 text-gray-700 dark:text-gray-200"
        />
        
        <button 
          v-if="isSearchExpanded && searchText"
          @click="clearSearch"
          class="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          <X class="w-3 h-3" />
        </button>
      </div>

      <!-- More Menu -->
      <div class="relative" ref="moreMenuRef">
        <button
          @click="showMoreMenu = !showMoreMenu"
          class="px-2 py-1 text-gray-700 dark:text-gray-200 hover:text-primary-500 transition-colors flex items-center gap-1 text-sm font-medium"
          :class="{ 'text-primary-500': showMoreMenu || moreLinks.some(l => $route.path.startsWith(l.href)) }"
        >
          更多 <ChevronDown class="w-3 h-3 transition-transform duration-200" :class="{ 'rotate-180': showMoreMenu }" />
        </button>

        <div
          v-if="showMoreMenu"
          class="absolute top-10 left-1/2 transform -translate-x-1/2 w-32 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl p-1 z-50 animate-in fade-in zoom-in-95 duration-200 overflow-hidden"
        >
          <RouterLink
            v-for="link in moreLinks"
            :key="link.href"
            :to="link.href"
            @click="showMoreMenu = false"
            class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors text-center"
            active-class="bg-primary-50 text-primary-600 dark:bg-slate-700 dark:text-primary-400 font-medium"
          >
            {{ link.label }}
          </RouterLink>
        </div>
      </div>
    </nav>
  </header>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import {
  Image as ImageIcon, Images, MoreHorizontal, ChevronDown, Search, X
} from 'lucide-vue-next';
import { useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { usePhotoStore } from '@/stores/photoStore'

// 导航数据
const navLinks = [
  { label: '首页', href: '/' },
  { label: '照片', href: '/photos' },
  { label: '相册', href: '/album'},
]

const moreLinks = [
  { label: '车票', href: '/ticket' },
  { label: '统计', href: '/statistics' },
  { label: '设置', href: '/settings' },
  { label: '关于', href: '/about' },
]

const showMoreMenu = ref(false);
const moreMenuRef = ref(null);

const router = useRouter();
const store = usePhotoStore();
const searchText = ref('');
const isSearchExpanded = ref(false);
const searchInputRef = ref(null);

// Sync with store
watch(() => store.currentContext, (ctx) => {
  if (ctx.type === 'search' && ctx.id) {
    searchText.value = ctx.id;
    isSearchExpanded.value = true;
  } else if (ctx.type !== 'search') {
    searchText.value = '';
    isSearchExpanded.value = false;
  }
});

const toggleSearch = () => {
  if (isSearchExpanded.value && searchText.value) {
    handleSearch();
  } else {
    isSearchExpanded.value = !isSearchExpanded.value;
    if (isSearchExpanded.value) {
      nextTick(() => {
        searchInputRef.value?.focus();
      });
    }
  }
};

const handleBlur = () => {
  // Give some time for other interactions (like clear button)
  setTimeout(() => {
    if (!searchText.value) {
      isSearchExpanded.value = false;
    }
  }, 200);
};

const handleSearch = () => {
  if (searchText.value.trim()) {
    router.push({ path: '/search', query: { q: searchText.value } });
  }
};

const clearSearch = () => {
  searchText.value = '';
  store.loadPhotos(true); // Reset to default
  searchInputRef.value?.focus();
};

onClickOutside(moreMenuRef, () => {
  showMoreMenu.value = false;
});

</script>

<style scoped>
@tailwind base;
@tailwind components;
@tailwind utilities;


.header {
  position: sticky;
  width: 100vw;
  top: 0;
  z-index: 100;
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin: 0 auto;
  padding: 0 1rem;
  height: 60px;
}

.nav-bg {
  height: 40px;
}

.logo-wrapper {
  display: flex;
  align-items: center;
}

.logo {
  height: 32px;
  width: auto;
}

.site-title {
  font: 1.5em sans-serif;
  margin-left: 10px;
  padding-left: 0;
  font-weight: bold;
}

@media (max-width: 767px) {
  .destop-only {
    display: none;
  }
  .nav-bg {
    width: 90vw;
  }
}

/* 深色模式下的额外样式调整 */
.dark .header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
</style>