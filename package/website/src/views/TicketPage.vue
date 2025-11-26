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
              placeholder="搜索车次 / 出发地 / 目的地"
              class="w-full pl-10 pr-4 py-2 bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-200 dark:focus:ring-primary-900 transition-all text-sm dark:text-white dark:placeholder-slate-400"
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

    <main class="max-w-[1400px] mx-auto px-4 py-6">
      <div class="flex flex-col xl:flex-row gap-6">
        
        <aside class="w-full xl:w-[320px] shrink-0 space-y-4">
          <div class="lg:hidden mb-4">
             <input v-model="searchQuery" type="text" placeholder="搜索车票..." class="w-full px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white" />
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-3 xl:grid-cols-1 gap-4">
            <div 
              @click="showCityModal = true"
              class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm hover:shadow-md transition-all cursor-pointer group relative overflow-hidden"
            >
              <div class="flex justify-between items-start z-10 relative">
                <div>
                  <div class="flex items-baseline gap-2">
                    <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ uniqueCities.length }}</span>
                    <span class="text-xs text-slate-500 dark:text-slate-400">座城市</span>
                  </div>
                  <p class="text-xs text-slate-400 mt-1">点击查看足迹地图</p>
                </div>
                <div class="p-2 bg-primary-50 dark:bg-slate-700 rounded-lg group-hover:bg-primary-500 group-hover:text-white transition-colors">
                  <MapPin class="w-5 h-5 text-primary-600 dark:text-primary-400 group-hover:text-white" />
                </div>
              </div>
            </div>

            <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm">
              <div class="flex justify-between items-start">
                <div>
                  <div class="flex items-baseline gap-2">
                    <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ totalDuration.hours }}<span class="text-sm font-normal text-slate-500 ml-0.5">h</span></span>
                    <span class="text-lg font-semibold text-slate-600 dark:text-slate-300">{{ totalDuration.minutes }}<span class="text-xs font-normal text-slate-500 ml-0.5">m</span></span>
                  </div>
                  <p class="text-xs text-slate-400 mt-1">累计旅程时长</p>
                </div>
                <div class="p-2 bg-primary-50 dark:bg-slate-700 rounded-lg">
                  <Clock class="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
              </div>
            </div>

            <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm">
              <div class="flex justify-between items-start">
                <div>
                  <div class="flex items-baseline gap-2">
                    <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ totalDistance.toLocaleString() }}</span>
                    <span class="text-xs text-slate-500 dark:text-slate-400">km</span>
                  </div>
                  <p class="text-xs text-slate-400 mt-1">绕赤道 {{ (totalDistance / 40075).toFixed(2) }} 圈</p>
                </div>
                <div class="p-2 bg-primary-50 dark:bg-slate-700 rounded-lg">
                  <Route class="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
              </div>
            </div>
          </div>
        </aside>

        <section class="flex-1 min-w-0">
          
          <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4 mb-6 flex flex-wrap gap-4 justify-between items-center shadow-sm transition-colors">
            
            <div class="flex items-center gap-3 w-full sm:w-auto">
              <div class="relative w-full sm:w-40">
                <select v-model="filterType" class="w-full appearance-none bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-sm rounded-md px-3 py-2 pr-8 focus:border-primary-500 dark:text-white outline-none cursor-pointer">
                  <option value="all">全部车票</option>
                  <option value="highspeed">高铁/动车</option>
                  <option value="normal">普速列车</option>
                </select>
                <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>

              <div class="hidden sm:flex bg-slate-100 dark:bg-slate-700 rounded-md p-1">
                <button 
                  @click="sortType = 'date'"
                  :class="['px-3 py-1 text-xs font-medium rounded transition-all', sortType === 'date' ? 'bg-white dark:bg-slate-600 text-primary-600 dark:text-primary-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200']"
                >
                  日期
                </button>
                <button 
                  @click="sortType = 'distance'"
                  :class="['px-3 py-1 text-xs font-medium rounded transition-all', sortType === 'distance' ? 'bg-white dark:bg-slate-600 text-primary-600 dark:text-primary-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200']"
                >
                  里程
                </button>
              </div>
            </div>

            <button 
              :disabled="selectedTickets.length === 0"
              @click="batchDelete"
              :class="['flex items-center gap-2 text-sm px-4 py-2 rounded-md transition-colors', selectedTickets.length > 0 ? 'text-red-600 bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50' : 'text-slate-300 dark:text-slate-600 bg-slate-50 dark:bg-slate-700 cursor-not-allowed']"
            >
              <Trash2 class="w-4 h-4" />
              <span>删除选中 ({{ selectedTickets.length }})</span>
            </button>
          </div>

          <div v-if="filteredTickets.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div 
              v-for="ticket in filteredTickets" 
              :key="ticket.id"
              class="group bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm hover:shadow-md hover:border-primary-300 dark:hover:border-primary-700 transition-all duration-300 relative overflow-hidden"
            >
              <div 
                class="h-1.5 w-full opacity-80"
                :style="{ background: `linear-gradient(to right, ${currentTheme.secondary}, ${currentTheme.primary})` }"
              ></div>

              <div class="p-5">
                <div class="flex justify-between items-start mb-4">
                  <div class="flex items-center gap-3">
                    <div 
                      @click.stop="toggleSelect(ticket.id)"
                      :class="['w-5 h-5 rounded-full border cursor-pointer flex items-center justify-center transition-colors', selectedTickets.includes(ticket.id) ? 'bg-primary-500 border-primary-500' : 'border-slate-300 dark:border-slate-600 hover:border-primary-500']"
                    >
                       <Check v-if="selectedTickets.includes(ticket.id)" class="w-3 h-3 text-white" />
                    </div>
                    <div>
                       <div class="flex items-center gap-2 text-lg font-bold text-slate-800 dark:text-slate-100">
                         <span>{{ ticket.from }}</span>
                         <MoveRight class="w-4 h-4 text-primary-500" />
                         <span>{{ ticket.to }}</span>
                       </div>
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-xl font-bold text-primary-600 dark:text-primary-400 font-mono">{{ ticket.trainNumber }}</div>
                    <div class="text-xs text-slate-400">{{ formatDate(ticket.date) }}</div>
                  </div>
                </div>

                <div class="border-b border-dashed border-slate-200 dark:border-slate-600 my-3 relative">
                  <div class="absolute -left-7 -top-1.5 w-3 h-3 bg-slate-50 dark:bg-slate-900 rounded-full"></div>
                  <div class="absolute -right-7 -top-1.5 w-3 h-3 bg-slate-50 dark:bg-slate-900 rounded-full"></div>
                </div>

                <div class="flex justify-between items-end">
                  <div class="space-y-1">
                    <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                      <Clock class="w-3.5 h-3.5" />
                      <span>{{ ticket.duration }}</span>
                      <span class="w-1 h-1 bg-slate-300 dark:bg-slate-600 rounded-full mx-1"></span>
                      <Route class="w-3.5 h-3.5" />
                      <span>{{ ticket.distance }}km</span>
                    </div>
                    <div class="text-sm font-medium text-slate-600 dark:text-slate-300">
                      {{ ticket.seatType }} · {{ ticket.seatNumber }}
                    </div>
                  </div>

                  <div class="flex gap-2 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity translate-y-0 md:translate-y-2 group-hover:translate-y-0">
                    <button @click.stop="openTicketModal(ticket)" class="p-2 text-primary-600 bg-primary-50 dark:bg-slate-700 dark:text-primary-400 rounded-md hover:bg-primary-500 hover:text-white dark:hover:bg-primary-600 dark:hover:text-white transition-colors">
                      <Pencil class="w-4 h-4" />
                    </button>
                    <button @click.stop="confirmDelete(ticket.id)" class="p-2 text-red-500 bg-red-50 dark:bg-red-900/20 rounded-md hover:bg-red-500 hover:text-white transition-colors">
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
              
              <div v-if="ticket.remarks" class="bg-slate-50 dark:bg-slate-700/30 px-5 py-2 text-xs text-slate-500 dark:text-slate-400 border-t border-slate-200 dark:border-slate-700">
                <span class="font-medium text-slate-700 dark:text-slate-300">备注：</span>{{ ticket.remarks }}
              </div>
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

    <Transition name="fade">
      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" @click="closeModal"></div>
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-2xl relative z-10 overflow-hidden flex flex-col max-h-[90vh]">
          
          <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-800">
            <h2 class="text-lg font-bold text-slate-800 dark:text-white">{{ isEditing ? '编辑车票' : '新增车票' }}</h2>
            <button @click="closeModal" class="text-slate-400 hover:text-red-500 transition-colors">
              <X class="w-6 h-6" />
            </button>
          </div>

          <div class="p-6 overflow-y-auto dark:text-slate-200">
            <form @submit.prevent="saveTicket" class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">出发地</label>
                <input v-model="form.from" type="text" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-colors" placeholder="如：北京南" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">目的地</label>
                <input v-model="form.to" type="text" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-colors" placeholder="如：上海虹桥" />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">车次</label>
                <input v-model="form.trainNumber" type="text" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none font-mono" placeholder="G101" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">出发日期</label>
                <input v-model="form.date" type="date" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">座位类型</label>
                <select v-model="form.seatType" class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none">
                  <option>二等座</option>
                  <option>一等座</option>
                  <option>商务座</option>
                  <option>硬卧</option>
                  <option>软卧</option>
                  <option>硬座</option>
                </select>
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">座位号</label>
                <input v-model="form.seatNumber" type="text" class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" placeholder="03车 12A" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">运行时间</label>
                <input v-model="form.duration" type="text" class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" placeholder="如：4h 30min" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">里程 (km)</label>
                <input v-model.number="form.distance" type="number" class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" placeholder="1318" />
              </div>
              <div class="md:col-span-2 space-y-1">
                 <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">备注</label>
                 <textarea v-model="form.remarks" rows="2" class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none resize-none" placeholder="旅行的意义..."></textarea>
              </div>
            </form>
          </div>

          <div class="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex justify-end gap-3 bg-slate-50 dark:bg-slate-800">
            <button @click="closeModal" class="px-5 py-2 text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">取消</button>
            <button @click="saveTicket" class="px-5 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 shadow-md shadow-primary-200 dark:shadow-none transition-transform active:scale-95">保存</button>
          </div>
        </div>
      </div>
    </Transition>

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

