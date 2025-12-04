<template>
  <div 
    :class="[isDarkMode ? 'dark' : '']"
    class="min-h-screen font-sans transition-colors duration-300 bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-200"
  >
    <nav class="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-30 shadow-sm h-16 transition-colors duration-300">
      <div class="max-w-[1400px] mx-auto px-4 h-full flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center border border-primary-500 bg-primary-50 dark:bg-slate-700/50 transition-colors">
            <TrainFront class="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
          <span class="text-xl font-light tracking-wide text-slate-800 dark:text-white hidden sm:block">车票收藏夹</span>
        </div>

        <div class="hidden lg:block w-1/3">
          <div class="relative group">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-primary-500 transition-colors" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索车次 / 出发地 / 目的地 / 乘车人"
              class="w-full pl-10 pr-4 py-2 bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-200 dark:focus:ring-primary-900 transition-all text-sm dark:text-white dark:placeholder-slate-400"
              @input="handleSearchInput"
            />
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button
            @click="openTicketModal()"
            class="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md transition-all active:scale-95 shadow-md shadow-primary-200 dark:shadow-none"
          >
            <Plus class="w-4 h-4" />
            <span class="hidden sm:inline text-sm font-medium">新增</span>
          </button>
          <div class="w-9 h-9 rounded-full bg-slate-200 overflow-hidden border border-white dark:border-slate-600 shadow-sm cursor-pointer">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Traveler" alt="Avatar" class="w-full h-full object-cover" />
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-[1400px] mx-auto px-4 py-4">
      <div class="flex flex-col xl:flex-row gap-6">
        <aside class="w-full xl:w-[320px] shrink-0 space-y-4">
          <div class="lg:hidden mb-4">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索车票 / 乘车人..."
              class="w-full px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white"
              @input="handleSearchInput"
            />
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-3 xl:grid-cols-1 gap-4">
            <StatsCard 
              label="点击查看足迹地图" 
              :icon="MapPin" 
              clickable 
              @click="showCityModal = true"
            >
              <template #value>
                <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ uniqueCities.length }}</span>
                <span class="text-xs text-slate-500 dark:text-slate-400">座城市</span>
              </template>
            </StatsCard>

            <StatsCard label="累计旅程时长" :icon="Clock">
              <template #value>
                <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ totalDuration.hours }}<span class="text-sm font-normal text-slate-500 ml-0.5">h</span></span>
                <span class="text-lg font-semibold text-slate-600 dark:text-slate-300">{{ totalDuration.minutes }}<span class="text-xs font-normal text-slate-500 ml-0.5">m</span></span>
              </template>
            </StatsCard>

            <StatsCard :label="`绕赤道 ${(totalDistance / 40075).toFixed(2)} 圈`" :icon="Route">
              <template #value>
                <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ totalDistance.toLocaleString() }}</span>
                <span class="text-xs text-slate-500 dark:text-slate-400">km</span>
              </template>
            </StatsCard>
          </div>

          <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm">
            <h3 class="text-sm font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
              <User class="w-4 h-4 text-primary-600 dark:text-primary-400" />
              乘车人筛选
            </h3>
            <div class="flex flex-wrap gap-2 max-h-[200px] overflow-y-auto">
              <span 
                v-for="passenger in uniquePassengers" 
                :key="passenger"
                @click="filterByPassenger(passenger)"
                class="px-3 py-1.5 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-full text-sm hover:bg-primary-50 hover:text-primary-600 hover:border-primary-200 dark:hover:bg-slate-600 dark:hover:text-primary-400 border border-transparent cursor-pointer transition-colors"
                :class="selectedPassenger === passenger ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400' : ''"
              >
                {{ passenger }}
              </span>
              <span 
                @click="clearPassengerFilter()"
                class="px-3 py-1.5 bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded-full text-sm hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-600 cursor-pointer transition-colors"
              >
                全部
              </span>
            </div>
          </div>
        </aside>

        <section class="flex-1 min-w-0">
          <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4 mb-6 flex flex-wrap gap-4 justify-between items-center shadow-sm transition-colors">
            <div class="flex items-center gap-3 w-full sm:w-auto">
              <div class="relative w-full sm:w-40">
                <select
                  v-model="filterType"
                  class="w-full appearance-none bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-sm rounded-md px-3 py-2 pr-8 focus:border-primary-500 dark:text-white outline-none cursor-pointer"
                  @change="fetchTickets()"
                >
                  v-model="filterType"
                  class="w-full appearance-none bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-sm rounded-md px-3 py-2 pr-8 focus:border-primary-500 dark:text-white outline-none cursor-pointer"
                  @change="fetchTickets"
                >
                  <option value="all">全部车票</option>
                  <option value="highspeed">高铁/动车</option>
                  <option value="normal">普速列车</option>
                </select>
                <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>

              <div class="hidden sm:flex bg-slate-100 dark:bg-slate-700 rounded-md p-1 flex-wrap gap-1">
                <button 
                  v-for="type in sortOptions"
                  :key="type.value"
                  @click="changeSortType(type.value)"
                  :class="['px-3 py-1 text-xs font-medium rounded transition-all', sortType === type.value ? 'bg-white dark:bg-slate-600 text-primary-600 dark:text-primary-400 shadow-sm' : 'text-slate-500 dark:text-slate-700 hover:text-slate-700 dark:hover:text-slate-800']"
                >
                  {{ type.label }}
                </button>
              </div>
            </div>

            <div class="flex items-center gap-3 w-full sm:w-auto justify-end">
              <div class="bg-slate-100 dark:bg-slate-700 p-1 rounded-md flex gap-1">
                <button 
                  @click="fetchTickets(true)"
                  class="p-1.5 rounded transition-all text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-white dark:hover:bg-slate-600 hover:shadow-sm"
                  title="刷新数据"
                  :disabled="loading"
                >
                  <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
                </button>
                <div class="w-px bg-slate-300 dark:bg-slate-600 my-1 mx-0.5"></div>
                <button 
                  @click="viewMode = 'timeline'"
                  :class="['p-1.5 rounded transition-all', viewMode === 'timeline' ? 'bg-white dark:bg-slate-600 shadow-sm text-primary-600 dark:text-primary-400' : 'text-slate-500 hover:text-slate-600 dark:hover:text-slate-300']"
                  title="时间轴视图"
                >
                  <ListTree class="w-4 h-4" />
                </button>
                <button 
                  @click="viewMode = 'grid'"
                  :class="['p-1.5 rounded transition-all', viewMode === 'grid' ? 'bg-white dark:bg-slate-600 shadow-sm text-primary-600 dark:text-primary-400' : 'text-slate-500 hover:text-slate-600 dark:hover:text-slate-300']"
                  title="卡片视图"
                >
                  <LayoutGrid class="w-4 h-4" />
                </button>
              </div>

              <div class="h-6 w-px bg-slate-200 dark:bg-slate-700 mx-1 hidden sm:block"></div>

              <button 
                :disabled="selectedTickets.length === 0 || loading"
                @click="batchDelete"
                :class="['flex items-center gap-2 text-sm px-4 py-2 rounded-md transition-colors', selectedTickets.length > 0 ? 'text-red-600 bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50' : 'text-slate-300 dark:text-slate-600 bg-slate-50 dark:bg-slate-700 cursor-not-allowed']"
              >
                <Trash2 class="w-4 h-4" />
                <span class="hidden sm:inline">删除选中</span>
                <span v-if="selectedTickets.length > 0">({{ selectedTickets.length }})</span>
              </button>
            </div>
          </div>

          <div v-if="loading" class="flex justify-center items-center py-20">
            <div class="w-10 h-10 border-4 border-slate-200 dark:border-slate-700 border-t-primary-500 rounded-full animate-spin"></div>
          </div>

          <div v-else-if="error" class="flex flex-col items-center justify-center py-20 text-center text-red-500">
            <X class="w-12 h-12 mb-4" />
            <h3 class="text-xl font-medium mb-2">数据加载失败</h3>
            <p class="mb-4">{{ error }}</p>
            <button @click="fetchTickets()" class="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors">重试</button>
          </div>

          <div v-else-if="filteredTickets.length > 0">
            <TicketTimeline
              v-if="viewMode === 'timeline'"
              :tickets="filteredTickets"
              :selected-ticket-ids="selectedTickets"
              :current-theme="currentTheme"
              @toggle-select="toggleSelect"
              @edit="openTicketModal"
              @delete="confirmDelete"
            />
            <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TicketCard
                v-for="ticket in filteredTickets"
                :key="ticket.id"
                :ticket="ticket"
                :selected-ticket-ids="selectedTickets"
                :current-theme="currentTheme"
                @toggle-select="toggleSelect"
                @edit="openTicketModal"
                @delete="confirmDelete"
              />
            </div>
          </div>

          <div v-else class="flex flex-col items-center justify-center py-20 text-center">
            <div class="w-24 h-24 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
              <TrainFront class="w-12 h-12 text-slate-300 dark:text-slate-600" />
            </div>
            <h3 class="text-xl font-medium text-slate-400 mb-2">暂无收藏车票</h3>
            <button @click="openTicketModal()" class="text-primary-500 hover:underline">点击新增添加你的第一张车票</button>
          </div>
        </section>
      </div>
    </main>

    <TicketFormModal
      :is-open="isModalOpen"
      :is-editing="isEditing"
      :initial-data="currentTicket"
      :current-theme="currentTheme"
      :saving="saving"
      @save="handleModalSave"
      @cancel="closeModal"
    />

    <Transition name="fade">
      <div v-if="showCityModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" @click="showCityModal = false"></div>
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-lg relative z-10 p-6">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
              <MapPin class="w-5 h-5 text-primary-600 dark:text-primary-400" />
              足迹地图
            </h2>
            <button @click="showCityModal = false"><X class="w-5 h-5 text-slate-400" /></button>
          </div>
          
          <div class="flex flex-wrap gap-2 max-h-[60vh] overflow-y-auto">
            <span 
              v-for="city in uniqueCities" 
              :key="city"
              @click="filterByCity(city)"
              class="px-3 py-1.5 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-full text-sm hover:bg-primary-50 hover:text-primary-600 hover:border-primary-200 dark:hover:bg-slate-600 dark:hover:text-primary-400 border border-transparent cursor-pointer transition-colors"
            >
              {{ city }}
            </span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { 
  TrainFront, Search, Plus, MapPin, Clock, Route,
  ChevronDown, Trash2, X, User, RefreshCw
} from 'lucide-vue-next';
import { ElMessage } from 'element-plus';
import { ListTree, LayoutGrid } from 'lucide-vue-next'; // 引入图标
import TicketTimeline from '@/components/TicketTimeline.vue'; // 引入新组件
import { storeToRefs } from 'pinia';
import { useTicketStore } from '@/stores/ticketStore';

