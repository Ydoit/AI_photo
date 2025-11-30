<template>
  <div 
    :class="[isDarkMode ? 'dark' : '']"
    class="min-h-screen font-sans transition-colors duration-300 bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-200"
  >
    <!-- 导航栏 -->
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
              @input="debouncedFetchTickets"
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
             <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="搜索车票 / 乘车人..." 
              class="w-full px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white"
              @input="debouncedFetchTickets"
            />
          </div>

          <!-- 统计卡片 -->
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

          <!-- 乘车人筛选卡片 -->
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
          <!-- 筛选栏 -->
          <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4 mb-6 flex flex-wrap gap-4 justify-between items-center shadow-sm transition-colors">
            
            <div class="flex items-center gap-3 w-full sm:w-auto">
              <div class="relative w-full sm:w-40">
                <select 
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
                  @click="sortType = 'date'; fetchTickets()"
                  :class="['px-3 py-1 text-xs font-medium rounded transition-all', sortType === 'date' ? 'bg-white dark:bg-slate-600 text-primary-600 dark:text-primary-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200']"
                >
                  日期
                </button>
                <button 
                  @click="sortType = 'distance'; fetchTickets()"
                  :class="['px-3 py-1 text-xs font-medium rounded transition-all', sortType === 'distance' ? 'bg-white dark:bg-slate-600 text-primary-600 dark:text-primary-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200']"
                >
                  里程
                </button>
                <button 
                  @click="sortType = 'duration'; fetchTickets()"
                  :class="['px-3 py-1 text-xs font-medium rounded transition-all', sortType === 'duration' ? 'bg-white dark:bg-slate-600 text-primary-600 dark:text-primary-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200']"
                >
                  时长
                </button>
                <button 
                  @click="sortType = 'price'; fetchTickets()"
                  :class="['px-3 py-1 text-xs font-medium rounded transition-all', sortType === 'price' ? 'bg-white dark:bg-slate-600 text-primary-600 dark:text-primary-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200']"
                >
                  票价
                </button>
              </div>
            </div>

            <button 
              :disabled="selectedTickets.length === 0 || loading"
              @click="batchDelete"
              :class="['flex items-center gap-2 text-sm px-4 py-2 rounded-md transition-colors', selectedTickets.length > 0 ? 'text-red-600 bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50' : 'text-slate-300 dark:text-slate-600 bg-slate-50 dark:bg-slate-700 cursor-not-allowed']"
            >
              <Trash2 class="w-4 h-4" />
              <span>删除选中 ({{ selectedTickets.length }})</span>
            </button>
          </div>

          <!-- 加载状态 -->
          <div v-if="loading" class="flex justify-center items-center py-20">
            <div class="w-10 h-10 border-4 border-slate-200 dark:border-slate-700 border-t-primary-500 rounded-full animate-spin"></div>
          </div>

          <!-- 错误提示 -->
          <div v-else-if="error" class="flex flex-col items-center justify-center py-20 text-center text-red-500">
            <X class="w-12 h-12 mb-4" />
            <h3 class="text-xl font-medium mb-2">数据加载失败</h3>
            <p class="mb-4">{{ error }}</p>
            <button @click="fetchTickets()" class="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors">重试</button>
          </div>

          <!-- 车票列表 -->
          <div v-else-if="filteredTickets.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                       <!-- 新增乘车人显示 -->
                       <div class="text-xs text-slate-500 dark:text-slate-400 mt-1">
                         乘车人：{{ ticket.passengerName }}
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
                      <span class="w-1 h-1 bg-slate-300 dark:bg-slate-600 rounded-full mx-1"></span>
                      <span>{{ ticket.price }}元</span>
                    </div>
                    <div class="text-sm font-medium text-slate-600 dark:text-slate-300">
                      {{ ticket.seatType }} · {{ ticket.carriage }}车 {{ ticket.seatNumber }}
                      <span v-if="ticket.berthType !== '无'" class="text-xs text-slate-400 ml-2">{{ ticket.berthType }}铺</span>
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
              
              <div v-if="ticket.comments" class="bg-slate-50 dark:bg-slate-700/30 px-5 py-2 text-xs text-slate-500 dark:text-slate-400 border-t border-slate-200 dark:border-slate-700">
                <span class="font-medium text-slate-700 dark:text-slate-300">备注：</span>{{ ticket.comments }}
              </div>
            </div>
          </div>

          <!-- 空状态 -->
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

    <!-- 新增/编辑模态框 -->
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
              <!-- 基础信息 -->
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">出发地 <span class="text-red-500">*</span></label>
                <input v-model="form.from" type="text" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-colors" placeholder="如：北京南" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">目的地 <span class="text-red-500">*</span></label>
                <input v-model="form.to" type="text" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-colors" placeholder="如：上海虹桥" />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">车次 <span class="text-red-500">*</span></label>
                <input v-model="form.trainNumber" type="text" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none font-mono" placeholder="G101 / Z123" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">乘车人 <span class="text-red-500">*</span></label>
                <input v-model="form.passengerName" type="text" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-colors" placeholder="如：张三" />
              </div>

              <div class="space-y-1 md:col-span-2">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">出发日期时间 <span class="text-red-500">*</span></label>
                <input 
                  v-model="form.dateTime" 
                  type="datetime-local" 
                  required 
                  class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
                />
              </div>

              <!-- 座位信息 -->
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">座位类型 <span class="text-red-500">*</span></label>
                <select v-model="form.seatType" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none">
                  <option>二等座</option>
                  <option>一等座</option>
                  <option>商务座</option>
                  <option>硬卧</option>
                  <option>软卧</option>
                  <option>硬座</option>
                  <option>软座</option>
                </select>
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">铺位类型</label>
                <select v-model="form.berthType" class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none">
                  <option>无</option>
                  <option>上铺</option>
                  <option>中铺</option>
                  <option>下铺</option>
                </select>
              </div>

              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">车厢号 <span class="text-red-500">*</span></label>
                <input v-model="form.carriage" type="text" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" placeholder="如：03 / 8A" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">座位号 <span class="text-red-500">*</span></label>
                <input v-model="form.seatNumber" type="text" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" placeholder="如：12A / 05下" />
              </div>

              <!-- 价格和里程 -->
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">票价（元）<span class="text-red-500">*</span></label>
                <input v-model.number="form.price" type="number" step="0.01" min="0" required class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" placeholder="198.5" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">里程 (km)</label>
                <input v-model.number="form.distance" type="number" min="0" class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" placeholder="1318" />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">运行时间（分钟）</label>
                <input v-model.number="form.totalRunningTime" type="number" min="0" class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" placeholder="268" />
              </div>
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">优惠类型</label>
                <select v-model="form.discountType" class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none">
                  <option>全价票</option>
                  <option>学生票</option>
                  <option>儿童票</option>
                  <option>优惠票</option>
                </select>
              </div>

              <!-- 备注 -->
              <div class="md:col-span-2 space-y-1">
                 <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">备注</label>
                 <textarea v-model="form.comments" rows="2" class="w-full p-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none resize-none" placeholder="旅行的意义..."></textarea>
              </div>
            </form>
          </div>

          <div class="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex justify-end gap-3 bg-slate-50 dark:bg-slate-800">
            <button @click="closeModal" class="px-5 py-2 text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">取消</button>
            <button 
              @click="saveTicket" 
              :disabled="saving"
              :class="['px-5 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 shadow-md shadow-primary-200 dark:shadow-none transition-transform active:scale-95', saving ? 'opacity-70 cursor-not-allowed' : '']"
            >
              <span v-if="saving" class="inline-block w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              保存
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 城市筛选模态框 -->
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
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { 
  TrainFront, Search, Plus, MapPin, Clock, Route,
  ChevronDown, Trash2, MoveRight, Pencil, X, Check, User
} from 'lucide-vue-next';
import axios from 'axios';