<script setup>
import { ref, computed, onMounted } from 'vue';
import { 
  TrainFront, Search, Plus, MapPin, Clock, Route,
  ChevronDown, Trash2, MoveRight, Pencil, X, Check,
  Palette, Sun, Moon
} from 'lucide-vue-next';

import { injectTheme } from '@/composables/useTheme';

// 2. 注入全局状态
const { isDarkMode, currentTheme } = injectTheme();

// 3. 提取所需的响应式值
const isDark = isDarkMode;
const mainColor = computed(() => currentTheme.value.primary);

// --- 业务数据 (与之前相同) ---
const tickets = ref([
  { id: 1, from: '北京南', to: '上海虹桥', trainNumber: 'G1', date: '2024-05-18', duration: '4h 28min', distance: 1318, seatType: '二等座', seatNumber: '03车 12A', remarks: '毕业旅行' },
  { id: 2, from: '成都东', to: '重庆北', trainNumber: 'G8601', date: '2024-06-01', duration: '1h 12min', distance: 308, seatType: '二等座', seatNumber: '05车 02F', remarks: '周末火锅局' },
  { id: 3, from: '广州南', to: '深圳北', trainNumber: 'G6021', date: '2024-06-15', duration: '0h 29min', distance: 102, seatType: '一等座', seatNumber: '01车 05A', remarks: '' },
]);