// 导入自定义类型、服务和组件
import type {
  TicketFrontend,
  TicketFormData,
  SortType,
  FilterType
} from '@/types/ticket';
import { ticketService } from '@/api/ticketService';
import { formatTicketToFrontend, formatFormToBackend, debounce } from '@/utils/ticketFormatters';
import { injectTheme } from '@/composables/useTheme';

// 组件
import TicketFormModal from '@/components/TicketFormModal.vue';
import TicketCard from '@/components/TicketCard.vue';
import StatsCard from '@/components/StatsCard.vue'; // 新组件

const { isDarkMode, currentTheme } = injectTheme();
const ticketStore = useTicketStore();

// --- 状态定义 ---
// 使用 storeToRefs 保持响应性
const {
  tickets,
  searchQuery,
  filterType,
  sortType,
  selectedPassenger,
  viewMode,
  loading,
  error
} = storeToRefs(ticketStore);

const selectedTickets = ref<number[]>([]);
const isModalOpen = ref(false);
const isEditing = ref(false);
const showCityModal = ref(false);
const saving = ref(false);
// 初始编辑对象，使用 Partial 或特定类型
const currentTicket = ref<Partial<TicketFormData>>({});

// 排序选项配置
const sortOptions: { label: string; value: SortType }[] = [
  { label: '日期', value: 'date' },
  { label: '里程', value: 'distance' },
  { label: '时长', value: 'duration' },
  { label: '票价', value: 'price' }
];