// 注入主题
import { injectTheme } from '@/composables/useTheme';
const { isDarkMode, currentTheme } = injectTheme();
const isDark = isDarkMode;
const mainColor = computed(() => currentTheme.value.primary);

// --- 环境配置 ---
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'; // 后端接口地址
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- 状态管理 ---
const tickets = ref([]); // 后端获取的原始数据
const searchQuery = ref('');
const filterType = ref('all');
const sortType = ref('date'); // 新增：支持 date/distance/duration/price
const selectedTickets = ref([]);
const isModalOpen = ref(false);
const isEditing = ref(false);
const showCityModal = ref(false);
const loading = ref(false);
const error = ref('');
const saving = ref(false);
const selectedPassenger = ref(''); // 选中的乘车人筛选条件

// --- 表单模型（新增乘车人字段、精确时间字段）---
const form = ref({
  id: null,
  from: '', // departure_station
  to: '', // arrival_station
  trainNumber: '', // train_code
  passengerName: '', // 乘车人姓名（对应后端name字段）
  dateTime: new Date().toISOString().slice(0, 16), // 精确到分钟的日期时间（YYYY-MM-DDTHH:mm）
  carriage: '', // 车厢号
  seatNumber: '', // 座位号
  berthType: '无', // 铺位类型
  price: 0, // 票价
  seatType: '二等座', // 座位类型
  discountType: '全价票', // 优惠类型
  totalRunningTime: 0, // 总运行时间（分钟）
  distance: 0, // 总里程（公里）
  comments: '' // 备注
});