const searchQuery = ref('');
const filterType = ref('all');
const sortType = ref('date');
const selectedTickets = ref([]);
const isModalOpen = ref(false);
const isEditing = ref(false);
const showCityModal = ref(false);
const form = ref({
  id: null, from: '', to: '', trainNumber: '', date: '', 
  duration: '', distance: null, seatType: '二等座', seatNumber: '', remarks: ''
});

// --- Computed ---
const uniqueCities = computed(() => {
  const cities = new Set();
  tickets.value.forEach(t => { cities.add(t.from); cities.add(t.to); });
  return Array.from(cities).sort();
});

const totalDistance = computed(() => tickets.value.reduce((sum, t) => sum + (Number(t.distance) || 0), 0));

const totalDuration = computed(() => {
  let totalMinutes = 0;
  tickets.value.forEach(t => {
    const h = parseInt(t.duration.match(/(\d+)h/)?.[1] || 0);
    const m = parseInt(t.duration.match(/(\d+)min/)?.[1] || 0);
    totalMinutes += h * 60 + m;
  });
  return { hours: Math.floor(totalMinutes / 60), minutes: totalMinutes % 60 };
});

const filteredTickets = computed(() => {
  let res = tickets.value;
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    res = res.filter(t => t.trainNumber.toLowerCase().includes(q) || t.from.includes(q) || t.to.includes(q));
  }
  if (filterType.value !== 'all') {
    res = res.filter(t => {
      const firstChar = t.trainNumber.charAt(0).toUpperCase();
      return filterType.value === 'highspeed' ? ['G', 'D', 'C'].includes(firstChar) : !['G', 'D', 'C'].includes(firstChar);
    });
  }
  return [...res].sort((a, b) => {
    if (sortType.value === 'date') return new Date(b.date) - new Date(a.date);
    if (sortType.value === 'distance') return b.distance - a.distance;
    return 0;
  });
});

// --- Methods ---
const formatDate = (str) => str;
const openTicketModal = (ticket = null) => {
  isModalOpen.value = true;
  if (ticket) {
    isEditing.value = true;
    form.value = { ...ticket };
  } else {
    isEditing.value = false;
    form.value = { id: Date.now(), from: '', to: '', trainNumber: '', date: new Date().toISOString().split('T')[0], duration: '', distance: null, seatType: '二等座', seatNumber: '', remarks: '' };
  }
};
const closeModal = () => isModalOpen.value = false;
const saveTicket = () => {
  if (isEditing.value) {
    const index = tickets.value.findIndex(t => t.id === form.value.id);
    if (index !== -1) tickets.value[index] = { ...form.value };
  } else {
    tickets.value.unshift({ ...form.value, id: Date.now() });
  }
  closeModal();
};
const toggleSelect = (id) => {
  if (selectedTickets.value.includes(id)) selectedTickets.value = selectedTickets.value.filter(item => item !== id);
  else selectedTickets.value.push(id);
};
const confirmDelete = (id) => {
  if (confirm('确定要删除这张车票吗？')) {
    tickets.value = tickets.value.filter(t => t.id !== id);
    selectedTickets.value = selectedTickets.value.filter(tid => tid !== id);
  }
};
const batchDelete = () => {
  if (confirm(`确定删除选中的 ${selectedTickets.value.length} 张车票吗？`)) {
    tickets.value = tickets.value.filter(t => !selectedTickets.value.includes(t.id));
    selectedTickets.value = [];
  }
};
const filterByCity = (city) => {
  searchQuery.value = city;
  showCityModal.value = false;
};
</script>

<style>

</style>