// --- 搜索防抖 ---
// 使用我们封装的带类型的防抖函数
const debouncedFetchTickets = debounce(() => {
  // 搜索时触发 store 的 fetch，或者因为 store 中 tickets 已经是全量数据，
  // 其实搜索主要是在前端过滤，所以这里可能不需要重新请求后端，
  // 除非后端支持搜索参数且我们希望服务端过滤。
  // 原逻辑中 fetchTickets 会带上 params，所以这里保留调用
  fetchTickets();
}, 500);

const handleSearchInput = () => {
  debouncedFetchTickets();
};

// --- 生命周期 ---
onMounted(() => {
  // 组件加载时获取数据（会自动检查缓存）
  fetchTickets();
});

onUnmounted(() => {
  debouncedFetchTickets.cancel?.();
});

// --- 计算属性 ---

// 转换后的前端数据列表
const frontendTickets = computed<TicketFrontend[]>(() => {
  return tickets.value.map(formatTicketToFrontend);
});

const filteredTickets = computed<TicketFrontend[]>(() => {
  let res = [...frontendTickets.value];
  // 1. 本地搜索筛选
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    res = res.filter(t => 
      t.trainCode.toLowerCase().includes(q) || 
      t.from.toLowerCase().includes(q) || 
      t.to.toLowerCase().includes(q) ||
      t.name.toLowerCase().includes(q)
    );
  }

  // 2. 列车类型筛选
  if (filterType.value !== 'all') {
    res = res.filter(t => {
      const firstChar = t.trainCode.charAt(0).toUpperCase();
      const isHighSpeed = ['G', 'D', 'C'].includes(firstChar);
      return filterType.value === 'highspeed' ? isHighSpeed : !isHighSpeed;
    });
  }

  // 3. 乘车人筛选 (本地)
  if (selectedPassenger.value) {
    res = res.filter(t => t.name === selectedPassenger.value);
  }

  // 4. 多维度排序
  return res.sort((a, b) => {
    switch (sortType.value) {
      case 'date':
        return new Date(b.dateTime).getTime() - new Date(a.dateTime).getTime();
      case 'distance':
        return b.distance - a.distance;
      case 'duration':
        return b.totalRunningTime - a.totalRunningTime;
      case 'price':
        return b.price - a.price;
      default:
        return 0;
    }
  });
});