// --- 防抖函数（优化搜索体验）---
const debounce = (fn, delay = 500) => {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
};
const debouncedFetchTickets = debounce(fetchTickets);

// --- 生命周期钩子 ---
onMounted(() => {
  fetchTickets(); // 初始化加载车票列表
});

onUnmounted(() => {
  // 清理防抖定时器
  debouncedFetchTickets.cancel?.();
});

// --- 数据转换与计算属性 ---
// 后端数据 → 前端展示数据映射
const formatTicket = (ticket) => ({
  id: ticket.id,
  from: ticket.departure_station,
  to: ticket.arrival_station,
  trainNumber: ticket.train_code,
  passengerName: ticket.name || '', // 乘车人姓名
  date: ticket.date_time.split(' ')[0], // 提取日期部分（YYYY-MM-DD）- 展示用
  dateTime: ticket.date_time, // 完整日期时间（后端格式）
  time: ticket.date_time.split(' ')[1], // 提取时间部分（HH:MM:SS）
  carriage: ticket.carriage,
  seatNumber: ticket.seat_num,
  berthType: ticket.berth_type || '无',
  price: ticket.price,
  seatType: ticket.seat_type,
  discountType: ticket.discount_type || '全价票',
  totalRunningTime: ticket.total_running_time || 0,
  distance: ticket.total_mileage || 0,
  comments: ticket.comments || '',
  // 计算运行时间文本（分钟 → h min 格式）
  duration: computed(() => {
    const minutes = ticket.total_running_time || 0;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}min` : `${mins}min`;
  }).value
});

// 前端数据 → 后端请求数据映射
const formatFormToBackend = (formData) => ({
  train_code: formData.trainNumber,
  departure_station: formData.from,
  arrival_station: formData.to,
  date_time: formData.dateTime.replace('T', ' '), // 转换为后端需要的格式（YYYY-MM-DD HH:mm）
  carriage: formData.carriage,
  seat_num: formData.seatNumber,
  berth_type: formData.berthType,
  price: formData.price,
  seat_type: formData.seatType,
  name: formData.passengerName, // 乘车人姓名（必填）
  discount_type: formData.discountType,
  total_running_time: formData.totalRunningTime || 0,
  total_mileage: formData.distance || 0,
  stop_stations: '', // 暂未实现途经站点
  comments: formData.comments
});

// 计算属性：筛选后的车票列表（新增乘车人筛选、多维度排序）
const filteredTickets = computed(() => {
  let res = tickets.value.map(formatTicket);
  
  // 1. 搜索筛选（支持乘车人筛选）
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    res = res.filter(t => 
      t.trainNumber.toLowerCase().includes(q) || 
      t.from.toLowerCase().includes(q) || 
      t.to.toLowerCase().includes(q) ||
      t.passengerName.toLowerCase().includes(q) // 新增：乘车人搜索
    );
  }

  // 2. 列车类型筛选
  if (filterType.value !== 'all') {
    res = res.filter(t => {
      const firstChar = t.trainNumber.charAt(0).toUpperCase();
      return filterType.value === 'highspeed' 
        ? ['G', 'D', 'C'].includes(firstChar) 
        : !['G', 'D', 'C'].includes(firstChar);
    });
  }

  // 3. 乘车人筛选
  if (selectedPassenger.value) {
    res = res.filter(t => t.passengerName === selectedPassenger.value);
  }

  // 4. 多维度排序（新增时长、票价排序）
  return [...res].sort((a, b) => {
    switch (sortType.value) {
      case 'date':
        return new Date(b.dateTime) - new Date(a.dateTime); // 按日期时间倒序
      case 'distance':
        return b.distance - a.distance; // 按里程倒序
      case 'duration':
        return b.totalRunningTime - a.totalRunningTime; // 按时长倒序
      case 'price':
        return b.price - a.price; // 按票价倒序
      default:
        return 0;
    }
  });
});

// 计算属性：唯一城市列表
const uniqueCities = computed(() => {
  const cities = new Set();
  filteredTickets.value.forEach(t => {
    cities.add(t.from);
    cities.add(t.to);
  });
  return Array.from(cities).sort();
});

// 计算属性：唯一乘车人列表（新增）
const uniquePassengers = computed(() => {
  const passengers = new Set();
  tickets.value.forEach(t => {
    if (t.name) passengers.add(t.name);
  });
  return Array.from(passengers).sort();
});

// 计算属性：累计里程
const totalDistance = computed(() => 
  tickets.value.reduce((sum, t) => sum + (t.total_mileage || 0), 0)
);

// 计算属性：累计运行时间
const totalDuration = computed(() => {
  const totalMinutes = tickets.value.reduce((sum, t) => sum + (t.total_running_time || 0), 0);
  return {
    hours: Math.floor(totalMinutes / 60),
    minutes: totalMinutes % 60
  };
});

// --- API请求函数（更新查询参数，支持乘车人筛选）---
// 获取车票列表
async function fetchTickets() {
  loading.value = true;
  error.value = '';
  try {
    // 构建查询参数（新增乘车人筛选参数）
    const params = {
      skip: 0,
      limit: 100,
      train_code: searchQuery.value || undefined,
      departure_station: searchQuery.value || undefined,
      arrival_station: searchQuery.value || undefined,
      name: selectedPassenger.value || undefined, // 新增：乘车人筛选参数
      // 可以扩展：支持按乘车人精确筛选
    };

    const response = await axiosInstance.get('/api/train-ticket', { params });
    tickets.value = response.data.items || [];
  } catch (err) {
    error.value = err.response?.data?.detail || '获取车票失败，请重试';
    console.error('Fetch tickets error:', err);
  } finally {
    loading.value = false;
  }
}

// 新增车票
async function createTicket(formData) {
  try {
    const backendData = formatFormToBackend(formData);
    const response = await axiosInstance.post('/api/train-ticket', backendData);
    return response.data;
  } catch (err) {
    throw new Error(err.response?.data?.detail || '新增车票失败');
  }
}

// 更新车票
async function updateTicket(id, formData) {
  try {
    const backendData = formatFormToBackend(formData);
    const response = await axiosInstance.put(`/api/train-ticket/${id}`, backendData);
    return response.data;
  } catch (err) {
    throw new Error(err.response?.data?.detail || '更新车票失败');
  }
}

// 删除单张车票
async function deleteTicket(id) {
  try {
    await axiosInstance.delete(`/api/train-ticket/${id}`);
    return true;
  } catch (err) {
    throw new Error(err.response?.data?.detail || '删除车票失败');
  }
}

// 批量删除车票
async function batchDeleteTickets(ids) {
  try {
    const promises = ids.map(id => deleteTicket(id));
    await Promise.all(promises);
    return true;
  } catch (err) {
    throw new Error('批量删除失败，请重试');
  }
}

// --- 页面方法（新增乘车人筛选相关方法）---
// 日期格式化（只显示日期部分）
const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};

// 打开模态框
const openTicketModal = (ticket = null) => {
  isModalOpen.value = true;
  if (ticket) {
    isEditing.value = true;
    // 反向填充表单（包含乘车人和精确时间）
    form.value = {
      id: ticket.id,
      from: ticket.from,
      to: ticket.to,
      trainNumber: ticket.trainNumber,
      passengerName: ticket.passengerName,
      dateTime: ticket.dateTime.replace(' ', 'T').slice(0, 16), // 转换为datetime-local格式
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
    // 重置表单
    form.value = {
      id: null,
      from: '',
      to: '',
      trainNumber: '',
      passengerName: '',
      dateTime: new Date().toISOString().slice(0, 16),
      carriage: '',
      seatNumber: '',
      berthType: '无',
      price: 0,
      seatType: '二等座',
      discountType: '全价票',
      totalRunningTime: 0,
      distance: 0,
      comments: ''
    };
  }
};

// 关闭模态框
const closeModal = () => {
  isModalOpen.value = false;
  setTimeout(() => {
    form.value = {
      id: null,
      from: '',
      to: '',
      trainNumber: '',
      passengerName: '',
      dateTime: new Date().toISOString().slice(0, 16),
      carriage: '',
      seatNumber: '',
      berthType: '无',
      price: 0,
      seatType: '二等座',
      discountType: '全价票',
      totalRunningTime: 0,
      distance: 0,
      comments: ''
    };
  }, 300);
};

// 保存车票
const saveTicket = async () => {
  saving.value = true;
  try {
    if (!form.value.passengerName) {
      alert('乘车人姓名不能为空');
      return;
    }
    
    if (isEditing.value) {
      await updateTicket(form.value.id, form.value);
    } else {
      await createTicket(form.value);
    }
    await fetchTickets();
    closeModal();
  } catch (err) {
    alert(err.message);
    console.error('Save ticket error:', err);
  } finally {
    saving.value = false;
  }
};

// 切换选中状态
const toggleSelect = (id) => {
  if (selectedTickets.value.includes(id)) {
    selectedTickets.value = selectedTickets.value.filter(item => item !== id);
  } else {
    selectedTickets.value.push(id);
  }
};

// 确认删除单张车票
const confirmDelete = async (id) => {
  if (confirm('确定要删除这张车票吗？删除后不可恢复')) {
    try {
      await deleteTicket(id);
      tickets.value = tickets.value.filter(t => t.id !== id);
      selectedTickets.value = selectedTickets.value.filter(tid => tid !== id);
    } catch (err) {
      alert(err.message);
    }
  }
};

// 批量删除车票
const batchDelete = async () => {
  if (selectedTickets.value.length === 0) return;
  if (confirm(`确定删除选中的 ${selectedTickets.value.length} 张车票吗？删除后不可恢复`)) {
    try {
      await batchDeleteTickets(selectedTickets.value);
      tickets.value = tickets.value.filter(t => !selectedTickets.value.includes(t.id));
      selectedTickets.value = [];
    } catch (err) {
      alert(err.message);
    }
  }
};

// 按城市筛选
const filterByCity = (city) => {
  searchQuery.value = city;
  showCityModal.value = false;
  fetchTickets();
};

// 按乘车人筛选（新增）
const filterByPassenger = (passenger) => {
  selectedPassenger.value = passenger;
  fetchTickets();
};

// 清除乘车人筛选（新增）
const clearPassengerFilter = () => {
  selectedPassenger.value = '';
  fetchTickets();
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