const uniqueCities = computed(() => {
  const cities = new Set<string>();
  tickets.value.forEach(t => {
    cities.add(t.departure_station);
    cities.add(t.arrival_station);
  });
  return Array.from(cities).sort();
});

const uniquePassengers = computed(() => {
  const passengers = new Set<string>();
  tickets.value.forEach(t => {
    if (t.name) passengers.add(t.name);
  });
  return Array.from(passengers).sort();
});

const totalDistance = computed(() => 
  tickets.value.reduce((sum, t) => sum + (t.total_mileage || 0), 0)
);

const totalDuration = computed(() => {
  const totalMinutes = tickets.value.reduce((sum, t) => sum + (t.total_running_time || 0), 0);
  return {
    hours: Math.floor(totalMinutes / 60),
    minutes: totalMinutes % 60
  };
});

// --- API 方法 ---

async function fetchTickets(force = false) {
  await ticketStore.fetchTickets(force);
}

const changeSortType = (type: SortType) => {
  sortType.value = type;
};

const filterByPassenger = (passenger: string) => {
  selectedPassenger.value = passenger;
  // 如果需要重新请求后端筛选，这里调用 fetchTickets
  // 目前是前端筛选，所以不需要
};

const clearPassengerFilter = () => {
  selectedPassenger.value = '';
};

const filterByCity = (city: string) => {
  searchQuery.value = city;
  showCityModal.value = false;
};

// --- 事件处理 ---

const openTicketModal = (ticket: TicketFrontend | null = null) => {
  isModalOpen.value = true;
  if (ticket) {
    isEditing.value = true;
    // 需要把 Frontend 数据转回 FormData 格式供表单使用
    currentTicket.value = {
        id: ticket.id,
        from: ticket.from,
        to: ticket.to,
        train_code: ticket.trainCode,
        name: ticket.name,
        dateTime: ticket.dateTime,
        carriage: ticket.carriage,
        seatNumber: ticket.seatNumber,
        berthType: ticket.berthType,
        price: ticket.price,
        seatType: ticket.seatType,
        discountType: ticket.discountType,
        totalRunningTime: ticket.totalRunningTime,
        distance: ticket.distance,
        comments: ticket.comments
    };
  } else {
    isEditing.value = false;
    currentTicket.value = {}; 
  }
};

const closeModal = () => {
  isModalOpen.value = false;
  setTimeout(() => {
    currentTicket.value = {};
  }, 300);
};

const handleModalSave = async (formData: TicketFormData) => {
  saving.value = true;
  try {
    const backendData = formatFormToBackend(formData);
    
    if (isEditing.value && formData.id) {
      await ticketService.updateTicket(formData.id, backendData);
      // 更新本地数据
      // const updatedTicket = { ...backendData, id: formData.id };
      // ticketStore.updateLocalTicket(updatedTicket as any); // 类型可能需要适配
    } else {
      await ticketService.createTicket(backendData);
    }
    // 简单起见，保存后强制刷新，确保数据一致性
    await fetchTickets(true);
    closeModal();
    ElMessage.success(isEditing.value ? '更新成功' : '新增成功');
  } catch (err: any) {
    ElMessage.error(err.message || '保存失败');
    console.error('Save ticket error:', err);
  } finally {
    saving.value = false;
  }
};

const toggleSelect = (id: number) => {
  if (selectedTickets.value.includes(id)) {
    selectedTickets.value = selectedTickets.value.filter(item => item !== id);
  } else {
    selectedTickets.value.push(id);
  }
};

const confirmDelete = async (id: number) => {
  if (confirm('确定要删除这张车票吗？删除后不可恢复')) {
    try {
      await ticketService.deleteTicket(id);
      ticketStore.removeLocalTickets([id]);
      selectedTickets.value = selectedTickets.value.filter(tid => tid !== id);
      ElMessage.success('删除成功');
    } catch (err: any) {
      ElMessage.error(err.message || '删除失败');
    }
  }
};

const batchDelete = async () => {
  if (selectedTickets.value.length === 0) return;
  if (confirm(`确定删除选中的 ${selectedTickets.value.length} 张车票吗？删除后不可恢复`)) {
    try {
      await ticketService.batchDeleteTickets(selectedTickets.value);
      // 前端乐观更新
      // 注意：这里需要调用 store 的方法来更新数据，或者重新 fetch
      // 简单起见，我们更新 store 中的 tickets
      ticketStore.removeLocalTickets(selectedTickets.value);
      selectedTickets.value = [];
      ElMessage.success('批量删除成功');
    } catch (err: any) {
      ElMessage.error(err.message || '批量删除失败');
    }
  }
};
</script>

<style>
/* 过渡动画 */
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
</style>